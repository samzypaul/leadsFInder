# Production-readiness implementation plan

This repo is a complete, runnable MVP. The plan below takes it to production. Items are ordered
by leverage; each notes the files involved.

## Phase 0 — what's already done ✅

- 5-step discovery workflow with merge/short-circuit logic (`services/workflow.py`)
- Pluggable scrapers with live + fallback paths (`scrapers/*`)
- AI abstraction (Gemini/OpenAI) with deterministic fallback (`services/ai.py`)
- Scoring, enrichment, competitor analysis, proposal, multi-channel outreach
- REST API + Next.js dashboard (scan, leads, lead detail)
- CSV/Excel export + HubSpot/Salesforce/Airtable/Google Sheets push
- Compliance: robots.txt, rate limiting, erasure endpoint, PII redaction
- Docker Compose, Dockerfiles, passing backend tests

## Phase 1 — data layer hardening

| Task | Files | Notes |
|---|---|---|
| Add Alembic migrations | `backend/alembic/` | replace `init_db()` `create_all` in prod |
| Unique constraints / dedup | `models.py` | de-dupe leads by (business_name, city) or IG handle |
| Indexable JSON → columns | `models.py` | promote frequently-filtered JSON keys if needed |
| Connection pooling tuning | `database.py` | set `pool_size`/`max_overflow` for RDS |

## Phase 2 — real data acquisition (compliance-critical)

| Task | Files | Notes |
|---|---|---|
| Google **Places API** for Step 3 | `scrapers/google_business.py` (`_from_places_api` hook) | reliable GBP data: phone, hours, reviews, website |
| Meta **Graph API** for Step 2 | `scrapers/facebook.py` | official, ToS-safe page data |
| Instagram strategy | `scrapers/instagram.py` | use IG Graph API for owned/whitelisted accounts; for discovery use a licensed data provider or manual import — avoid ToS-violating scraping |
| Proxy + session pool | `scrapers/fetch.py` | residential proxies, rotating UA, backoff |
| Selector resilience tests | `tests/` | golden-HTML fixtures to detect layout drift |

## Phase 3 — scale & async

| Task | Files | Notes |
|---|---|---|
| Move workflow to a queue | new `worker/` + SQS/Arq/Celery | `run_workflow(job)` is already queue-ready |
| Batch/bulk scan endpoint | `api/scan.py` | accept a list, fan out to the queue |
| Caching of search/AI results | `services/ai.py`, `google_search.py` | cut cost; cache by prompt/query hash |
| Rate-limit & quota guards | `core/compliance.py` | per-provider budgets |

## Phase 4 — product depth

| Task | Files | Notes |
|---|---|---|
| Auth + multi-tenant | backend + frontend | per-user lead ownership, RBAC |
| Email/WhatsApp sending | `services/outreach.py` | integrate SES / WhatsApp Business API; track replies |
| Proposal → PDF | new exporter | render `proposal` JSON to branded PDF |
| Activity log / notes | `models.py` | timeline per lead |
| Saved searches / scheduling | EventBridge + `api/scan.py` | recurring discovery |

## Phase 5 — quality, security, ops

| Task | Notes |
|---|---|
| Frontend tests (Playwright/RTL) | smoke the three pages |
| Backend coverage to ~80% | scrapers' HTML parsers, exporters, API routes |
| Secrets via Secrets Manager / Vault | never bake keys into images |
| Observability | OpenTelemetry traces, CloudWatch dashboards, Sentry |
| Rate limiting / WAF on the API | abuse protection |
| Data Protection Impact Assessment | document lawful basis; honour erasure/SAR requests |
| Pen test + dependency scanning | `pip-audit`, `npm audit`, Dependabot |

## Risk register

| Risk | Mitigation |
|---|---|
| IG/FB scraping breaches ToS / gets blocked | prefer official APIs; licensed data; `fallback` default; proxies for permitted use |
| AI hallucination in proposals/outreach | human-in-the-loop review before sending; `ai_generated` flag surfaced in UI |
| Selector drift breaks live scrapers | golden-HTML tests + alerting; graceful fallback already in place |
| Cost blow-up from AI/search | caching, budgets, template fallback |
| Privacy non-compliance | data minimization, erasure endpoint, provenance, DPIA |
