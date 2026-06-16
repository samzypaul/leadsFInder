"""Shared scraper primitives: the ProfileData container and contact extraction helpers.

Every concrete scraper returns a `ProfileData`. The discovery workflow only ever consumes
this normalized shape, so swapping a fallback implementation for a real one (or an official
API) never touches the workflow code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

# ── Contact / link extraction regexes ─────────────────────────────────
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Tanzania numbers: +255 / 0 prefixes, plus generic international.
PHONE_RE = re.compile(r"(?:\+?255|0)\s?7\d{2}[\s-]?\d{3}[\s-]?\d{3}|\+\d{7,15}")
WHATSAPP_RE = re.compile(r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?\d{7,15})")
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+")

# Hosts that are NOT a business's *own* website. Three buckets:
#   1. Social platforms / link-shorteners / chat apps
#   2. Search & map surfaces
#   3. Third-party directories & marketplaces (a listing there is not an owned site)
NON_WEBSITE_HOSTS = {
    # social / shorteners / chat
    "instagram.com", "www.instagram.com", "facebook.com", "www.facebook.com",
    "fb.com", "m.facebook.com", "wa.me", "api.whatsapp.com", "whatsapp.com",
    "linktr.ee", "linktree.com", "bit.ly", "linkin.bio", "tiktok.com",
    "twitter.com", "x.com", "youtube.com", "t.me", "telegram.me",
    # search / maps
    "google.com", "maps.google.com", "goo.gl", "g.page", "business.site",
    # third-party directories / marketplaces
    "tripadvisor.com", "safaribookings.com", "foursquare.com", "yelp.com",
    "property24.co.tz", "property24.com", "jiji.co.tz", "zoomtanzania.com",
    "yellowpages.co.tz", "businesslist.co.tz", "tanzania-web.com",
    "lonelyplanet.com", "booking.com", "expedia.com", "airbnb.com",
}


@dataclass
class ProfileData:
    """Normalized output of any scraper."""
    source: str                       # "instagram" | "facebook" | "google_business" | "search"
    found: bool = False               # was the profile/record located at all?
    business_name: str | None = None
    username: str | None = None
    bio: str | None = None
    category: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: str | None = None
    location: str | None = None
    city: str | None = None
    region: str | None = None
    address: str | None = None
    external_links: list[str] = field(default_factory=list)
    website_url: str | None = None    # the first *owned* website found, if any
    followers: int | None = None
    posts_count: int | None = None
    reviews_count: int | None = None
    rating: float | None = None
    hours: str | None = None
    facebook_url: str | None = None
    instagram_url: str | None = None
    google_business_url: str | None = None
    raw: dict = field(default_factory=dict)
    note: str | None = None           # human-readable note (e.g. "fallback fixture")

    def as_dict(self) -> dict:
        return asdict(self)


def is_owned_website(url: str) -> bool:
    """A link is an 'owned website' if it isn't a social/aggregator/shortener host."""
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    if not host:
        return False
    # Strip leading www. for comparison but keep exact-host membership check.
    return host not in NON_WEBSITE_HOSTS and not any(
        host == h or host.endswith("." + h) for h in NON_WEBSITE_HOSTS
    )


def pick_website(links: list[str]) -> str | None:
    for link in links:
        if is_owned_website(link):
            return link
    return None


def extract_contacts(text: str | None) -> dict:
    """Pull email / phone / whatsapp / links out of free text."""
    if not text:
        return {}
    out: dict = {}
    if m := EMAIL_RE.search(text):
        out["email"] = m.group(0)
    if m := WHATSAPP_RE.search(text):
        out["whatsapp"] = m.group(1)
    if m := PHONE_RE.search(text):
        out["phone"] = re.sub(r"[\s-]", "", m.group(0))
    links = URL_RE.findall(text)
    if links:
        out["external_links"] = links
    return out


def username_from_instagram_url(url: str) -> str | None:
    try:
        path = urlparse(url).path.strip("/")
        return path.split("/")[0] or None
    except Exception:  # noqa: BLE001
        return None
