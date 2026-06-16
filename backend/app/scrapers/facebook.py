"""Facebook page scraper (Step 2)."""
from __future__ import annotations

import logging
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from app.config import settings
from app.scrapers import fixtures
from app.scrapers.base import ProfileData, extract_contacts, pick_website
from app.scrapers.fetch import fetch_html, fetch_html_rendered

log = logging.getLogger("leadhunter.facebook")


def _page_slug(url: str) -> str:
    path = urlparse(url).path.strip("/")
    # handle profile.php?id=... and /pages/name/id
    return (path.split("/")[0] or "").lower()


def _from_fixture(slug: str, url: str) -> ProfileData | None:
    raw = fixtures.FACEBOOK_FIXTURES.get(slug)
    if not raw:
        return None
    website = raw.get("website")
    return ProfileData(
        source="facebook",
        found=True,
        business_name=raw.get("business_name"),
        bio=raw.get("about"),
        category=raw.get("category"),
        phone=raw.get("phone"),
        email=raw.get("email"),
        location=raw.get("location"),
        website_url=website if website and pick_website([website]) else None,
        external_links=[website] if website else [],
        facebook_url=url,
        raw=raw,
        note="fixture",
    )


def _parse_html(html: str, url: str) -> ProfileData:
    soup = BeautifulSoup(html, "lxml")
    pd = ProfileData(source="facebook", facebook_url=url)

    title = soup.find("meta", property="og:title")
    desc = soup.find("meta", property="og:description")
    pd.business_name = (title.get("content").strip() if title else None) or None
    pd.bio = desc.get("content") if desc else None
    text = " ".join(filter(None, [pd.business_name, pd.bio, html[:20000]]))

    # External website links that aren't facebook itself.
    links = re.findall(r'href="(https?://[^"]+)"', html)
    links = [re_unescape(l) for l in links]
    pd.external_links = links
    pd.website_url = pick_website(links)

    contacts = extract_contacts(text)
    pd.email = contacts.get("email")
    pd.phone = contacts.get("phone")
    pd.whatsapp = contacts.get("whatsapp")
    pd.found = bool(pd.business_name or pd.bio)
    return pd


def re_unescape(s: str) -> str:
    return s.replace("&amp;", "&").replace("\\/", "/")


def scrape_facebook(url: str) -> ProfileData:
    slug = _page_slug(url)

    if settings.scraper_mode != "live":
        fx = _from_fixture(slug, url)
        if fx:
            return fx

    html = fetch_html_rendered(url) if settings.scraper_mode == "live" else fetch_html(url)
    if html:
        try:
            return _parse_html(html, url)
        except Exception as exc:  # noqa: BLE001
            log.warning("facebook parse failed for %s: %s", url, exc)

    fx = _from_fixture(slug, url)
    if fx:
        return fx
    return ProfileData(source="facebook", found=False, facebook_url=url, note="not-found")
