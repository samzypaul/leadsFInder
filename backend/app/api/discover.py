"""Targeted + natural-language business discovery endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import ScanJob, User
from app.schemas import (
    Candidate,
    DiscoverRequest,
    DiscoverResponse,
    DiscoverScanRequest,
    DiscoveryFilters,
)
from app.services import discovery
from app.services.workflow import run_workflow

router = APIRouter(prefix="/discover", tags=["discovery"])


def _resolve_filters(req: DiscoverRequest) -> tuple[DiscoveryFilters, bool]:
    """Merge an explicit filter object with anything parsed from the NL query."""
    ai_parsed = False
    filters = req.filters or DiscoveryFilters()
    if req.query:
        parsed, ai_parsed = discovery.parse_nl_query(req.query)
        if req.filters:
            # explicit filters take precedence over parsed ones (field-by-field)
            data = parsed.model_dump()
            data.update({k: v for k, v in req.filters.model_dump().items()
                         if v not in (None, [], False) or k == "only_without_website"})
            filters = DiscoveryFilters(**data)
        else:
            filters = parsed
    return filters, ai_parsed


@router.post("", response_model=DiscoverResponse)
def discover(
    req: DiscoverRequest,
    _: User = Depends(get_current_user),
):
    if not req.query and not req.filters:
        raise HTTPException(400, "Provide a natural-language query or filters")
    filters, ai_parsed = _resolve_filters(req)
    candidates = discovery.search_businesses(filters)
    return DiscoverResponse(
        interpreted_filters=filters,
        query=req.query,
        ai_parsed=ai_parsed,
        count=len(candidates),
        candidates=candidates,
    )


@router.post("/scan")
def discover_and_scan(
    req: DiscoverScanRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Discover candidates (or use the supplied list) and run the workflow over them."""
    candidates: list[Candidate]
    if req.candidates:
        candidates = req.candidates
    else:
        filters, _ai = _resolve_filters(req)
        candidates = discovery.search_businesses(filters)

    results = []
    for cand in candidates[: req.max_scans]:
        job = ScanJob(
            input_url=cand.instagram_url,
            input_name=cand.business_name,
            status="queued",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        run_workflow(db, job)
        db.refresh(job)
        results.append({
            "business_name": cand.business_name,
            "verdict": job.verdict,
            "lead_id": job.lead_id,
            "final_stage": job.final_stage,
        })

    qualified = sum(1 for r in results if r["verdict"] == "Qualified Lead")
    return {
        "scanned": len(results),
        "qualified_leads": qualified,
        "websites_found": len(results) - qualified,
        "results": results,
    }
