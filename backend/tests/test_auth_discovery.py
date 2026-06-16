"""Auth + discovery (filters + natural-language) tests."""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_authdisc.db")
os.environ.setdefault("SCRAPER_MODE", "fallback")
os.environ.setdefault("ADMIN_PASSWORD", "secret123")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app
from app.services.discovery import parse_nl_query, search_businesses


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # context manager fires startup (init_db + admin)
        yield c
    Base.metadata.drop_all(bind=engine)


def _auth(client) -> dict:
    r = client.post("/auth/login", json={"email": "admin@leadhunter.tz", "password": "secret123"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ── Auth ───────────────────────────────────────────────────────────────
def test_protected_route_requires_token(client):
    assert client.get("/leads").status_code == 401


def test_login_and_access(client):
    h = _auth(client)
    assert client.get("/leads", headers=h).status_code == 200
    assert client.get("/auth/me", headers=h).json()["email"] == "admin@leadhunter.tz"


def test_bad_password_rejected(client):
    r = client.post("/auth/login", json={"email": "admin@leadhunter.tz", "password": "nope"})
    assert r.status_code == 401


def test_health_is_public(client):
    assert client.get("/health").status_code == 200


# ── NL parsing ───────────────────────────────────────────────────────────
def test_nl_parse_city_and_industry():
    f, _ = parse_nl_query("find 5 tour operators in Arusha without a website")
    assert f.city == "Arusha"
    assert f.category == "Tour Agency"
    assert f.limit == 5
    assert f.only_without_website is True


def test_nl_parse_min_followers():
    f, _ = parse_nl_query("salons in Dar es Salaam with over 10k followers")
    assert f.city == "Dar es Salaam"
    assert f.min_followers == 10000


def test_nl_plural_keyword_matches_singular_category():
    f, _ = parse_nl_query("hotels without a website")
    assert f.category == "Hotel"
    results = search_businesses(f)
    assert len(results) >= 3
    assert all(r.likely_no_website for r in results)


# ── Discovery API ──────────────────────────────────────────────────────
def test_discover_endpoint_nl(client):
    h = _auth(client)
    r = client.post("/discover", headers=h, json={"query": "tour operators in Arusha without a website"})
    assert r.status_code == 200
    body = r.json()
    assert body["interpreted_filters"]["category"] == "Tour Agency"
    assert body["count"] >= 1


def test_discover_endpoint_filters(client):
    h = _auth(client)
    r = client.post("/discover", headers=h, json={"filters": {"city": "Dar es Salaam", "limit": 10}})
    names = [c["business_name"] for c in r.json()["candidates"]]
    assert "Mama Ndogo Kitchen" in names


def test_discover_scan_creates_leads(client):
    h = _auth(client)
    r = client.post("/discover/scan", headers=h, json={"query": "hotels without a website", "max_scans": 3})
    body = r.json()
    assert body["scanned"] == 3
    assert body["qualified_leads"] == 3
    # leads now visible
    assert len(client.get("/leads", headers=h).json()) >= 3
