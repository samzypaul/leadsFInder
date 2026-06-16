"""Export / CRM-integration layer.

CSV and Excel are produced in-process (no external dependency). The CRM/Sheets integrations
(`google_sheets`, `airtable`, `hubspot`, `salesforce`) push via each provider's REST API when
credentials are supplied; without credentials they return the exact JSON payload that *would*
be sent, so the integration is fully inspectable and testable offline.
"""
from __future__ import annotations

import csv
import io
import logging

import httpx

from app.models import Lead

log = logging.getLogger("leadhunter.export")

# Flat column order used for tabular exports.
COLUMNS = [
    "id", "business_name", "industry", "category", "status", "outreach_status",
    "score", "priority", "phone", "whatsapp", "email", "city", "region", "country",
    "instagram_url", "facebook_url", "google_business_url", "website_url",
    "followers", "reviews_count", "rating", "ai_summary",
]


def lead_to_row(lead: Lead) -> dict:
    return {c: getattr(lead, c, None) for c in COLUMNS}


# ── CSV / Excel ───────────────────────────────────────────────────────
def to_csv(leads: list[Lead]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        writer.writerow(lead_to_row(lead))
    return buf.getvalue().encode("utf-8")


def to_excel(leads: list[Lead]) -> bytes:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "Leads"
    ws.append(COLUMNS)
    for lead in leads:
        row = lead_to_row(lead)
        ws.append([row.get(c) for c in COLUMNS])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── CRM payload mappers ────────────────────────────────────────────────
def _hubspot_payload(leads: list[Lead]) -> dict:
    return {
        "inputs": [
            {
                "properties": {
                    "company": l.business_name,
                    "phone": l.phone or l.whatsapp,
                    "email": l.email,
                    "city": l.city,
                    "state": l.region,
                    "country": l.country,
                    "industry": l.industry,
                    "website": l.website_url,
                    "hs_lead_status": l.outreach_status,
                    "lead_score": l.score,
                }
            }
            for l in leads
        ]
    }


def _salesforce_payload(leads: list[Lead]) -> dict:
    return {
        "records": [
            {
                "attributes": {"type": "Lead"},
                "Company": l.business_name,
                "LastName": l.business_name,
                "Phone": l.phone or l.whatsapp,
                "Email": l.email,
                "City": l.city,
                "State": l.region,
                "Country": l.country,
                "Industry": l.industry,
                "Website": l.website_url,
                "Rating": l.priority,
                "Description": l.ai_summary,
            }
            for l in leads
        ]
    }


def _airtable_payload(leads: list[Lead]) -> dict:
    return {
        "records": [
            {"fields": {k: v for k, v in lead_to_row(l).items() if v is not None}}
            for l in leads
        ]
    }


def _sheets_values(leads: list[Lead]) -> list[list]:
    rows = [COLUMNS]
    rows.extend([[lead_to_row(l).get(c) for c in COLUMNS] for l in leads])
    return rows


# ── CRM push (with offline payload preview) ─────────────────────────────
def push_hubspot(leads: list[Lead], token: str | None) -> dict:
    payload = _hubspot_payload(leads)
    if not token:
        return {"pushed": False, "reason": "no HUBSPOT token", "payload": payload}
    try:
        r = httpx.post(
            "https://api.hubapi.com/crm/v3/objects/companies/batch/create",
            headers={"Authorization": f"Bearer {token}"},
            json=payload, timeout=30,
        )
        return {"pushed": r.is_success, "status": r.status_code, "response": r.json()}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": False, "error": str(exc), "payload": payload}


def push_salesforce(leads: list[Lead], instance_url: str | None, token: str | None) -> dict:
    payload = _salesforce_payload(leads)
    if not (instance_url and token):
        return {"pushed": False, "reason": "no Salesforce instance_url/token", "payload": payload}
    try:
        r = httpx.post(
            f"{instance_url}/services/data/v60.0/composite/sobjects",
            headers={"Authorization": f"Bearer {token}"},
            json=payload, timeout=30,
        )
        return {"pushed": r.is_success, "status": r.status_code, "response": r.json()}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": False, "error": str(exc), "payload": payload}


def push_airtable(leads: list[Lead], token: str | None, base_id: str | None, table: str | None) -> dict:
    payload = _airtable_payload(leads)
    if not (token and base_id and table):
        return {"pushed": False, "reason": "no Airtable token/base/table", "payload": payload}
    try:
        r = httpx.post(
            f"https://api.airtable.com/v0/{base_id}/{table}",
            headers={"Authorization": f"Bearer {token}"},
            json=payload, timeout=30,
        )
        return {"pushed": r.is_success, "status": r.status_code, "response": r.json()}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": False, "error": str(exc), "payload": payload}


def push_google_sheets(leads: list[Lead], access_token: str | None, spreadsheet_id: str | None) -> dict:
    values = _sheets_values(leads)
    if not (access_token and spreadsheet_id):
        return {"pushed": False, "reason": "no Google access_token/spreadsheet_id", "values": values}
    try:
        r = httpx.post(
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/A1:append",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"valueInputOption": "RAW"},
            json={"values": values}, timeout=30,
        )
        return {"pushed": r.is_success, "status": r.status_code, "response": r.json()}
    except Exception as exc:  # noqa: BLE001
        return {"pushed": False, "error": str(exc), "values": values}
