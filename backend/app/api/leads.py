"""Lead CRUD + enrichment endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.schemas import LeadOut, LeadSummary, LeadUpdate
from app.services.workflow import _enrich_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=list[LeadSummary])
def list_leads(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    outreach_status: str | None = Query(None),
    q: str | None = Query(None, description="search business name"),
    sort: str = Query("score", description="score | created_at | business_name"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if priority:
        stmt = stmt.where(Lead.priority == priority)
    if outreach_status:
        stmt = stmt.where(Lead.outreach_status == outreach_status)
    if q:
        stmt = stmt.where(Lead.business_name.ilike(f"%{q}%"))

    order = {
        "score": Lead.score.desc(),
        "created_at": Lead.created_at.desc(),
        "business_name": Lead.business_name.asc(),
    }.get(sort, Lead.score.desc())
    stmt = stmt.order_by(order).limit(limit).offset(offset)
    return db.execute(stmt).scalars().all()


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    return lead


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        if hasattr(lead, field):
            setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/enrich", response_model=LeadOut)
def reenrich_lead(lead_id: int, db: Session = Depends(get_db)):
    """Re-run AI enrichment (summary, opportunity, strategy, competitors, proposal, score)."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    # Clear existing children so re-enrichment doesn't duplicate.
    lead.competitors.clear()
    lead.outreach_messages.clear()
    db.commit()
    _enrich_lead(db, lead, lead.target_service or "website development")
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    """GDPR / TZ DPA right-to-erasure: hard-delete a lead and its children."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    db.delete(lead)
    db.commit()
