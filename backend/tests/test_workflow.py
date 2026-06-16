"""End-to-end workflow tests using the in-memory fallback path (no network, no keys)."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_leadhunter.db")
os.environ.setdefault("SCRAPER_MODE", "fallback")

import pytest

from app.database import Base, SessionLocal, engine, init_db
from app.models import Lead, LeadStatus, ScanJob
from app.services.scoring import priority_for, score_lead
from app.services.workflow import run_workflow


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


def _run(url: str, service: str = "website development") -> ScanJob:
    db = SessionLocal()
    try:
        job = ScanJob(input_url=url, service=service, status="queued")
        db.add(job)
        db.commit()
        db.refresh(job)
        return run_workflow(db, job)
    finally:
        db.close()


def test_business_without_website_becomes_qualified_lead():
    job = _run("https://www.instagram.com/serengetidreamsafaris/")
    assert job.verdict == LeadStatus.QUALIFIED_LEAD.value
    db = SessionLocal()
    lead = db.get(Lead, job.lead_id)
    assert lead.business_name == "Serengeti Dreams Safaris"
    assert lead.website_url is None
    assert lead.ai_summary  # enrichment ran
    assert lead.score and 1 <= lead.score <= 100
    assert lead.priority
    assert len(lead.competitors) > 0
    assert len(lead.outreach_messages) == 5  # all channels
    db.close()


def test_business_with_website_is_not_a_lead():
    job = _run("https://www.instagram.com/kilizotech/")
    assert job.verdict == LeadStatus.WEBSITE_FOUND.value
    db = SessionLocal()
    lead = db.get(Lead, job.lead_id)
    assert lead.website_url is not None
    assert lead.status == LeadStatus.WEBSITE_FOUND.value
    db.close()


def test_facebook_step_runs_when_instagram_has_no_website():
    # Mama Ndogo has FB but no website anywhere -> qualified, FB step recorded.
    job = _run("https://www.instagram.com/mamandogokitchen/")
    stages = [s["stage"] for s in job.steps]
    assert "facebook" in stages
    assert job.verdict == LeadStatus.QUALIFIED_LEAD.value


def test_nonwebsite_service_qualifies_business_with_website():
    # Kilizo Tech HAS a website, so it's not a website lead — but for an "AI chatbot"
    # offering it should still qualify (website presence is irrelevant).
    job = _run("https://www.instagram.com/kilizotech/", service="AI chatbot")
    assert job.verdict == LeadStatus.QUALIFIED_LEAD.value
    db = SessionLocal()
    lead = db.get(Lead, job.lead_id)
    assert lead.target_service == "AI chatbot"
    # Service-aware opportunity reasons mention the service, not "website".
    reasons = " ".join(lead.opportunity_analysis["reasons"]).lower()
    assert "ai chatbot" in reasons
    db.close()


def test_website_service_still_filters_on_website():
    job = _run("https://www.instagram.com/kilizotech/", service="website development")
    assert job.verdict == LeadStatus.WEBSITE_FOUND.value


def test_competitors_match_niche_not_default():
    from app.services.competitor import find_competitors

    class FakeLead:
        industry = "Construction"
        category = "Construction"
        city = "Iringa"
        region = "Iringa"

    comps = find_competitors(FakeLead(), limit=5)
    blob = " ".join((c["name"] + " " + (c.get("key_services") or "")).lower() for c in comps)
    assert comps, "should return some competitors"
    # The old bug returned safari/tour operators for every niche.
    assert "safari" not in blob and "travel & tours" not in blob


def test_generic_competitors_for_unknown_niche():
    from app.services.competitor import find_competitors

    class FakeLead:
        industry = "Pottery Studio"
        category = "Pottery Studio"
        city = "Mtwara"
        region = "Mtwara"

    comps = find_competitors(FakeLead(), limit=5)
    blob = " ".join(c["name"].lower() for c in comps)
    assert "pottery" in blob  # niche-correct, not off-topic
    assert "safari" not in blob


def test_scoring_buckets():
    assert priority_for(85).value == "Hot Lead"
    assert priority_for(70).value == "Warm Lead"
    assert priority_for(45).value == "Medium Lead"
    assert priority_for(10).value == "Low Priority"


def test_score_breakdown_sums_to_score():
    class FakeLead:
        followers = 20000
        reviews_count = 200
        posts_count = 400
        rating = 5.0
        industry = "Real Estate"
        category = "Real Estate"
        email = "a@b.com"
        phone = "+255700000000"
        whatsapp = None
        instagram_url = "x"
        facebook_url = "y"
        google_business_url = "z"

    score, priority, breakdown = score_lead(FakeLead())
    assert score == 100
    assert priority == "Hot Lead"
    assert round(sum(breakdown.values())) == 100
