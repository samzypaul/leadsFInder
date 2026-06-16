# LeadHunter TZ — Tanzania Business Lead Generation & Website Opportunity Scraper

LeadHunter TZ discovers Tanzanian businesses that have an online presence (Instagram,
Facebook, Google Business Profile) **but do not own a website**, then turns each one into a
qualified, scored sales lead complete with an AI business summary, opportunity analysis,
competitor comparison, a ready-to-send proposal, and multi-channel outreach drafts.

> **Use it for legitimate B2B lead generation on publicly available business information only.**
> See [Compliance](#compliance) before running against live platforms.

---

## What it does

### Two ways in

- **Discover** (recommended) — type a request in plain English ("tour operators in Arusha
  without a website") or set filters (category, city, min followers). AI parses it into a
  targeted search, returns matching businesses, and you scan the ones you pick into leads.
- **Single scan** — paste one Instagram profile URL (or business name) to run the workflow on it.

Access is protected by **JWT auth** — users can **self-service sign up** (`/signup`) or sign in
(`/login`); a default admin is seeded on first boot (see Configuration).

### The verification workflow

Given an Instagram profile URL (or a business name), the system runs a **5-step verification
workflow** before deciding a business has no website:

1. **Instagram analysis** — extract profile fields, look for a website link.
2. **Facebook verification** — if a FB page is linked, open it and check its website field.
3. **Google Business Profile search** — look up the business and read its website field.
4. **Deep web verification** — run targeted Google searches and scan the top 20 results.
5. **Lead creation** — if still no website, mark as a **Qualified Lead** and enrich it with AI.

Each qualified lead gets:

- AI **business summary**
- **Why they need a website** opportunity analysis
- **Marketing strategy** (Website / AI / Marketing opportunities)
- **Competitor analysis** (top competitors + gap comparison)
- **Customized proposal** (exec summary, solution, benefits, timeline, CTA)
- **Lead score (1–100)** with Hot / Warm / Medium / Low priority
- **Outreach drafts**: cold email, WhatsApp, Instagram DM, Facebook message, LinkedIn message

A dashboard summarizes the pipeline; leads export to **CSV, Excel, Google Sheets, Airtable,
HubSpot, and Salesforce**.

---

## Architecture

```
┌──────────────┐      REST/JSON      ┌──────────────────────────────────────┐
│  Next.js UI  │  ───────────────▶   │            FastAPI backend            │
│  (dashboard) │  ◀───────────────   │                                       │
└──────────────┘                     │  ┌────────────────────────────────┐  │
                                      │  │  Discovery workflow (5 steps)  │  │
                                      │  └───────────────┬────────────────┘  │
                                      │   scrapers │ ai │ scoring │ exporters │
                                      └──────┬─────┴──┬──┴────┬────┴────┬─────┘
                                             │        │       │         │
                                        Playwright  Gemini  rules   PostgreSQL
                                        /httpx      API
```

Full detail in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
[docs/WORKFLOW.md](docs/WORKFLOW.md), and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## Quick start (Docker)

```bash
cp .env.example .env          # fill in API keys (optional — runs with fallbacks)
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API + docs: http://localhost:8000/docs

The stack ships with **demo fixtures**, so you can run a full scan and see qualified leads
**without any API keys or live scraping**. Add keys in `.env` to enable real Gemini summaries,
Google search verification, and live Playwright scraping.

## Quick start (local, no Docker)

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium          # only needed for live scraping
python -m app.seed                   # optional: load demo leads
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Configuration

All settings come from environment variables (see [.env.example](.env.example)):

| Variable | Purpose | If unset |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection | falls back to local SQLite (`leadhunter.db`) |
| `GEMINI_API_KEY` | AI summaries / proposals / outreach | deterministic template fallback |
| `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_CX` | Steps 3 & 4 web verification | fixture/heuristic fallback |
| `SCRAPER_MODE` | `live` (Playwright) or `fallback` (fixtures/httpx) | `fallback` |
| `RESPECT_ROBOTS` | enforce robots.txt on web fetches | `true` |
| `AUTH_ENABLED` | require JWT login on data endpoints | `true` |
| `SECRET_KEY` | JWT signing key — **set in production** | dev placeholder |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | seeded admin login | `admin@leadhunter.tz` / `changeme` |

No key is required to run the app — every external dependency has a deterministic fallback so
the pipeline is fully demoable offline. **Natural-language search** uses Gemini when
`GEMINI_API_KEY` is set and falls back to a deterministic keyword/city parser otherwise.

> **First login:** `admin@leadhunter.tz` / `changeme` (or whatever `ADMIN_PASSWORD` you set).
> Change these before deploying.

---

## Compliance

This tool is designed for **public business information** and B2B lead generation. Note:

- Scraping Instagram/Facebook may violate their Terms of Service. `SCRAPER_MODE=live` is
  provided for environments where you have permission (e.g. official API access, owned data).
- `RESPECT_ROBOTS=true` enforces robots.txt on generic web fetches.
- The system stores **only publicly available business contact data** and is built to support
  GDPR / Tanzania Data Protection Act obligations (right to erasure via `DELETE /leads/{id}`,
  data minimization, provenance tracking). See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#compliance).

You are responsible for using this software lawfully in your jurisdiction.
```
