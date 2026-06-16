"""The 'offering' — what the user is selling, and how it changes lead qualification.

If the offering is website-related, a business *qualifies* as a lead when it has **no
website** (the classic 5-step verification). For any other service (chatbots, POS, social
media, accounting, ...), website presence is irrelevant — a business qualifies when it
matches the target niche, and the opportunity/proposal/outreach are tailored to that service.
"""
from __future__ import annotations

DEFAULT_SERVICE = "website development"

# Terms that mean "the offering is building/owning a website".
_WEBSITE_TERMS = (
    "website", "web site", "web design", "web development", "webdev",
    "landing page", "web app", "web presence", "site build", "ecommerce site",
)


def is_website_service(service: str | None) -> bool:
    s = (service or "").lower()
    if not s:
        return True  # default offering is website development
    return any(t in s for t in _WEBSITE_TERMS)


def normalize_service(service: str | None) -> str:
    return (service or DEFAULT_SERVICE).strip() or DEFAULT_SERVICE
