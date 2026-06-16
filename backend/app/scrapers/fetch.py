"""HTML fetching with two backends and full compliance gating.

* `fetch_html` — fast path via httpx (used in both modes for generic pages).
* `fetch_html_rendered` — Playwright (sync API) for JS-heavy pages; only used when
  SCRAPER_MODE=live. Playwright's sync API is safe here because scrapers run inside a
  background-task worker thread that has no running asyncio event loop.

Both paths honour robots.txt and per-host politeness delays.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.core.compliance import can_fetch, polite_wait

log = logging.getLogger("leadhunter.fetch")


def fetch_html(url: str) -> str | None:
    """Fetch a URL with httpx. Returns HTML text or None on block/error."""
    if not can_fetch(url):
        log.info("robots.txt disallows %s — skipping", url)
        return None
    polite_wait(url)
    try:
        resp = httpx.get(
            url,
            headers={"User-Agent": settings.scraper_user_agent, "Accept-Language": "en,sw"},
            timeout=settings.scraper_timeout_seconds,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            return resp.text
        log.info("GET %s -> HTTP %s", url, resp.status_code)
    except Exception as exc:  # noqa: BLE001
        log.warning("fetch failed for %s: %s", url, exc)
    return None


def fetch_html_rendered(url: str) -> str | None:
    """Fetch a JS-rendered page via Playwright (sync). Live mode only."""
    if not can_fetch(url):
        log.info("robots.txt disallows %s — skipping", url)
        return None
    polite_wait(url)
    try:
        from playwright.sync_api import sync_playwright  # imported lazily
    except Exception as exc:  # noqa: BLE001
        log.warning("Playwright unavailable (%s); falling back to httpx", exc)
        return fetch_html(url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent=settings.scraper_user_agent, locale="en-US")
            page = ctx.new_page()
            page.goto(url, timeout=settings.scraper_timeout_seconds * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            html = page.content()
            browser.close()
            return html
    except Exception as exc:  # noqa: BLE001
        log.warning("Playwright render failed for %s: %s", url, exc)
        return fetch_html(url)
