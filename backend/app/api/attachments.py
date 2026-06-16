"""Proposal / contract file uploads.

Proposals can be uploaded as a PDF (or doc/text), or submitted as plain text. Signed contracts
can be uploaded as PDF or image. Files are stored in the database (small documents) with a size
cap; metadata is returned and bytes are streamed back on download. Access is owner-scoped.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Attachment, Lead, User
from app.schemas import AttachmentOut, ProposalTextRequest

router = APIRouter(tags=["attachments"])

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED = {
    "proposal": {"application/pdf", "text/plain", "application/msword",
                 "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    "contract": {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp"},
}


def _owned_lead(db: Session, lead_id: int, current: User) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead or (not current.is_admin and lead.owner_id != current.id):
        raise HTTPException(404, "lead not found")
    return lead


def _owned_attachment(db: Session, att_id: int, current: User) -> Attachment:
    att = db.get(Attachment, att_id)
    if not att:
        raise HTTPException(404, "attachment not found")
    lead = db.get(Lead, att.lead_id)
    if not lead or (not current.is_admin and lead.owner_id != current.id):
        raise HTTPException(404, "attachment not found")
    return att


@router.get("/leads/{lead_id}/attachments", response_model=list[AttachmentOut])
def list_attachments(lead_id: int, db: Session = Depends(get_db),
                     current: User = Depends(get_current_user)):
    lead = _owned_lead(db, lead_id, current)
    return lead.attachments


@router.post("/leads/{lead_id}/attachments", response_model=AttachmentOut, status_code=201)
async def upload_attachment(
    lead_id: int,
    kind: str = Form(..., description="proposal | contract"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if kind not in ALLOWED:
        raise HTTPException(400, "kind must be 'proposal' or 'contract'")
    lead = _owned_lead(db, lead_id, current)

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"file too large (max {MAX_BYTES // (1024*1024)} MB)")
    ctype = file.content_type or "application/octet-stream"
    if ctype not in ALLOWED[kind]:
        raise HTTPException(415, f"{ctype} not allowed for a {kind} (allowed: {sorted(ALLOWED[kind])})")

    att = Attachment(
        lead_id=lead.id, kind=kind, filename=file.filename or f"{kind}",
        content_type=ctype, size=len(data), data=data,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@router.post("/leads/{lead_id}/attachments/proposal-text", response_model=AttachmentOut, status_code=201)
def upload_proposal_text(lead_id: int, payload: ProposalTextRequest,
                         db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    lead = _owned_lead(db, lead_id, current)
    text = payload.text.strip()
    if not text:
        raise HTTPException(400, "text is empty")
    att = Attachment(
        lead_id=lead.id, kind="proposal", filename=payload.filename or "proposal.txt",
        content_type="text/plain", size=len(text.encode("utf-8")), text_content=text,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@router.get("/attachments/{att_id}/download")
def download_attachment(att_id: int, db: Session = Depends(get_db),
                        current: User = Depends(get_current_user)):
    att = _owned_attachment(db, att_id, current)
    body = att.data if att.data is not None else (att.text_content or "").encode("utf-8")
    return Response(
        content=body, media_type=att.content_type,
        headers={"Content-Disposition": f'inline; filename="{att.filename}"'},
    )


@router.delete("/attachments/{att_id}", status_code=204)
def delete_attachment(att_id: int, db: Session = Depends(get_db),
                      current: User = Depends(get_current_user)):
    att = _owned_attachment(db, att_id, current)
    db.delete(att)
    db.commit()
