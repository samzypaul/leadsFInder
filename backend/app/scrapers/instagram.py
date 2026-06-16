"""Instagram profile scraper (Step 1).

Live mode renders the public profile with Playwright and parses og/meta + embedded JSON.
Fallback mode returns a bundled fixture when available, otherwise makes a best-effort httpx
read of the public page's meta tags. Either way the workflow gets a normalized ProfileData.
"""
from __future__ import annotations

import json
import logging
import re

from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import (
    ProfileData,
    extract_contacts,
    pick_website,
    username_from_instagram_url,
)
from app.scrapers.fetch import fetch_html, fetch_html_rendered

log = logging.getLogger("leadhunter.instagram")

_COUNT_RE = re.compile(r"([\d,.]+)\s*([KkMm]?)\s*Followers", re.I)


def _parse_count(text: str) -> int | None:
    m = _COUNT_RE.search(text)
    if not m:
        return None
    num = float(m.group(1).replace(",", ""))
    mult = {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1)
    return int(num * mult)


def _from_fixture(username: str, url: str) -> ProfileData | None:
    raw = fixtures.INSTAGRAM_FIXTURES.get(username)
    if not raw:
        return None
    links = list(raw.get("external_links", []))
    return ProfileData(
        source="instagram",
        found=True,
        business_name=raw.get("business_name"),
        username=raw.get("username"),
        bio=raw.get("bio"),
        category=raw.get("category"),
        phone=raw.get("phone"),
        whatsapp=raw.get("whatsapp"),
        email=raw.get("email"),
        location=raw.get("location"),
        external_links=links,
        website_url=pick_website(links),
        followers=raw.get("followers"),
        posts_count=raw.get("posts_count"),
        facebook_url=raw.get("facebook_url"),
        instagram_url=url,
        raw=raw,
        note="fixture",
    )


def _parse_html(html: str, url: str, username: str) -> ProfileData:
    soup = BeautifulSoup(html, "lxml")
    pd = ProfileData(source="instagram", instagram_url=url, username=username)

    # og:description holds "<followers> Followers, <posts> Posts - <name> (@user) ..."
    desc_tag = soup.find("meta", property="og:description")
    title_tag = soup.find("meta", property="og:title")
    desc = desc_tag.get("content", "") if desc_tag else ""
    title = title_tag.get("content", "") if title_tag else ""

    pd.found = bool(desc or title)
    pd.bio = desc or None
    pd.followers = _parse_count(desc)
    if title:
        pd.business_name = re.split(r"[•|(]", title)[0].strip() or None

    # Embedded JSON sometimes contains external_url + biography.
    for script in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(script.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        blob = json.dumps(data)
        if "external_url" in blob:
            m = re.search(r'"external_url":"(https?:[^"]+)"', blob)
            if m:
                pd.external_links.append(m.group(1).replace("\\/", "/"))

    contacts = extract_contacts((desc or "") + " " + " ".join(pd.external_links))
    pd.email = pd.email or contacts.get("email")
    pd.phone = pd.phone or contacts.get("phone")
    pd.whatsapp = pd.whatsapp or contacts.get("whatsapp")
    if contacts.get("external_links"):
        pd.external_links.extend(contacts["external_links"])

    pd.website_url = pick_website(pd.external_links)
    pd.business_name = pd.business_name or (username.title() if username else None)
    return pd


def scrape_instagram(url: str) -> ProfileData:
    username = (username_from_instagram_url(url) or "").lower()

    # Fixtures first in fallback mode (deterministic + offline-safe).
    if settings.scraper_mode != "live":
        fx = _from_fixture(username, url)
        if fx:
            return fx

    html = (
        fetch_html_rendered(url)
        if settings.scraper_mode == "live"
        else fetch_html(url)
    )
    if html:
        try:
            return _parse_html(html, url, username)
        except Exception as exc:  # noqa: BLE001
            log.warning("instagram parse failed for %s: %s", url, exc)

    # Last resort: empty-but-shaped result so the workflow can proceed.
    fx = _from_fixture(username, url)
    if fx:
        return fx
    return ProfileData(
        source="instagram", found=False, instagram_url=url,
        username=username or None,
        business_name=username.title() if username else None,
        note="not-found",
    )
