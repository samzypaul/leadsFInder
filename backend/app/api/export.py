"""Export + CRM integration endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead
from app.services import exporters

router = APIRouter(prefix="/export", tags=["export"])


def _select_leads(db: Session, status: str | None, ids: list[int] | None) -> list[Lead]:
    stmt = select(Lead)
    if ids:
        stmt = stmt.where(Lead.id.in_(ids))
    elif status:
        stmt = stmt.where(Lead.status == status)
    return db.execute(stmt.order_by(Lead.score.desc())).scalars().all()


@router.get("/csv")
def export_csv(
    status: str | None = Query(None), db: Session = Depends(get_db)
):
    leads = _select_leads(db, status, None)
    data = exporters.to_csv(leads)
    return Response(
        content=data, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/excel")
def export_excel(status: str | None = Query(None), db: Session = Depends(get_db)):
    leads = _select_leads(db, status, None)
    data = exporters.to_excel(leads)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=leads.xlsx"},
    )


@router.post("/{provider}")
def export_crm(
    provider: str,
    status: str | None = Query(None),
    ids: list[int] | None = Query(None),
    credentials: dict = Body(default_factory=dict),
    db: Session = Depends(get_db),
):
    """Push leads to a CRM/Sheets provider.

    Pass credentials in the body, e.g.:
      hubspot:      {"token": "..."}
      salesforce:   {"instance_url": "...", "token": "..."}
      airtable:     {"token": "...", "base_id": "...", "table": "Leads"}
      google_sheets:{"access_token": "...", "spreadsheet_id": "..."}

    Without credentials the endpoint returns the exact payload that would be sent.
    """
    leads = _select_leads(db, status, ids)
    c = credentials or {}
    if provider == "hubspot":
        return exporters.push_hubspot(leads, c.get("token"))
    if provider == "salesforce":
        return exporters.push_salesforce(leads, c.get("instance_url"), c.get("token"))
    if provider == "airtable":
        return exporters.push_airtable(leads, c.get("token"), c.get("base_id"), c.get("table"))
    if provider == "google_sheets":
        return exporters.push_google_sheets(leads, c.get("access_token"), c.get("spreadsheet_id"))
    raise HTTPException(400, f"unknown provider '{provider}'")
