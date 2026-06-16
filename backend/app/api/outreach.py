"""Outreach generation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, OutreachMessage
from app.schemas import OutreachGenerateRequest, OutreachOut
from app.services import outreach as outreach_svc

router = APIRouter(prefix="/leads/{lead_id}/outreach", tags=["outreach"])


@router.get("", response_model=list[OutreachOut])
def list_outreach(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")
    return lead.outreach_messages


@router.post("/generate", response_model=list[OutreachOut])
def generate_outreach(
    lead_id: int, payload: OutreachGenerateRequest, db: Session = Depends(get_db)
):
    """(Re)generate outreach messages for the requested channels."""
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "lead not found")

    channels = payload.channels or outreach_svc.CHANNELS
    # Replace existing messages for those channels.
    for msg in list(lead.outreach_messages):
        if msg.channel in channels:
            db.delete(msg)
    db.commit()

    created: list[OutreachMessage] = []
    for msg in outreach_svc.generate_all(lead, channels):
        row = OutreachMessage(
            lead_id=lead.id, channel=msg["channel"],
            subject=msg.get("subject"), body=msg["body"],
        )
        db.add(row)
        created.append(row)
    db.commit()
    for r in created:
        db.refresh(r)
    return created
