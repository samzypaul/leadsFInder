"""Pydantic request/response models (the API contract)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Auth ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, description="At least 8 characters")
    full_name: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str | None
    is_admin: bool
    brand_name: str | None = None
    business_info: str | None = None
    brand_website: str | None = None
    brand_phone: str | None = None
    brand_email: str | None = None


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    brand_name: str | None = None
    business_info: str | None = None
    brand_website: str | None = None
    brand_phone: str | None = None
    brand_email: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Discovery (targeted + natural-language search) ─────────────────────
class DiscoveryFilters(BaseModel):
    industry: str | None = None
    city: str | None = None
    region: str | None = None
    category: str | None = None  # free-text business niche (any value accepted)
    keywords: list[str] = Field(default_factory=list)
    min_followers: int | None = None
    only_without_website: bool = True
    limit: int = Field(default=10, ge=1, le=50)


class DiscoverRequest(BaseModel):
    """Either a natural-language `query` or explicit `filters` (or both), plus the offering."""
    query: str | None = Field(default=None, description="Natural-language search, e.g. "
                              "'coffee shops in Arusha' or 'law firms in Dodoma'")
    filters: DiscoveryFilters | None = None
    service: str = Field(
        default="website development",
        description="What you're selling. Determines how leads qualify (website-type => "
                    "businesses without a website; otherwise any niche match).",
    )


class Candidate(BaseModel):
    business_name: str
    instagram_url: str | None = None
    category: str | None = None
    city: str | None = None
    region: str | None = None
    followers: int | None = None
    source: str  # "directory" | "google"
    likely_no_website: bool | None = None


class DiscoverResponse(BaseModel):
    interpreted_filters: DiscoveryFilters
    query: str | None
    ai_parsed: bool
    count: int
    candidates: list[Candidate]


class DiscoverScanRequest(DiscoverRequest):
    """Run the full discovery workflow over the matched candidates."""
    candidates: list[Candidate] | None = Field(
        default=None, description="Explicit candidates to scan; if omitted, discovery runs first"
    )
    max_scans: int = Field(default=10, ge=1, le=25)


# ── Scan ──────────────────────────────────────────────────────────────
class ScanRequest(BaseModel):
    instagram_url: str | None = Field(
        default=None, description="Instagram profile URL (primary entrypoint)"
    )
    business_name: str | None = Field(
        default=None, description="Business name (used if no Instagram URL is given)"
    )
    service: str = Field(
        default="website development",
        description="What you're selling. Website-type services qualify businesses that have "
                    "no website; other services qualify any business in the target niche.",
    )


class ScanStep(BaseModel):
    stage: str
    found_website: bool
    detail: str
    data: dict | None = None


class ScanResult(BaseModel):
    job_id: int
    verdict: str
    final_stage: str | None
    website_url: str | None
    steps: list[ScanStep]
    lead_id: int | None


# ── Competitor / Outreach ─────────────────────────────────────────────
class CompetitorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    website_url: str | None
    key_services: str | None


class OutreachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    channel: str
    subject: str | None
    body: str
    created_at: datetime


# ── Deal / funnel ─────────────────────────────────────────────────────
class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    stage: str
    outreach_made: bool
    currency: str
    revenue: float
    cost: float
    deposit: float
    notes: str | None
    profit: float
    outstanding: float
    updated_at: datetime


class DealUpdate(BaseModel):
    stage: str | None = None
    outreach_made: bool | None = None
    currency: str | None = None
    revenue: float | None = None
    cost: float | None = None
    deposit: float | None = None
    notes: str | None = None


# ── Attachments ───────────────────────────────────────────────────────
class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    kind: str
    filename: str
    content_type: str
    size: int
    text_content: str | None
    created_at: datetime


class ProposalTextRequest(BaseModel):
    text: str
    filename: str = "proposal.txt"


# ── Lead ──────────────────────────────────────────────────────────────
class LeadBase(BaseModel):
    business_name: str
    username: str | None = None
    industry: str | None = None
    category: str | None = None
    description: str | None = None
    instagram_url: str | None = None
    facebook_url: str | None = None
    google_business_url: str | None = None
    website_url: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = "Tanzania"
    followers: int | None = None
    posts_count: int | None = None
    reviews_count: int | None = None
    rating: float | None = None


class LeadOut(LeadBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    target_service: str | None
    status: str
    outreach_status: str
    score: int | None
    priority: str | None
    score_breakdown: dict | None
    ai_summary: str | None
    opportunity_analysis: dict | None
    marketing_strategy: dict | None
    proposal: dict | None
    competitor_comparison: str | None
    ai_generated: bool
    created_at: datetime
    updated_at: datetime
    competitors: list[CompetitorOut] = []
    outreach_messages: list[OutreachOut] = []
    deal: DealOut | None = None
    attachments: list[AttachmentOut] = []


class LeadSummary(BaseModel):
    """Lightweight row for list views."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    business_name: str
    category: str | None
    city: str | None
    status: str
    outreach_status: str
    score: int | None
    priority: str | None
    phone: str | None
    email: str | None
    created_at: datetime
    # deal-derived
    deal_stage: str | None = None
    is_client: bool = False
    deal_revenue: float | None = None
    deal_profit: float | None = None
    deal_currency: str | None = None


class LeadUpdate(BaseModel):
    """Editable lead/client details (applies to won and lost alike)."""
    business_name: str | None = None
    industry: str | None = None
    category: str | None = None
    description: str | None = None
    website_url: str | None = None
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    address: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    outreach_status: str | None = None


class ClientRow(BaseModel):
    id: int
    business_name: str
    revenue: float
    profit: float
    currency: str


class ClientAnalytics(BaseModel):
    clients: int
    lost: int
    win_rate: float                     # won / (won + lost)
    total_revenue: float
    total_cost: float
    total_profit: float
    total_deposits: float
    outstanding: float
    avg_deal_size: float
    currency: str
    top_clients: list[ClientRow] = []


# ── Dashboard ─────────────────────────────────────────────────────────
class DashboardStats(BaseModel):
    total_scanned: int
    with_website: int
    without_website: int
    hot_leads: int
    warm_leads: int
    medium_leads: int
    low_leads: int
    pipeline: dict[str, int]            # outreach_status -> count
    by_priority: dict[str, int]
    recent_leads: list[LeadSummary]
    # Funnel + financials (from deals)
    funnel: dict[str, int] = {}         # deal stage -> count
    deals_won: int = 0
    deals_lost: int = 0
    total_revenue: float = 0.0
    total_cost: float = 0.0
    total_profit: float = 0.0
    total_deposits: float = 0.0
    currency: str = "TZS"


# ── Outreach generation request ───────────────────────────────────────
class OutreachGenerateRequest(BaseModel):
    channels: list[str] | None = Field(
        default=None,
        description="Subset of channels to generate; default = all "
                    "(email, whatsapp, instagram, facebook, linkedin)",
    )
