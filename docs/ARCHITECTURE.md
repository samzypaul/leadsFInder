# Architecture

## 1. System overview

LeadHunter TZ is a two-service monorepo plus a database:

```
┌───────────────────────┐        HTTPS / JSON         ┌────────────────────────────┐
│   Next.js frontend     │  ───────────────────────▶   │      FastAPI backend         │
│   (App Router, TS)     │  ◀───────────────────────   │                              │
│   - Dashboard          │                             │  Routers:                    │
│   - Scan               │                             │   /scan /leads /dashboard    │
│   - Leads + detail     │                             │   /export /outreach          │
└───────────────────────┘                             │                              │
                                                       │  Services:                   │
                                                       │   workflow · ai · scoring    │
                                                       │   enrichment · competitor    │
                                                       │   proposal · outreach        │
                                                       │   exporters                  │
                                                       │                              │
                                                       │  Scrapers (pluggable):       │
                                                       │   instagram · facebook       │
                                                       │   google_business · search   │
                                                       └──────┬───────────┬───────────┘
                                                              │           │
                                              ┌───────────────┘           └───────────────┐
                                              ▼                                            ▼
                                     external (optional)                            PostgreSQL
                                     Gemini · Google CSE                            (SQLite fallback)
                                     Playwright/httpx
```

### Design principles

- **Pluggable boundaries.** Every external dependency (scraping, AI, search, CRM) sits behind
  an interface with a deterministic fallback, so the whole pipeline runs offline with zero keys
  and you can swap in real providers per-environment via env vars.
- **Normalized scraper output.** All scrapers return a single `ProfileData` shape; the workflow
  never knows whether data came from Playwright, httpx, a fixture, or an official API.
- **Explainable scoring.** Scores are rule-based and the per-factor breakdown is persisted.
- **Provenance.** Each `ScanJob` records the ordered step trace and links to the lead it created.

## 2. Backend layout

```
backend/app/
├── main.py            # FastAPI app + router wiring + /health
├── config.py          # env-driven Settings (pydantic-settings)
├── database.py        # engine, SessionLocal, Base, init_db
├── models.py          # SQLAlchemy ORM (the DB schema)
├── schemas.py         # Pydantic request/response models (the API contract)
├── core/
│   └── compliance.py  # robots.txt, polite rate limiting, PII redaction
├── scrapers/
│   ├── base.py        # ProfileData + contact/website extraction
│   ├── fetch.py       # httpx + Playwright fetchers (robots-gated)
│   ├── fixtures.py    # offline demo data
│   ├── instagram.py   # Step 1
│   ├── facebook.py    # Step 2
│   ├── google_business.py  # Step 3
│   └── google_search.py    # Steps 3 & 4 (Google CSE)
├── services/
│   ├── workflow.py    # the 5-step orchestrator
│   ├── ai.py          # Gemini/OpenAI provider abstraction + fallback
│   ├── enrichment.py  # summary / opportunity / strategy
│   ├── competitor.py  # competitor discovery + comparison
│   ├── proposal.py    # proposal generator
│   ├── outreach.py    # multi-channel message generator
│   ├── scoring.py     # 1–100 score + priority bucket
│   └── exporters.py   # CSV/Excel + CRM push
└── api/
    ├── scan.py  leads.py  dashboard.py  outreach.py  export.py
```

## 3. Database schema

See [models.py](../backend/app/models.py). Core tables:

| Table | Purpose | Key columns |
|---|---|---|
| `leads` | central entity | business/contact fields, `status`, `score`, `priority`, JSON `opportunity_analysis` / `marketing_strategy` / `proposal` / `score_breakdown`, `raw_data` |
| `competitors` | per-lead competitors | `name`, `website_url`, `key_services`, FK `lead_id` |
| `outreach_messages` | per-lead drafts | `channel`, `subject`, `body`, FK `lead_id` |
| `scan_jobs` | workflow provenance | `input_url`, `verdict`, `final_stage`, JSON `steps`, FK `lead_id` |

```
scan_jobs ──many-to-one──▶ leads ──one-to-many──▶ competitors
                              └────one-to-many──▶ outreach_messages
```

Enums (`LeadStatus`, `Priority`, `OutreachStatus`, `ScanStage`) are stored as strings for
Postgres/SQLite portability. For production migrations, add Alembic (the models are
Alembic-ready); `init_db()` uses `create_all` for dev convenience.

## 4. API surface

All paths except `/health` and `/auth/login` require a `Authorization: Bearer <token>` header
(unless `AUTH_ENABLED=false`).

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | status + which providers are enabled (public) |
| `POST` | `/auth/login` | exchange email+password for a JWT (public) |
| `GET` | `/auth/me` | current user |
| `POST` | `/discover` | targeted/NL business discovery → candidates |
| `POST` | `/discover/scan` | discover (or take candidates) and run the workflow over them |
| `POST` | `/scan?wait=true\|false` | run the discovery workflow (sync or background) |
| `GET` | `/scan/{job_id}` | poll a background scan |
| `GET` | `/leads` | list/filter/sort (`status`, `priority`, `q`, `sort`) |
| `GET` | `/leads/{id}` | full lead with competitors + outreach |
| `PATCH` | `/leads/{id}` | update outreach status / contact fields |
| `POST` | `/leads/{id}/enrich` | re-run AI enrichment + scoring |
| `DELETE` | `/leads/{id}` | right-to-erasure delete |
| `GET` | `/leads/{id}/outreach` | list drafts |
| `POST` | `/leads/{id}/outreach/generate` | (re)generate drafts for channels |
| `GET` | `/dashboard/stats` | pipeline + quality aggregates |
| `GET` | `/export/csv`, `/export/excel` | tabular downloads |
| `POST` | `/export/{provider}` | push to hubspot/salesforce/airtable/google_sheets |

Interactive docs: `http://localhost:8000/docs`.

## 5. AI workflow

```
Qualified lead
     │
     ├─▶ enrichment.business_summary()      ──┐
     ├─▶ enrichment.opportunity_analysis()    │  Gemini (json/text)  ──fail/no-key──▶ template fallback
     ├─▶ enrichment.marketing_strategy()      │
     ├─▶ competitor.find_competitors()       ─┤  Google CSE / fixtures
     ├─▶ competitor.comparison_text()         │
     ├─▶ proposal.build_proposal()           ─┘
     ├─▶ scoring.score_lead()                    (deterministic rules)
     └─▶ outreach.generate_all()                 (5 channels)
```

`services/ai.py` exposes `generate_text(prompt, fallback)` and `generate_json(prompt, fallback)`.
Each higher-level call supplies a fallback closure, so **the same code path produces output with
or without an API key** — the only difference is quality and the `ai_generated` flag.

## 6. Compliance

The system is built to store **only publicly available business information**.

- **robots.txt** — `core/compliance.can_fetch()` consults a cached `RobotFileParser` per host for
  every generic web fetch (`RESPECT_ROBOTS=true`). Note that the IG/FB scrapers are intended for
  `SCRAPER_MODE=live` only where you have permission/official access; the default `fallback` mode
  never hits those platforms.
- **Rate limiting** — `polite_wait()` enforces `SCRAPER_MIN_DELAY` per host.
- **Data minimization** — only the business fields in `models.Lead` are persisted; the
  `redact_personal_data()` helper strips national-ID-like patterns.
- **Right to erasure** — `DELETE /leads/{id}` hard-deletes a lead and its children (GDPR Art. 17 /
  Tanzania Data Protection Act, 2022).
- **Provenance** — `scan_jobs.steps` records exactly what was checked and found.

> Scraping Instagram/Facebook may breach their Terms of Service. Operate `live` mode only with a
> lawful basis (official API access, owned pages, or explicit permission).
