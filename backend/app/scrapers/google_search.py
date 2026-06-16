"""Google search wrapper (Steps 3 & 4).

Uses the Google Custom Search JSON API when GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX are set.
Falls back to bundled deep-search fixtures (or an empty list) otherwise, so the workflow's
"analyze top N results" logic always has something to run against.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import is_owned_website

log = logging.getLogger("leadhunter.search")

ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def google_search(query: str, num: int = 10) -> list[dict]:
    """Return [{title, link, snippet}] for a query."""
    if settings.search_enabled:
        try:
            resp = httpx.get(
                ENDPOINT,
                params={
                    "key": settings.google_search_api_key,
                    "cx": settings.google_search_cx,
                    "q": query,
                    "num": min(num, 10),
                    "gl": "tz",
                },
                timeout=settings.scraper_timeout_seconds,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return [
                {"title": i.get("title"), "link": i.get("link"), "snippet": i.get("snippet")}
                for i in items
            ]
        except Exception as exc:  # noqa: BLE001
            log.warning("Google search failed for %r: %s", query, exc)

    # Fallback: fixture URLs keyed by business name found inside the query.
    for name, urls in fixtures.DEEP_SEARCH_FIXTURES.items():
        if name in query.lower():
            return [{"title": name, "link": u, "snippet": ""} for u in urls][:num]
    return []


def find_official_website(business_name: str, max_results: int = 20) -> str | None:
    """Step 4: run several targeted queries over the top `max_results` results.

    Robustness measures:
      * multiple query phrasings (plain, +Tanzania, "official website", site-style)
      * de-duplication across queries
      * a hard cap on total results examined (`max_results`)
      * only links passing `is_owned_website` (rejects social/maps/directory hosts) count
    """
    slug = business_name.lower().replace("&", "and")
    queries = [
        business_name,
        f"{business_name} Tanzania",
        f"{business_name} official website",
        f'"{business_name}" website',
        f"{slug} site:co.tz OR site:com",
    ]
    seen: set[str] = set()
    checked = 0
    for q in queries:
        for result in google_search(q, num=10):
            link = result.get("link")
            if not link or link in seen:
                continue
            seen.add(link)
            checked += 1
            if is_owned_website(link):
                return link
            if checked >= max_results:
                return None
    return None
