"""Competitor discovery + gap comparison."""
from __future__ import annotations

from app.scrapers import fixtures
from app.scrapers.base import is_owned_website
from app.scrapers.google_search import google_search
from app.services import ai


def find_competitors(lead, limit: int = 5) -> list[dict]:
    """Return [{name, website_url, key_services}] for top competitors."""
    category = lead.category or lead.industry or "business"

    # Live search path.
    results = google_search(f"top {category} in Tanzania", num=10) if (
        lead and category
    ) else []
    competitors: list[dict] = []
    seen: set[str] = set()
    for r in results:
        link = r.get("link") or ""
        name = (r.get("title") or "").split(" - ")[0].split("|")[0].strip()
        if link and is_owned_website(link) and link not in seen and name:
            seen.add(link)
            competitors.append(
                {"name": name[:120], "website_url": link, "key_services": r.get("snippet")}
            )
        if len(competitors) >= limit:
            break

    if competitors:
        return competitors

    # Fallback: curated competitor fixtures by category bucket.
    for key, comps in fixtures.COMPETITOR_FIXTURES.items():
        if key.lower() in category.lower() or category.lower() in key.lower():
            return comps[:limit]
    # Generic default
    return fixtures.COMPETITOR_FIXTURES.get("Tour Agency", [])[:limit]


def comparison_text(lead, competitors: list[dict]) -> tuple[str, bool]:
    comp_lines = "\n".join(
        f"- {c['name']} ({c.get('website_url')}): {c.get('key_services')}" for c in competitors
    )
    prompt = (
        f"In 2-4 sentences, explain what these competitors are doing online that "
        f"{lead.business_name} is missing by not having a website. Be specific and persuasive.\n\n"
        f"Competitors:\n{comp_lines}"
    )

    def fallback() -> str:
        names = ", ".join(c["name"] for c in competitors[:3]) or "Competitors"
        return (
            f"{names} all run dedicated websites with online booking/enquiry, SEO and Google "
            f"Maps integration — capturing search traffic and converting it 24/7. "
            f"{lead.business_name} currently relies on social media alone, so it is invisible "
            f"to customers searching Google and has no owned funnel to capture and qualify leads."
        )

    return ai.generate_text(prompt, fallback)
