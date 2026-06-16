"""Targeted business discovery + natural-language query parsing.

`parse_nl_query` turns a free-text request ("tour operators in Arusha without a website")
into structured `DiscoveryFilters` — via Gemini when available, otherwise a deterministic
keyword/city parser. `search_businesses` then finds candidate businesses matching those
filters, from the bundled directory (fallback) or Google Places/CSE (live).
"""
from __future__ import annotations

import logging
import re

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import is_owned_website
from app.scrapers.google_search import google_search
from app.schemas import Candidate, DiscoveryFilters
from app.services import ai

log = logging.getLogger("leadhunter.discovery")


# ── Natural-language → filters ─────────────────────────────────────────
def parse_nl_query(query: str) -> tuple[DiscoveryFilters, bool]:
    """Return (filters, ai_parsed)."""
    prompt = (
        "You convert a sales rep's natural-language request into JSON search filters for "
        "discovering Tanzanian businesses. Keys: industry (string|null), category (string|null), "
        "city (string|null), region (string|null), keywords (array of strings), "
        "min_followers (int|null), only_without_website (bool, default true), "
        "limit (int 1-50, default 10). Only output JSON.\n\n"
        f"Request: {query!r}"
    )

    def fallback() -> dict:
        return _heuristic_parse(query).model_dump()

    data, ai_parsed = ai.generate_json(prompt, fallback)
    try:
        filters = DiscoveryFilters(**{k: v for k, v in data.items()
                                      if k in DiscoveryFilters.model_fields})
    except Exception:  # noqa: BLE001
        filters, ai_parsed = _heuristic_parse(query), False
    return filters, ai_parsed


def _heuristic_parse(query: str) -> DiscoveryFilters:
    q = query.lower()
    f = DiscoveryFilters()

    # City / region
    for city in fixtures.TZ_CITIES:
        if city.lower() in q:
            f.city = city
            f.region = fixtures.CITY_TO_REGION.get(city)
            break

    # Industry / category
    for kw, category in fixtures.INDUSTRY_KEYWORDS.items():
        if kw.strip() in q:
            f.category = category
            break

    # "with no website" / "without a website" -> only_without_website
    if re.search(r"(with|has)\s+(a\s+)?websites?", q) and "without" not in q and "no website" not in q:
        f.only_without_website = False

    # min followers, e.g. "over 5000 followers", "5k followers"
    m = re.search(r"(\d[\d,\.]*)\s*([kK])?\s*\+?\s*followers", q)
    if m:
        n = float(m.group(1).replace(",", ""))
        if m.group(2):
            n *= 1000
        f.min_followers = int(n)

    # limit, e.g. "top 5", "find 20"
    m = re.search(r"\b(?:top|find|show|get)\s+(\d{1,2})\b", q)
    if m:
        f.limit = max(1, min(50, int(m.group(1))))

    # leftover keywords (drop stop words, location words, and anything already captured
    # as a city/industry so a redundant token can't over-filter the results).
    stop = {"in", "the", "a", "with", "without", "no", "website", "websites", "businesses",
            "business", "find", "show", "me", "top", "and", "that", "have", "has", "of",
            "tanzania", "tanzanian", "followers", "over", "under", "get", "all", "list"}
    stop.update(k.strip() for k in fixtures.INDUSTRY_KEYWORDS)        # industry words
    if f.category:
        stop.update(f.category.lower().split())
    if f.city:
        stop.update(f.city.lower().split())
    tokens = [t for t in re.findall(r"[a-z]+", q) if t not in stop and len(t) > 2]
    f.keywords = list(dict.fromkeys(tokens))[:5]
    return f


def _singular(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") else word


# ── Candidate search ───────────────────────────────────────────────────
def search_businesses(filters: DiscoveryFilters) -> list[Candidate]:
    if settings.search_enabled:
        live = _search_google(filters)
        if live:
            return live[: filters.limit]
    return _search_directory(filters)[: filters.limit]


def _matches(entry: dict, filters: DiscoveryFilters) -> bool:
    if filters.only_without_website and entry.get("has_website"):
        return False
    if filters.city and filters.city.lower() not in (entry.get("city") or "").lower() \
            and (entry.get("city") or "").lower() not in filters.city.lower():
        return False
    if filters.region and filters.region.lower() not in (entry.get("region") or "").lower():
        return False
    target = f"{entry.get('category','')} {entry.get('industry','')}".lower()
    if filters.category and filters.category.lower() not in target \
            and not any(w in target for w in filters.category.lower().split()):
        return False
    if filters.industry and filters.industry.lower() not in target \
            and not any(w in target for w in filters.industry.lower().split()):
        return False
    if filters.min_followers and (entry.get("followers") or 0) < filters.min_followers:
        return False
    # Keywords are only a *hard* filter when they're the sole signal. If a structured
    # filter (city/region/category/industry) already matched, free-text keywords like
    # "operators" or "shop" merely refine ranking and must not exclude valid results.
    has_structured = any([filters.city, filters.region, filters.category, filters.industry])
    if filters.keywords and not has_structured:
        hay = f"{entry.get('business_name','')} {target} {entry.get('city','')}".lower()
        if not any(_singular(k.lower()) in hay for k in filters.keywords):
            return False
    return True


def _search_directory(filters: DiscoveryFilters) -> list[Candidate]:
    out: list[Candidate] = []
    for entry in fixtures.BUSINESS_DIRECTORY:
        if not _matches(entry, filters):
            continue
        ig = entry.get("instagram")
        out.append(Candidate(
            business_name=entry["business_name"],
            instagram_url=f"https://www.instagram.com/{ig}/" if ig else None,
            category=entry.get("category"),
            city=entry.get("city"),
            region=entry.get("region"),
            followers=entry.get("followers"),
            source="directory",
            likely_no_website=not entry.get("has_website", False),
        ))
    # Sort by followers desc so the strongest opportunities surface first.
    out.sort(key=lambda c: c.followers or 0, reverse=True)
    return out


def _search_google(filters: DiscoveryFilters) -> list[Candidate]:
    """Live discovery via Google Custom Search (best-effort candidate extraction)."""
    bits = [filters.category or filters.industry or "businesses"]
    if filters.city:
        bits.append(f"in {filters.city}")
    bits.append("Tanzania")
    if filters.only_without_website:
        bits.append("instagram")  # bias toward social-first businesses
    query = " ".join(bits)

    candidates: list[Candidate] = []
    seen: set[str] = set()
    for r in google_search(query, num=10):
        link = r.get("link") or ""
        name = (r.get("title") or "").split(" - ")[0].split("|")[0].strip()
        if not name or name in seen:
            continue
        seen.add(name)
        ig = link if "instagram.com" in link else None
        candidates.append(Candidate(
            business_name=name[:120],
            instagram_url=ig,
            category=filters.category or filters.industry,
            city=filters.city,
            region=filters.region,
            source="google",
            likely_no_website=not is_owned_website(link),
        ))
    return candidates
