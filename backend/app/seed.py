"""Seed the database by running the discovery workflow over the demo Instagram fixtures.

Usage:
    python -m app.seed            # always seed
    python -m app.seed --if-empty # only seed when there are no leads yet (used in Docker)
"""
from __future__ import annotations

import sys

from sqlalchemy import func, select

from app.core.bootstrap import ensure_admin_user
from app.database import SessionLocal, init_db
from app.models import Lead, ScanJob
from app.scrapers.fixtures import INSTAGRAM_FIXTURES
from app.services.workflow import run_workflow


def seed(if_empty: bool = False) -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_admin_user(db)
        if if_empty and (db.scalar(select(func.count(Lead.id))) or 0) > 0:
            print("Database already has leads; skipping seed.")
            return

        for username in INSTAGRAM_FIXTURES:
            url = f"https://www.instagram.com/{username}/"
            job = ScanJob(input_url=url, status="queued")
            db.add(job)
            db.commit()
            db.refresh(job)
            run_workflow(db, job)
            print(f"  seeded {username:30s} -> {job.verdict}")
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed(if_empty="--if-empty" in sys.argv)
