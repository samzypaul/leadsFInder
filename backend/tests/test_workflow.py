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


def _run(url: str) -> ScanJob:
    db = SessionLocal()
    try:
        job = ScanJob(input_url=url, status="queued")
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
