"""Lead scoring (1–100) and priority bucketing.

Transparent, rule-based and weighted so results are explainable (`score_breakdown` is stored
on the lead). Factors mirror the spec: followers, reviews, activity, industry value, and the
presence of email/phone plus a maturity signal.
"""
from __future__ import annotations

from app.models import Priority

# Industry value weighting — higher-ticket / website-dependent industries score higher.
INDUSTRY_VALUE = {
    "real estate": 1.0, "tour agency": 1.0, "travel": 1.0, "safari": 1.0,
    "hotel": 0.95, "hospitality": 0.95, "information technology": 0.9, "it": 0.9,
    "automotive": 0.85, "construction": 0.8, "healthcare": 0.85, "clinic": 0.85,
    "restaurant": 0.7, "caterer": 0.65, "retail": 0.6, "beauty": 0.6, "salon": 0.55,
}

# Max points each factor can contribute (sums to 100).
WEIGHTS = {
    "followers": 22,
    "reviews": 16,
    "activity": 12,
    "industry": 20,
    "email": 8,
    "phone": 8,
    "maturity": 14,
}


def _industry_factor(industry: str | None, category: str | None) -> float:
    text = f"{industry or ''} {category or ''}".lower()
    best = 0.5  # neutral default
    for key, val in INDUSTRY_VALUE.items():
        if key in text:
            best = max(best, val)
    return best


def _scaled(value: int | float | None, full: float) -> float:
    """0..1 where `full` (or more) maps to 1.0."""
    if not value:
        return 0.0
    return min(1.0, float(value) / full)


def score_lead(lead) -> tuple[int, str, dict]:
    """Return (score, priority, breakdown)."""
    followers_f = _scaled(lead.followers, 20_000)
    reviews_f = _scaled(lead.reviews_count, 200)
    activity_f = _scaled(lead.posts_count, 400)
    industry_f = _industry_factor(lead.industry, lead.category)
    email_f = 1.0 if lead.email else 0.0
    phone_f = 1.0 if (lead.phone or lead.whatsapp) else 0.0

    # Maturity: blend of rating and having multiple presences/contact channels.
    presence = sum(bool(x) for x in (lead.instagram_url, lead.facebook_url, lead.google_business_url))
    rating_f = (lead.rating or 0) / 5.0
    maturity_f = min(1.0, 0.6 * rating_f + 0.4 * (presence / 3))

    breakdown = {
        "followers": round(WEIGHTS["followers"] * followers_f, 1),
        "reviews": round(WEIGHTS["reviews"] * reviews_f, 1),
        "activity": round(WEIGHTS["activity"] * activity_f, 1),
        "industry": round(WEIGHTS["industry"] * industry_f, 1),
        "email": round(WEIGHTS["email"] * email_f, 1),
        "phone": round(WEIGHTS["phone"] * phone_f, 1),
        "maturity": round(WEIGHTS["maturity"] * maturity_f, 1),
    }
    score = int(round(sum(breakdown.values())))
    score = max(1, min(100, score))
    return score, priority_for(score).value, breakdown


def priority_for(score: int) -> Priority:
    if score >= 80:
        return Priority.HOT
    if score >= 60:
        return Priority.WARM
    if score >= 40:
        return Priority.MEDIUM
    return Priority.LOW
