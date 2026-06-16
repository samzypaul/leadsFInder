"""Dashboard aggregate stats (scoped to the current user; admins see everything)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Deal, DealStage, Lead, LeadStatus, Priority, ScanJob, User
from app.schemas import ClientAnalytics, ClientRow, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    mine = not current.is_admin

    def scope_lead(stmt):
        return stmt.where(Lead.owner_id == current.id) if mine else stmt

    total_scanned = db.scalar(
        scope_lead(select(func.count(ScanJob.id))) if not mine
        else select(func.count(ScanJob.id)).where(ScanJob.owner_id == current.id)
    ) or 0

    def count_where(*conds) -> int:
        stmt = scope_lead(select(func.count(Lead.id)))
        for c in conds:
            stmt = stmt.where(c)
        return db.scalar(stmt) or 0

    with_website = count_where(Lead.status == LeadStatus.WEBSITE_FOUND.value)
    without_website = count_where(Lead.status == LeadStatus.QUALIFIED_LEAD.value)
    by_priority = {p.value: count_where(Lead.priority == p.value) for p in Priority}

    pipeline_rows = db.execute(
        scope_lead(select(Lead.outreach_status, func.count(Lead.id))).group_by(Lead.outreach_status)
    ).all()
    pipeline = {status: cnt for status, cnt in pipeline_rows}

    recent = db.execute(
        scope_lead(select(Lead)).order_by(Lead.created_at.desc()).limit(8)
    ).scalars().all()

    # ── Funnel + financials (deals joined to owned leads) ──────────────
    deal_q = select(Deal).join(Lead, Deal.lead_id == Lead.id)
    if mine:
        deal_q = deal_q.where(Lead.owner_id == current.id)
    deals = db.execute(deal_q).scalars().all()

    # Financials use the SAME realized (won-deal) basis as the Clients dashboard so the two
    # views always agree. Funnel counts span every stage.
    funnel: dict[str, int] = {s.value: 0 for s in DealStage}
    revenue = cost = deposits = 0.0
    won_deals = [d for d in deals if d.stage == DealStage.WON.value]
    for d in deals:
        funnel[d.stage] = funnel.get(d.stage, 0) + 1
    for d in won_deals:
        revenue += d.revenue or 0.0
        cost += d.cost or 0.0
        deposits += d.deposit or 0.0
    currency = won_deals[0].currency if won_deals else (deals[0].currency if deals else "TZS")

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
        funnel=funnel,
        deals_won=funnel.get(DealStage.WON.value, 0),
        deals_lost=funnel.get(DealStage.LOST.value, 0),
        total_revenue=round(revenue, 2),
        total_cost=round(cost, 2),
        total_profit=round(revenue - cost, 2),
        total_deposits=round(deposits, 2),
        currency=currency,
    )


@router.get("/clients", response_model=ClientAnalytics)
def client_analytics(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Analytics over won clients (and lost deals) for the current user."""
    q = select(Deal, Lead).join(Lead, Deal.lead_id == Lead.id)
    if not current.is_admin:
        q = q.where(Lead.owner_id == current.id)
    rows = db.execute(q).all()

    won = [(d, l) for d, l in rows if d.stage == DealStage.WON.value]
    lost = [(d, l) for d, l in rows if d.stage == DealStage.LOST.value]

    revenue = sum(d.revenue or 0.0 for d, _ in won)
    cost = sum(d.cost or 0.0 for d, _ in won)
    deposits = sum(d.deposit or 0.0 for d, _ in won)
    currency = won[0][0].currency if won else (rows[0][0].currency if rows else "TZS")
    decided = len(won) + len(lost)

    top = sorted(won, key=lambda dl: dl[0].revenue or 0.0, reverse=True)[:5]
    top_clients = [
        ClientRow(id=l.id, business_name=l.business_name, revenue=d.revenue or 0.0,
                  profit=d.profit, currency=d.currency)
        for d, l in top
    ]

    return ClientAnalytics(
        clients=len(won),
        lost=len(lost),
        win_rate=round(len(won) / decided, 3) if decided else 0.0,
        total_revenue=round(revenue, 2),
        total_cost=round(cost, 2),
        total_profit=round(revenue - cost, 2),
        total_deposits=round(deposits, 2),
        outstanding=round(revenue - deposits, 2),
        avg_deal_size=round(revenue / len(won), 2) if won else 0.0,
        currency=currency,
        top_clients=top_clients,
    )
