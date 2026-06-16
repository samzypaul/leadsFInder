"""Lead CRUD + enrichment endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Deal, DealStage, Lead, User
from app.schemas import DealOut, DealUpdate, LeadOut, LeadSummary, LeadUpdate
from app.services.workflow import _enrich_lead

# Map a deal stage onto the lead's quick outreach_status so the pipeline view stays in sync.
_STAGE_TO_OUTREACH = {
    "prospect": "new", "contacted": "contacted", "proposal_sent": "meeting",
    "negotiating": "meeting", "won": "won", "lost": "lost",
}

router = APIRouter(prefix="/leads", tags=["leads"])


def _scope(stmt, current: User):
    """Restrict a leads query to the current user (admins see everything)."""
    if not current.is_admin:
        stmt = stmt.where(Lead.owner_id == current.id)
    return stmt


def _get_owned(db: Session, lead_id: int, current: User) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead or (not current.is_admin and lead.owner_id != current.id):
        raise HTTPException(404, "lead not found")
    return lead


@router.get("", response_model=list[LeadSummary])
def list_leads(
    status: str | None = Query(None),
    priority: str | None = Query(None),
    outreach_status: str | None = Query(None),
    relationship: str | None = Query(
        None, description="lead (active pipeline) | client (won) | lost | all"
    ),
    q: str | None = Query(None, description="search business name"),
    sort: str = Query("score", description="score | created_at | business_name"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = _scope(select(Lead), current)

    # Won deals are "clients", lost are "lost"; everything else is the active pipeline.
    if relationship == "client":
        stmt = stmt.join(Deal, Deal.lead_id == Lead.id).where(Deal.stage == DealStage.WON.value)
    elif relationship == "lost":
        stmt = stmt.join(Deal, Deal.lead_id == Lead.id).where(Deal.stage == DealStage.LOST.value)
    elif relationship == "lead":
        stmt = stmt.outerjoin(Deal, Deal.lead_id == Lead.id).where(
            or_(Deal.id.is_(None), Deal.stage.notin_([DealStage.WON.value, DealStage.LOST.value]))
        )

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
def get_lead(lead_id: int, db: Session = Depends(get_db),
             current: User = Depends(get_current_user)):
    return _get_owned(db, lead_id, current)


@router.patch("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    lead = _get_owned(db, lead_id, current)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        if hasattr(lead, field):
            setattr(lead, field, value)
    db.commit()
    db.refresh(lead)
    return lead


@router.post("/{lead_id}/enrich", response_model=LeadOut)
def reenrich_lead(lead_id: int, db: Session = Depends(get_db),
                  current: User = Depends(get_current_user)):
    """Re-run AI enrichment (summary, opportunity, strategy, competitors, proposal, score)."""
    lead = _get_owned(db, lead_id, current)
    # Clear existing children so re-enrichment doesn't duplicate.
    lead.competitors.clear()
    lead.outreach_messages.clear()
    db.commit()
    _enrich_lead(db, lead, lead.target_service or "website development")
    db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    """GDPR / TZ DPA right-to-erasure: hard-delete a lead and its children."""
    lead = _get_owned(db, lead_id, current)
    db.delete(lead)
    db.commit()


# ── Deal / funnel ──────────────────────────────────────────────────────
def _get_or_create_deal(db: Session, lead: Lead) -> Deal:
    if lead.deal:
        return lead.deal
    deal = Deal(lead_id=lead.id, stage=DealStage.PROSPECT.value)
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@router.get("/{lead_id}/deal", response_model=DealOut)
def get_deal(lead_id: int, db: Session = Depends(get_db),
             current: User = Depends(get_current_user)):
    lead = _get_owned(db, lead_id, current)
    return _get_or_create_deal(db, lead)


@router.put("/{lead_id}/deal", response_model=DealOut)
def update_deal(lead_id: int, payload: DealUpdate, db: Session = Depends(get_db),
                current: User = Depends(get_current_user)):
    lead = _get_owned(db, lead_id, current)
    deal = _get_or_create_deal(db, lead)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(deal, field, value)
    # Keep the lead's quick status + outreach flag in sync with the funnel stage.
    if payload.stage:
        lead.outreach_status = _STAGE_TO_OUTREACH.get(payload.stage, lead.outreach_status)
        if payload.stage != DealStage.PROSPECT.value:
            deal.outreach_made = True
    db.commit()
    db.refresh(deal)
    return deal
