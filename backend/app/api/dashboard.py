"""Dashboard aggregate stats."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, LeadStatus, Priority, ScanJob
from app.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    total_scanned = db.scalar(select(func.count(ScanJob.id))) or 0

    def count_where(*conds) -> int:
        stmt = select(func.count(Lead.id))
        for c in conds:
            stmt = stmt.where(c)
        return db.scalar(stmt) or 0

    with_website = count_where(Lead.status == LeadStatus.WEBSITE_FOUND.value)
    without_website = count_where(Lead.status == LeadStatus.QUALIFIED_LEAD.value)

    by_priority = {
        p.value: count_where(Lead.priority == p.value) for p in Priority
    }

    # Outreach pipeline counts.
    pipeline_rows = db.execute(
        select(Lead.outreach_status, func.count(Lead.id)).group_by(Lead.outreach_status)
    ).all()
    pipeline = {status: cnt for status, cnt in pipeline_rows}

    recent = db.execute(
        select(Lead).order_by(Lead.created_at.desc()).limit(8)
    ).scalars().all()

    return DashboardStats(
        total_scanned=total_scanned,
        with_website=with_website,
        without_website=without_website,
        hot_leads=by_priority.get(Priority.HOT.value, 0),
        warm_leads=by_priority.get(Priority.WARM.value, 0),
        medium_leads=by_priority.get(Priority.MEDIUM.value, 0),
        low_leads=by_priority.get(Priority.LOW.value, 0),
        pipeline=pipeline,
        by_priority=by_priority,
        recent_leads=recent,
    )
