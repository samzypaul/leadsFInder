"""Scan endpoints — trigger and inspect the discovery workflow."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import SessionLocal, get_db
from app.models import ScanJob, User
from app.schemas import ScanRequest, ScanResult, ScanStep
from app.services.workflow import run_workflow

router = APIRouter(prefix="/scan", tags=["scan"])


def _run_job_in_background(job_id: int) -> None:
    """Background task: open its own session (the request's session is closed by then)."""
    db = SessionLocal()
    try:
        job = db.get(ScanJob, job_id)
        if job:
            run_workflow(db, job)
    finally:
        db.close()


def _job_to_result(job: ScanJob) -> ScanResult:
    steps = [ScanStep(**s) for s in (job.steps or [])]
    website = next((s.data.get("website_url") if s.data else None
                    for s in steps if s.found_website and s.data), None)
    # also pull from explicit detail-only website steps
    return ScanResult(
        job_id=job.id,
        verdict=job.verdict or job.status,
        final_stage=job.final_stage,
        website_url=website,
        steps=steps,
        lead_id=job.lead_id,
    )


@router.post("", response_model=ScanResult)
def create_scan(
    payload: ScanRequest,
    background: BackgroundTasks,
    wait: bool = Query(False, description="Run synchronously and return the full result"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if not payload.instagram_url and not payload.business_name:
        raise HTTPException(400, "Provide instagram_url or business_name")

    job = ScanJob(input_url=payload.instagram_url, input_name=payload.business_name,
                  service=payload.service, owner_id=current.id, status="queued")
    db.add(job)
    db.commit()
    db.refresh(job)

    if wait:
        run_workflow(db, job)
        db.refresh(job)
        return _job_to_result(job)

    background.add_task(_run_job_in_background, job.id)
    return ScanResult(job_id=job.id, verdict="queued", final_stage=None,
                      website_url=None, steps=[], lead_id=None)


@router.get("/{job_id}", response_model=ScanResult)
def get_scan(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ScanJob, job_id)
    if not job:
        raise HTTPException(404, "scan job not found")
    return _job_to_result(job)
