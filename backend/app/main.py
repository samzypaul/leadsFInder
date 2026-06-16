"""FastAPI application entrypoint."""
from __future__ import annotations

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, dashboard, discover, export, leads, outreach, scan
from app.api.deps import get_current_user
from app.config import settings
from app.core.bootstrap import ensure_admin_user
from app.database import SessionLocal, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="LeadHunter TZ API",
    version=__version__,
    description="Discover Tanzanian businesses without websites and generate qualified leads.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    init_db()
    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {
        "status": "ok",
        "version": __version__,
        "scraper_mode": settings.scraper_mode,
        "ai_enabled": settings.ai_enabled,
        "search_enabled": settings.search_enabled,
    }


# Public
app.include_router(auth.router)

# Protected (require a valid bearer token unless AUTH_ENABLED=false)
_protected = [Depends(get_current_user)]
app.include_router(scan.router, dependencies=_protected)
app.include_router(leads.router, dependencies=_protected)
app.include_router(outreach.router, dependencies=_protected)
app.include_router(dashboard.router, dependencies=_protected)
app.include_router(export.router, dependencies=_protected)
app.include_router(discover.router)  # has per-route auth deps
