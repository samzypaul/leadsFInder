# Discovery workflow

The heart of the system is a 5-step verification pipeline (`backend/app/services/workflow.py`).
It only declares a business "website-less" after exhausting every reasonable source.

## Flow diagram

```
            ┌─────────────────────────────┐
  input ──▶ │ Step 1: Instagram analysis  │
            │  extract name/bio/contacts  │
            │  + look for website link    │
            └──────────────┬──────────────┘
                  website?  │
            ┌───── yes ─────┴───── no ───────┐
            ▼                                 ▼
   ┌──────────────────┐          ┌─────────────────────────────┐
   │ Status:          │          │ Step 2: Facebook            │
   │ "Website Found"  │          │  (only if FB link present)  │
   │ store + END      │          │  read website field         │
   └──────────────────┘          └──────────────┬──────────────┘
            ▲                          website?  │
            │                    ┌──── yes ──────┴──── no ──────┐
            │                    │                              ▼
            │                    │             ┌─────────────────────────────┐
            │                    │             │ Step 3: Google Business      │
            │                    │             │  "[name] Tanzania" +         │
            │                    │             │  "[name] Google Business..." │
            │                    │             │  read website field          │
            │                    │             └──────────────┬──────────────┘
            │                    │                  website?  │
            │                    │            ┌──── yes ───────┴──── no ──────┐
            │                    │            │                               ▼
            │                    │            │            ┌─────────────────────────────┐
            │                    │            │            │ Step 4: Deep web search     │
            │                    │            │            │  "[name]" / "...Tanzania" / │
            │                    │            │            │  "...official website"      │
            │                    │            │            │  scan top 20 results        │
            │                    │            │            └──────────────┬──────────────┘
            │                    │            │                website?   │
            └────────────────────┴────────────┴───── yes ─────┘          │ no
                                                                          ▼
                                                       ┌─────────────────────────────┐
                                                       │ Step 5: Qualified Lead       │
                                                       │  enrich (AI) + score +        │
                                                       │  competitors + proposal +     │
                                                       │  outreach drafts              │
                                                       └─────────────────────────────┘
```

## What counts as an "owned website"?

`scrapers/base.is_owned_website()` rejects three buckets of hosts so they don't false-positive
as a business's own site:

1. **Social / shorteners / chat** — instagram, facebook, wa.me, linktr.ee, tiktok, t.me …
2. **Search / maps** — google.com, g.page, business.site, maps.google …
3. **Third-party directories / marketplaces** — tripadvisor, safaribookings, jiji, property24,
   booking.com, yelp …

Only a link outside all three buckets is treated as an owned website. This is why a business that
only appears on TripAdvisor or a Linktree is still correctly flagged as a **Qualified Lead**.

## Data accumulation

Across steps the workflow merges results into a single `ProfileData` (`_absorb`, first-non-empty
wins), so contact details discovered on Instagram, Facebook, and the Google Business Profile all
land on the final lead even though the website verdict short-circuits.

## Execution model

`POST /scan` enqueues a `BackgroundTask` (or runs synchronously with `?wait=true`). Background
tasks run in a worker thread with **no asyncio event loop**, which lets the scrapers use
Playwright's *sync* API and SQLAlchemy's *sync* sessions safely and simply.

## Step → source mapping

| Step | Module | Live source | Fallback |
|---|---|---|---|
| 1 Instagram | `scrapers/instagram.py` | Playwright render + og/meta + embedded JSON | fixtures, then httpx meta read |
| 2 Facebook | `scrapers/facebook.py` | Playwright render + link/meta scan | fixtures |
| 3 Google Business | `scrapers/google_business.py` | Google CSE to locate g.page/maps + Places API hook | fixtures |
| 4 Deep search | `scrapers/google_search.py` | Google Custom Search JSON API (top 20) | deep-search fixtures |
| 5 Enrichment | `services/*` | Gemini | deterministic templates |
