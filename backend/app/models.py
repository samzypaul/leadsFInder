"""Database schema (SQLAlchemy ORM models).

Design notes
------------
* `Lead` is the central entity. Structured, queryable fields are columns; AI-generated
  long-form / nested content (opportunity analysis, marketing strategy, proposal) lives in
  JSON columns so the schema stays stable as prompts evolve.
* `ScanJob` records each run of the discovery workflow and links to the lead it produced,
  giving full provenance (which input produced which lead, what the verdict was, errors).
* `OutreachMessage` and `Competitor` are 1-to-many children of a lead.
* Enums are stored as plain strings for portability across Postgres/SQLite.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LeadStatus(str, enum.Enum):
    WEBSITE_FOUND = "Website Found"
    QUALIFIED_LEAD = "Qualified Lead"
    PROCESSING = "Processing"
    ERROR = "Error"


class OutreachStatus(str, enum.Enum):
    NEW = "new"
    CONTACTED = "contacted"
    REPLIED = "replied"
    MEETING = "meeting"
    WON = "won"
    LOST = "lost"


class Priority(str, enum.Enum):
    HOT = "Hot Lead"
    WARM = "Warm Lead"
    MEDIUM = "Medium Lead"
    LOW = "Low Priority"


class ScanStage(str, enum.Enum):
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_BUSINESS = "google_business"
    DEEP_SEARCH = "deep_search"
    LEAD_CREATED = "lead_created"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)

    # ── Business details ──────────────────────────────────────────────
    business_name: Mapped[str] = mapped_column(String(255), index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    # ── Online presence ───────────────────────────────────────────────
    instagram_url: Mapped[str | None] = mapped_column(String(512))
    facebook_url: Mapped[str | None] = mapped_column(String(512))
    google_business_url: Mapped[str | None] = mapped_column(String(512))
    website_url: Mapped[str | None] = mapped_column(String(512))

    # ── Contact ───────────────────────────────────────────────────────
    phone: Mapped[str | None] = mapped_column(String(64))
    whatsapp: Mapped[str | None] = mapped_column(String(64))
    email: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(String(512))
    city: Mapped[str | None] = mapped_column(String(128))
    region: Mapped[str | None] = mapped_column(String(128))
    country: Mapped[str | None] = mapped_column(String(128), default="Tanzania")

    # ── Social signals (used by scoring) ──────────────────────────────
    followers: Mapped[int | None] = mapped_column(Integer)
    posts_count: Mapped[int | None] = mapped_column(Integer)
    reviews_count: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[float | None] = mapped_column(Float)

    # ── Targeting ─────────────────────────────────────────────────────
    target_service: Mapped[str | None] = mapped_column(String(255))  # what we'd sell them

    # ── Workflow verdict ──────────────────────────────────────────────
    status: Mapped[str] = mapped_column(String(32), default=LeadStatus.PROCESSING.value, index=True)
    outreach_status: Mapped[str] = mapped_column(String(32), default=OutreachStatus.NEW.value, index=True)

    # ── Scoring ───────────────────────────────────────────────────────
    score: Mapped[int | None] = mapped_column(Integer, index=True)
    priority: Mapped[str | None] = mapped_column(String(32), index=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON)

    # ── AI-generated content ──────────────────────────────────────────
    ai_summary: Mapped[str | None] = mapped_column(Text)
    opportunity_analysis: Mapped[dict | None] = mapped_column(JSON)  # {"reasons": [...]}
    marketing_strategy: Mapped[dict | None] = mapped_column(JSON)    # {"website": [...], "ai": [...], "marketing": [...]}
    proposal: Mapped[dict | None] = mapped_column(JSON)              # structured proposal sections
    competitor_comparison: Mapped[str | None] = mapped_column(Text)

    # ── Provenance / raw data ─────────────────────────────────────────
    raw_data: Mapped[dict | None] = mapped_column(JSON)  # raw scraped payloads per source
    source_url: Mapped[str | None] = mapped_column(String(512))      # original input
    ai_generated: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utcnow
    )

    competitors: Mapped[list["Competitor"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    outreach_messages: Mapped[list["OutreachMessage"]] = relationship(
        back_populates="lead", cascade="all, delete-orphan"
    )
    scan_jobs: Mapped[list["ScanJob"]] = relationship(back_populates="lead")


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    website_url: Mapped[str | None] = mapped_column(String(512))
    key_services: Mapped[str | None] = mapped_column(Text)

    lead: Mapped["Lead"] = relationship(back_populates="competitors")


class OutreachMessage(Base):
    __tablename__ = "outreach_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(32))  # email | whatsapp | instagram | facebook | linkedin
    subject: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lead: Mapped["Lead"] = relationship(back_populates="outreach_messages")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    input_url: Mapped[str | None] = mapped_column(String(512))
    input_name: Mapped[str | None] = mapped_column(String(255))
    service: Mapped[str | None] = mapped_column(String(255))  # the offering being sold
    hint_category: Mapped[str | None] = mapped_column(String(255))  # niche hint from discovery
    hint_city: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued|running|done|error
    final_stage: Mapped[str | None] = mapped_column(String(32))
    verdict: Mapped[str | None] = mapped_column(String(32))  # LeadStatus value
    steps: Mapped[list | None] = mapped_column(JSON)  # ordered trace of each step
    error: Mapped[str | None] = mapped_column(Text)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    lead: Mapped["Lead | None"] = relationship(back_populates="scan_jobs")
