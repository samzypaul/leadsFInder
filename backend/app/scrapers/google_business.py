"""Google Business Profile lookup (Step 3).

Production note
---------------
Reliable GBP data comes from the **Google Places API** (Place Details), not HTML scraping.
This module is structured so you can drop a Places API call into `_from_places_api`. In
fallback mode it returns bundled fixtures; with a search key it at least locates the GBP/maps
URL via Custom Search and extracts what it can.
"""
from __future__ import annotations

import logging

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import ProfileData, is_owned_website
from app.scrapers.google_search import google_search

log = logging.getLogger("leadhunter.gbp")


def _from_fixture(business_name: str) -> ProfileData | None:
    raw = fixtures.GOOGLE_BUSINESS_FIXTURES.get(business_name.strip().lower())
    if not raw:
        return None
    website = raw.get("website")
    return ProfileData(
        source="google_business",
        found=True,
        business_name=raw.get("business_name"),
        category=raw.get("category"),
        phone=raw.get("phone"),
        address=raw.get("address"),
        city=raw.get("city"),
        region=raw.get("region"),
        reviews_count=raw.get("reviews_count"),
        rating=raw.get("rating"),
        hours=raw.get("hours"),
        website_url=website if website and is_owned_website(website) else None,
        raw=raw,
        note="fixture",
    )


def scrape_google_business(business_name: str) -> ProfileData:
    # Fixtures first when not live.
    if settings.scraper_mode != "live":
        fx = _from_fixture(business_name)
        if fx:
            return fx

    # Live-ish: locate the GBP / maps / g.page link via search.
    if settings.search_enabled:
        results = google_search(f"{business_name} Tanzania Google Business Profile", num=10)
        gbp_url = None
        website = None
        for r in results:
            link = r.get("link", "")
            if any(h in link for h in ("g.page", "maps.google", "business.site")):
                gbp_url = gbp_url or link
            elif is_owned_website(link) and website is None:
                website = link
        if gbp_url or website:
            return ProfileData(
                source="google_business",
                found=True,
                business_name=business_name,
                google_business_url=gbp_url,
                website_url=website,
                note="search-derived",
            )

    fx = _from_fixture(business_name)
    if fx:
        return fx
    return ProfileData(source="google_business", found=False, business_name=business_name, note="not-found")
