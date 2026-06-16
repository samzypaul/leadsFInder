"""Competitor discovery + gap comparison.

Strategy (best signal first):
  1. AI (Gemini): ask for real competitors in the same niche + location.
  2. Live Google Custom Search (if a key is configured).
  3. Curated fixtures by category bucket.
"""
from __future__ import annotations

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import is_owned_website
from app.scrapers.google_search import google_search
from app.services import ai


def _ai_competitors(lead, limit: int) -> list[dict]:
    niche = lead.industry or lead.category or "business"
    loc = lead.city or lead.region or "Tanzania"
    prompt = (
        f"List up to {limit} real, well-known competitor businesses operating as a {niche} "
        f"in or near {loc}, Tanzania. For each give name, website_url (or null if unknown), "
        f"and a short key_services description. Prefer real businesses; if unsure, return fewer. "
        'Return JSON: {"competitors": [{"name": "...", "website_url": "...", "key_services": "..."}]}'
    )

    def fallback() -> dict:
        return {"competitors": []}

    data, ai_used = ai.generate_json(prompt, fallback)
    comps = data.get("competitors") or []
    cleaned = []
    for c in comps:
        name = (c.get("name") or "").strip()
        if name:
            cleaned.append({
                "name": name[:120],
                "website_url": c.get("website_url") or None,
                "key_services": c.get("key_services"),
            })
    return cleaned[:limit] if ai_used else []


def find_competitors(lead, limit: int = 5) -> list[dict]:
    """Return [{name, website_url, key_services}] for same-niche competitors."""
    # 1. AI-driven discovery (preferred — works for any niche).
    if settings.ai_enabled:
        ai_comps = _ai_competitors(lead, limit)
        if ai_comps:
            return ai_comps

    # 2. Live search.
    category = lead.category or lead.industry or "business"
    results = google_search(f"top {category} in Tanzania", num=10) if settings.search_enabled else []
    competitors: list[dict] = []
    seen: set[str] = set()
    for r in results:
        link = r.get("link") or ""
        name = (r.get("title") or "").split(" - ")[0].split("|")[0].strip()
        if link and is_owned_website(link) and link not in seen and name:
            seen.add(link)
            competitors.append({"name": name[:120], "website_url": link, "key_services": r.get("snippet")})
        if len(competitors) >= limit:
            break
    if competitors:
        return competitors

    # 3. Curated fixtures matched to the lead's niche (never cross-niche).
    fx = _fixture_competitors(category)
    if fx:
        return fx[:limit]

    # 4. Last resort: niche-correct generic competitors (no off-niche businesses, no fake URLs).
    return _generic_competitors(lead, category, limit)


def _fixture_competitors(category: str) -> list[dict]:
    """Return curated competitors only if a bucket genuinely matches the niche."""
    c = (category or "").lower()
    if not c:
        return []
    for key, comps in fixtures.COMPETITOR_FIXTURES.items():
        k = key.lower()
        if k in c or c in k or any(w in c for w in k.split()) or any(w in k for w in c.split()):
            return comps
    return []


def _generic_competitors(lead, category: str, limit: int) -> list[dict]:
    """Niche-correct placeholders when we have no real same-niche data (e.g. AI quota out)."""
    niche = (category or "business").strip()
    loc = lead.region or lead.city or "Tanzania"
    return [
        {
            "name": f"Established {niche.lower()} businesses in {loc}",
            "website_url": None,
            "key_services": (
                f"Leading {niche.lower()}s in {loc} typically run a website with online "
                f"enquiries/booking, SEO and Google Maps — capturing customers this business misses."
            ),
        },
        {
            "name": f"Digitally-active {niche.lower()} competitors",
            "website_url": None,
            "key_services": (
                f"Competitors investing in their online presence convert search demand 24/7, "
                f"while social-only {niche.lower()}s rely on manual enquiries."
            ),
        },
    ][:limit]


def comparison_text(lead, competitors: list[dict], service: str = "website development") -> tuple[str, bool]:
    comp_lines = "\n".join(
        f"- {c['name']} ({c.get('website_url')}): {c.get('key_services')}" for c in competitors
    )
    prompt = (
        f"In 2-4 sentences, explain what these competitors are doing (especially regarding "
        f"'{service}') that {lead.business_name} is missing, and why that matters. Be specific "
        f"and persuasive.\n\nCompetitors:\n{comp_lines}"
    )

    def fallback() -> str:
        from app.services.offering import is_website_service

        names = ", ".join(c["name"] for c in competitors[:3]) or "Competitors"
        if is_website_service(service):
            return (
                f"{names} all run dedicated websites with online booking/enquiry, SEO and Google "
                f"Maps integration — capturing search traffic and converting it 24/7. "
                f"{lead.business_name} currently relies on social media alone, so it is invisible "
                f"to customers searching Google and has no owned funnel to capture and qualify leads."
            )
        return (
            f"{names} are already investing in {service} to win and retain more customers, while "
            f"{lead.business_name} is not — leaving efficiency and revenue on the table. Adopting "
            f"{service} would close that gap and create a competitive edge."
        )

    return ai.generate_text(prompt, fallback)
