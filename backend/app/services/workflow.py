"""The 5-step lead-discovery workflow.

Step 1  Instagram analysis            -> website? stop : continue
Step 2  Facebook verification         -> website? stop : continue
Step 3  Google Business Profile       -> website? stop : continue
Step 4  Deep web search (top 20)      -> website? stop : continue
Step 5  Qualified lead -> enrich (AI summary, opportunity, strategy, competitors,
        proposal, score) + generate outreach drafts.

Runs synchronously inside a background-task worker thread (see api/scan.py), which keeps
Playwright's sync API and SQLAlchemy's sync sessions simple and safe.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Competitor, Lead, LeadStatus, OutreachMessage, ScanJob, ScanStage
from app.scrapers.base import ProfileData, username_from_instagram_url
from app.scrapers.facebook import scrape_facebook
from app.scrapers.google_business import scrape_google_business
from app.scrapers.google_search import find_official_website
from app.scrapers.instagram import scrape_instagram
from app.services import competitor as competitor_svc
from app.services import enrichment, outreach, proposal
from app.services.offering import is_website_service, normalize_service
from app.services.scoring import score_lead

log = logging.getLogger("leadhunter.workflow")


def _step(stage: str, found: bool, detail: str, data: dict | None = None) -> dict:
    return {"stage": stage, "found_website": found, "detail": detail, "data": data}


def run_workflow(db: Session, job: ScanJob) -> ScanJob:
    job.status = "running"
    db.commit()

    steps: list[dict] = []
    merged = ProfileData(source="merged")  # accumulates contact data across steps
    website_url: str | None = None
    final_stage: str | None = None

    # The offering determines qualification: website services qualify businesses with NO
    # website; any other service qualifies any business in the target niche.
    service = normalize_service(job.service)
    website_mode = is_website_service(service)

    try:
        business_name = job.input_name

        # ── Step 1: Instagram ────────────────────────────────────────
        if job.input_url:
            ig = scrape_instagram(job.input_url)
            _absorb(merged, ig)
            business_name = business_name or ig.business_name
            final_stage = ScanStage.INSTAGRAM.value
            if ig.website_url:
                website_url = ig.website_url
                steps.append(_step(final_stage, True, f"Website on Instagram: {website_url}", ig.as_dict()))
            else:
                steps.append(_step(final_stage, False, "No website link on Instagram", ig.as_dict()))

        # `keep_checking` is True while we still want to run website-detection steps. In
        # non-website mode we keep running them only to enrich data, never to disqualify.
        def keep_checking() -> bool:
            return (not website_url) if website_mode else (not website_url)

        # ── Step 2: Facebook ─────────────────────────────────────────
        if keep_checking() and merged.facebook_url:
            fb = scrape_facebook(merged.facebook_url)
            _absorb(merged, fb)
            business_name = business_name or fb.business_name
            final_stage = ScanStage.FACEBOOK.value
            if fb.website_url:
                website_url = fb.website_url
                steps.append(_step(final_stage, True, f"Website on Facebook: {website_url}", fb.as_dict()))
            else:
                steps.append(_step(final_stage, False, "No website on Facebook page", fb.as_dict()))

        # ── Step 3: Google Business Profile ──────────────────────────
        if keep_checking() and business_name:
            gbp = scrape_google_business(business_name)
            _absorb(merged, gbp)
            final_stage = ScanStage.GOOGLE_BUSINESS.value
            if gbp.website_url:
                website_url = gbp.website_url
                steps.append(_step(final_stage, True, f"Website on Google Business: {website_url}", gbp.as_dict()))
            else:
                steps.append(_step(final_stage, False, "No website on Google Business Profile", gbp.as_dict()))

        # ── Step 4: Deep web search (website mode only) ──────────────
        if website_mode and not website_url and business_name:
            final_stage = ScanStage.DEEP_SEARCH.value
            found = find_official_website(business_name, max_results=20)
            if found:
                website_url = found
                steps.append(_step(final_stage, True, f"Official website found via search: {found}"))
            else:
                steps.append(_step(final_stage, False, "No official website in top 20 results"))

        # Backfill niche/city from the discovery hints when scraping didn't surface them,
        # so the lead (and its competitor analysis) reflect the right niche.
        if not merged.category and job.hint_category:
            merged.category = job.hint_category
        if not merged.city and job.hint_city:
            merged.city = job.hint_city

        # ── Verdict ──────────────────────────────────────────────────
        # Only website services disqualify on an existing website. For other offerings the
        # business qualifies regardless (we still record any website we happened to find).
        if website_mode and website_url:
            lead = _persist_lead(db, job, merged, business_name, LeadStatus.WEBSITE_FOUND,
                                 website_url, service)
            job.verdict = LeadStatus.WEBSITE_FOUND.value
            steps.append(_step("verdict", True, "Website Found — not a lead for website services"))
        else:
            final_stage = ScanStage.LEAD_CREATED.value
            lead = _persist_lead(db, job, merged, business_name, LeadStatus.QUALIFIED_LEAD,
                                 website_url if not website_mode else None, service)
            _enrich_lead(db, lead, service)
            job.verdict = LeadStatus.QUALIFIED_LEAD.value
            msg = (
                "No website found — Qualified Lead created" if website_mode
                else f"Qualified Lead for '{service}' created"
            )
            steps.append(_step(final_stage, False, msg))

        job.lead_id = lead.id
        job.final_stage = final_stage
        job.steps = steps
        job.status = "done"
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job

    except Exception as exc:  # noqa: BLE001
        log.exception("workflow failed for job %s", job.id)
        job.status = "error"
        job.error = str(exc)
        job.steps = steps
        job.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(job)
        return job


def _absorb(merged: ProfileData, pd: ProfileData) -> None:
    """Fill empty fields of `merged` from a step result (first non-empty wins)."""
    for f in (
        "business_name", "username", "bio", "category", "phone", "whatsapp", "email",
        "location", "city", "region", "address", "followers", "posts_count",
        "reviews_count", "rating", "hours", "facebook_url", "instagram_url",
        "google_business_url",
    ):
        if getattr(merged, f) in (None, "") and getattr(pd, f) not in (None, ""):
            setattr(merged, f, getattr(pd, f))
    merged.external_links.extend(l for l in pd.external_links if l not in merged.external_links)
    if pd.raw:
        merged.raw[pd.source] = pd.raw


def _split_location(merged: ProfileData) -> tuple[str | None, str | None]:
    """Derive city/region from a 'City, Country' style location string."""
    city, region = merged.city, merged.region
    if not city and merged.location:
        first = merged.location.split(",")[0].strip()
        if first and first.lower() != "tanzania":
            city = first
    return city, region


def _persist_lead(
    db: Session,
    job: ScanJob,
    merged: ProfileData,
    business_name: str | None,
    status: LeadStatus,
    website_url: str | None,
    service: str,
) -> Lead:
    city, region = _split_location(merged)
    name = business_name or merged.business_name or (
        username_from_instagram_url(job.input_url or "") or "Unknown Business"
    )
    lead = Lead(
        business_name=name,
        username=merged.username,
        industry=merged.category,
        category=merged.category,
        description=merged.bio,
        instagram_url=merged.instagram_url or job.input_url,
        facebook_url=merged.facebook_url,
        google_business_url=merged.google_business_url,
        website_url=website_url,
        phone=merged.phone,
        whatsapp=merged.whatsapp,
        email=merged.email,
        address=merged.address,
        city=city,
        region=region,
        country=settings.default_country,
        followers=merged.followers,
        posts_count=merged.posts_count,
        reviews_count=merged.reviews_count,
        rating=merged.rating,
        status=status.value,
        target_service=service,
        raw_data=merged.raw,
        source_url=job.input_url,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def _enrich_lead(db: Session, lead: Lead, service: str = "website development") -> None:
    """Step 5 enrichment: AI summary, opportunity, strategy, competitors, proposal, score.

    All service-dependent content (opportunity, comparison, proposal, outreach) is tailored
    to the `service` being offered.
    """
    ai_flags: list[bool] = []

    summary, f1 = enrichment.business_summary(lead)
    lead.ai_summary = summary
    ai_flags.append(f1)

    opp, f2 = enrichment.opportunity_analysis(lead, service)
    lead.opportunity_analysis = opp
    ai_flags.append(f2)

    strat, f3 = enrichment.marketing_strategy(lead)
    lead.marketing_strategy = strat
    ai_flags.append(f3)

    # Competitors (AI-discovered, same niche) + service-aware comparison
    comps = competitor_svc.find_competitors(lead, limit=5)
    for c in comps:
        db.add(Competitor(
            lead_id=lead.id, name=c["name"],
            website_url=c.get("website_url"), key_services=c.get("key_services"),
        ))
    comp_text, f4 = competitor_svc.comparison_text(lead, comps, service)
    lead.competitor_comparison = comp_text
    ai_flags.append(f4)

    # Proposal (after summary so it can reference it)
    prop, f5 = proposal.build_proposal(lead, service)
    lead.proposal = prop
    ai_flags.append(f5)

    # Scoring
    score, priority, breakdown = score_lead(lead)
    lead.score = score
    lead.priority = priority
    lead.score_breakdown = breakdown

    # Outreach drafts (all channels), pitched around the offering
    for msg in outreach.generate_all(lead, service=service):
        db.add(OutreachMessage(
            lead_id=lead.id, channel=msg["channel"],
            subject=msg.get("subject"), body=msg["body"],
        ))

    lead.ai_generated = any(ai_flags)
    db.commit()
    db.refresh(lead)
