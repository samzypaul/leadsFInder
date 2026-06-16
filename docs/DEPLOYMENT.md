# Deployment

## Local (Docker Compose) — recommended

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend (Swagger) | http://localhost:8000/docs |
| Postgres | localhost:5432 |

The backend container seeds demo leads on first boot (`python -m app.seed --if-empty`).

## Local (no Docker)

```bash
# Terminal 1 — backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium          # only for SCRAPER_MODE=live
python -m app.seed                   # optional demo data
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE` if the backend isn't on `http://localhost:8000`.

## Environment variables

See [.env.example](../.env.example). The app runs with **none of them set** (SQLite + fallbacks).
Set these to go live:

- `DATABASE_URL` — Postgres DSN (`postgresql+psycopg://user:pass@host:5432/db`)
- `GEMINI_API_KEY` (+ `AI_PROVIDER=gemini`) — real AI content
- `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_CX` — real Steps 3 & 4
- `SCRAPER_MODE=live` — real Playwright scraping (requires `playwright install` + likely proxies)

## Production on AWS

A pragmatic, low-ops topology:

```
                       ┌──────────── Route 53 ────────────┐
                       ▼                                   ▼
              CloudFront + S3                       ALB (HTTPS, ACM cert)
            (Next.js static/SSR via                       │
             Amplify or `next start`)                     ▼
                                              ┌────────────────────────┐
                                              │  ECS Fargate service    │
                                              │  backend (uvicorn)      │
                                              │  + Playwright image     │
                                              └───────────┬────────────┘
                                                          ▼
                                                 RDS PostgreSQL (Multi-AZ)
                                                          │
                                        Secrets Manager (API keys, DB creds)
```

Recommended setup:

1. **Backend** → build `backend/Dockerfile`, push to ECR, run on **ECS Fargate** (1–2 tasks).
   The image is based on the official Playwright image so `live` scraping works out of the box.
   Put it behind an **ALB** with an ACM TLS cert. Inject secrets from **Secrets Manager**.
2. **Database** → **RDS PostgreSQL** (Multi-AZ for prod). Set `DATABASE_URL` from Secrets Manager.
   Run migrations on deploy (add Alembic; currently `init_db()` creates tables on startup).
3. **Frontend** → **AWS Amplify Hosting** (simplest for Next.js) or a second Fargate service using
   `frontend/Dockerfile` (standalone output). Set `NEXT_PUBLIC_API_BASE` to the ALB URL.
4. **Async scans at scale** → move the background workflow off the request thread onto **SQS +
   a worker service** (or Celery/Arq). The workflow is already a pure function of a `ScanJob`, so
   wrapping it in a queue consumer is mechanical.
5. **Scheduling / bulk discovery** → an EventBridge rule can POST batches of profiles to `/scan`.

### Scaling notes

- Live scraping is the bottleneck and the compliance-sensitive part: run it with residential
  proxies, low concurrency, and per-host rate limits (`SCRAPER_MIN_DELAY`). Prefer official APIs
  (Google Places, Meta Graph) where available.
- The DB is light; a single small RDS instance handles tens of thousands of leads.
- AI calls are the main cost driver — `ai_generated=false` rows used the free template fallback.

## Health & observability

- `GET /health` returns provider/mode flags for readiness probes.
- Backend logs to stdout (structured-ish) — ship to CloudWatch.
- Add request tracing / metrics (e.g. OpenTelemetry) before heavy production use.

## CI/CD (suggested)

1. `pytest` in `backend/` (already green).
2. `npm run build` in `frontend/`.
3. Build & push both images to ECR; `aws ecs update-service --force-new-deployment`.
