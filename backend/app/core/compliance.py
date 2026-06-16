"""Compliance helpers: robots.txt enforcement, polite rate limiting, PII guards.

These are intentionally conservative. The goal is to store only *public business*
information and to behave like a well-mannered crawler.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from urllib import robotparser
from urllib.parse import urlparse

from app.config import settings

log = logging.getLogger("leadhunter.compliance")

# Cache one RobotFileParser per host.
_robots_cache: dict[str, robotparser.RobotFileParser] = {}
_robots_lock = threading.Lock()

# Track last-request time per host for politeness delays.
_last_request: dict[str, float] = {}
_rate_lock = threading.Lock()

# Personal data we deliberately avoid persisting (only business contact data is kept).
_NATIONAL_ID_RE = re.compile(r"\b\d{8}-\d{5}-\d{5}-\d{2}\b")  # TZ NIDA format example


def _host(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def can_fetch(url: str) -> bool:
    """Return True if robots.txt allows fetching `url` for our user agent.

    When RESPECT_ROBOTS is disabled, always returns True. Network failures while reading
    robots.txt fail *open* for the host (treated as allowed) but are logged.
    """
    if not settings.respect_robots:
        return True

    host = _host(url)
    with _robots_lock:
        rp = _robots_cache.get(host)
        if rp is None:
            rp = robotparser.RobotFileParser()
            rp.set_url(f"{host}/robots.txt")
            try:
                rp.read()
            except Exception as exc:  # noqa: BLE001
                log.warning("robots.txt unreadable for %s (%s) — allowing", host, exc)
                rp = None
            _robots_cache[host] = rp  # type: ignore[assignment]

        if rp is None:
            return True
        return rp.can_fetch(settings.scraper_user_agent, url)


def polite_wait(url: str) -> None:
    """Sleep just enough to honour SCRAPER_MIN_DELAY per host."""
    host = _host(url)
    delay = settings.scraper_min_delay
    if delay <= 0:
        return
    with _rate_lock:
        last = _last_request.get(host, 0.0)
        wait = delay - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        _last_request[host] = time.monotonic()


def redact_personal_data(text: str | None) -> str | None:
    """Strip patterns that look like personal (non-business) identifiers."""
    if not text:
        return text
    return _NATIONAL_ID_RE.sub("[redacted]", text)
