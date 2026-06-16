"""Profile/branding, password change, deal funnel, attachments, and per-user isolation."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def _signup(client, email, pw="password123"):
    r = client.post("/auth/signup", json={"email": email, "password": pw})
    assert r.status_code == 201
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _make_lead(client, headers) -> int:
    r = client.post("/scan?wait=true", headers=headers,
                    json={"business_name": "Test Biz", "service": "website development"})
    return r.json()["lead_id"]


# ── Profile / branding / password ──────────────────────────────────────
def test_profile_update_and_branding(client):
    h = _signup(client, "user@x.com")
    r = client.patch("/auth/me", headers=h, json={"brand_name": "Acme Digital", "business_info": "We build sites"})
    assert r.status_code == 200
    assert r.json()["brand_name"] == "Acme Digital"
    assert client.get("/auth/me", headers=h).json()["business_info"] == "We build sites"


def test_change_password(client):
    h = _signup(client, "pw@x.com", "oldpass123")
    assert client.post("/auth/change-password", headers=h,
                       json={"current_password": "wrong", "new_password": "newpass123"}).status_code == 400
    assert client.post("/auth/change-password", headers=h,
                       json={"current_password": "oldpass123", "new_password": "newpass123"}).status_code == 204
    assert client.post("/auth/login", json={"email": "pw@x.com", "password": "newpass123"}).status_code == 200


# ── Ownership isolation ────────────────────────────────────────────────
def test_users_only_see_their_own_leads(client):
    a = _signup(client, "a@x.com")
    b = _signup(client, "b@x.com")
    lead_a = _make_lead(client, a)
    # B cannot list or fetch A's lead
    assert client.get(f"/leads/{lead_a}", headers=b).status_code == 404
    assert all(l["id"] != lead_a for l in client.get("/leads", headers=b).json())
    # A can
    assert client.get(f"/leads/{lead_a}", headers=a).status_code == 200


# ── Deal funnel ────────────────────────────────────────────────────────
def test_deal_funnel_and_profit(client):
    h = _signup(client, "deal@x.com")
    lead = _make_lead(client, h)
    r = client.put(f"/leads/{lead}/deal", headers=h,
                   json={"stage": "won", "revenue": 1500000, "cost": 400000, "deposit": 500000})
    assert r.status_code == 200
    d = r.json()
    assert d["stage"] == "won"
    assert d["profit"] == 1100000          # revenue - cost
    assert d["outstanding"] == 1000000     # revenue - deposit
    assert d["outreach_made"] is True
    # lead status synced
    assert client.get(f"/leads/{lead}", headers=h).json()["outreach_status"] == "won"
    # dashboard reflects financials
    stats = client.get("/dashboard/stats", headers=h).json()
    assert stats["total_revenue"] == 1500000
    assert stats["total_profit"] == 1100000
    assert stats["deals_won"] == 1


# ── Attachments ────────────────────────────────────────────────────────
def test_proposal_text_and_contract_upload(client):
    h = _signup(client, "att@x.com")
    lead = _make_lead(client, h)

    # proposal as text
    r = client.post(f"/leads/{lead}/attachments/proposal-text", headers=h,
                    json={"text": "Our proposal: build a website for 1.5M TZS."})
    assert r.status_code == 201 and r.json()["kind"] == "proposal"

    # contract as a (fake) PDF upload
    files = {"file": ("contract.pdf", b"%PDF-1.4 fake", "application/pdf")}
    r = client.post(f"/leads/{lead}/attachments", headers=h, data={"kind": "contract"}, files=files)
    assert r.status_code == 201 and r.json()["kind"] == "contract"

    atts = client.get(f"/leads/{lead}/attachments", headers=h).json()
    assert {a["kind"] for a in atts} == {"proposal", "contract"}

    # download works
    att_id = atts[0]["id"]
    assert client.get(f"/attachments/{att_id}/download", headers=h).status_code == 200


def test_won_lead_becomes_client_and_is_filterable(client):
    h = _signup(client, "clients@x.com")
    won = _make_lead(client, h)
    lost = _make_lead(client, h)
    open_lead = _make_lead(client, h)  # stays in pipeline

    client.put(f"/leads/{won}/deal", headers=h, json={"stage": "won", "revenue": 2000000, "cost": 500000})
    # A lost deal with money entered must NOT count toward realized financials.
    client.put(f"/leads/{lost}/deal", headers=h, json={"stage": "lost", "revenue": 999999, "cost": 111})

    clients = client.get("/leads?relationship=client", headers=h).json()
    assert [c["id"] for c in clients] == [won]
    assert clients[0]["is_client"] is True
    assert clients[0]["deal_revenue"] == 2000000

    pipeline = {l["id"] for l in client.get("/leads?relationship=lead", headers=h).json()}
    assert open_lead in pipeline and won not in pipeline and lost not in pipeline

    lost_list = client.get("/leads?relationship=lost", headers=h).json()
    assert [l["id"] for l in lost_list] == [lost]

    # client analytics
    a = client.get("/dashboard/clients", headers=h).json()
    assert a["clients"] == 1 and a["lost"] == 1
    assert a["win_rate"] == 0.5
    assert a["total_revenue"] == 2000000 and a["total_profit"] == 1500000
    assert a["top_clients"][0]["id"] == won

    # The main dashboard financials must match the clients dashboard (same won-deal basis).
    s = client.get("/dashboard/stats", headers=h).json()
    assert s["total_revenue"] == a["total_revenue"]
    assert s["total_cost"] == a["total_cost"]
    assert s["total_profit"] == a["total_profit"]
    assert s["total_deposits"] == a["total_deposits"]


def test_client_details_editable_including_lost(client):
    h = _signup(client, "edit@x.com")
    lead = _make_lead(client, h)
    client.put(f"/leads/{lead}/deal", headers=h, json={"stage": "lost"})
    # full detail edit still allowed on a lost lead
    r = client.patch(f"/leads/{lead}", headers=h,
                     json={"business_name": "Renamed Co", "email": "new@co.tz", "city": "Mwanza"})
    assert r.status_code == 200
    body = r.json()
    assert body["business_name"] == "Renamed Co" and body["email"] == "new@co.tz" and body["city"] == "Mwanza"


def test_upload_rejects_bad_type(client):
    h = _signup(client, "bad@x.com")
    lead = _make_lead(client, h)
    files = {"file": ("x.exe", b"MZ", "application/x-msdownload")}
    r = client.post(f"/leads/{lead}/attachments", headers=h, data={"kind": "contract"}, files=files)
    assert r.status_code == 415
