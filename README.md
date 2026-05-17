# JobConnect MVP

A shared-pool recruiting marketplace. Candidates upload CVs, match against jobs, apply, and respond to invites. Recruiters create jobs, match against resumes, invite candidates, and manage applications. Admins monitor users, documents, and audit events.

Canonical product requirements: `docs/REQUIREMENTS.md`  
Backend architecture: `docs/backend/HLD/`  
MVP roadmap: `docs/mvp-roadmap/README.md`

## Quick Start

**Requirements:** Docker + Docker Compose.

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Apply database migrations (first time, or after reset)
docker compose exec backend python db/apply_migrations.py

# 4. (Optional) Install SQLAlchemy seed tooling dependency once per running container
docker compose exec backend pip install -r db/seeds/requirements-seed.txt

# 5. Seed demo data (ORM SQLAlchemy, separate from migrations)
docker compose exec backend python -m db.seeds.cli seed --profile demo
```

Services:

| Service  | URL                       |
|----------|---------------------------|
| Frontend | http://localhost:5173     |
| Backend  | http://localhost:8000     |
| Postgres | localhost:5433            |

## First-Time Setup Flow

1. Open http://localhost:5173
2. Register as **candidate** or **recruiter** (or **admin**).
3. Complete profile setup — candidates set name/headline/location, recruiters select/create an organization.
4. Candidates: activate a resume to apply to jobs or receive invites.
5. Recruiters: publish a job to appear in the talent market and accept applications.

## Verification

Backend tests (204 tests):

```bash
docker compose exec backend python -m unittest discover -s tests
```

Backend smoke (22-step live flow):

```bash
docker compose exec backend python tests/smoke_e2e.py
```

API health + OpenAPI:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/openapi.json
```

Seed tooling checks:

```bash
# idempotent run (execute twice, should not duplicate seed rows)
docker compose exec backend python -m db.seeds.cli seed --profile demo
docker compose exec backend python -m db.seeds.cli seed --profile demo

# scoped reset and reseed for jobs + related records
docker compose exec backend python -m db.seeds.cli reset --target jobs --with-related
docker compose exec backend python -m db.seeds.cli reseed --target jobs --profile demo --with-related
```

Frontend TypeScript check:

```bash
docker compose exec frontend node_modules/.bin/tsc --noEmit
```

## Project Layout

```
backend/
  src/jobconnect/
    core/           # config, database, security, logging
    common/         # dependencies, pagination, responses
    integrations/   # pgvector, llm, embedding, storage, email, rerank
    modules/        # auth, users, orgs, jobs, resumes, documents,
                    # matching, applications, invites, notifications,
                    # admin, system
  db/migrations/    # 001_production_mvp.sql
  tests/            # 204 unit + integration tests + smoke_e2e.py

frontend/
  src/
    contexts/       # AuthContext (JWT session)
    components/     # ProtectedRoute, AppShell, UI primitives
    pages/          # candidate/, recruiter/, admin/, shared
    lib/            # api.ts, hooks.ts, constants.ts, cn.ts
```

## Known Gaps (MVP Scope)

| Gap | Status | Notes |
|-----|--------|-------|
| `sentence_transformers` not installed → rerank falls back with a warning | Open | Matching still works via score sort. Install via `pip install -r requirements.txt` to enable. |
| Semantic search UI | **Closed** (post-MVP fix) | Job/Talent market pages now expose a "Thông minh (AI)" mode using `POST /api/jobs/semantic-search` & `POST /api/candidate/resumes/semantic-search`. |
| Pagination UI | **Closed** (post-MVP fix) | Reusable `<Pagination>` component wired into Job Market, Talent Market, and Admin pages (20/page). |
| DOCX parsing | **Closed** (post-MVP fix) | `python-docx` extracts paragraphs + tables. Invalid DOCX returns empty (worker marks `empty_extraction`). |
| Admin disable-user action in UI | **Closed** (post-MVP fix) | `PATCH /api/admin/users/{id}` + admin-page button (with self-disable guard). |
| Local filesystem storage for uploads | Open | Not suitable for multi-instance or production. Storage adapter boundary already exists; add S3/MinIO impl. |
| No real email delivery | Open | `EMAIL_PROVIDER=local` (default) logs only. Set `EMAIL_PROVIDER=smtp`, `SMTP_HOST`, `EMAIL_FROM` to enable SMTP. |

## Environment Variables

Key vars (all have defaults — only set to override):

```bash
# Database
POSTGRES_HOST=localhost       # use "postgres" inside Docker
POSTGRES_PORT=5433
POSTGRES_USER=jobmatcher
POSTGRES_PASSWORD=jobmatcher
POSTGRES_DB=jobmatcher_v2

# Security
JWT_SECRET=...               # random secret for JWT signing
JWT_TTL_SECONDS=86400

# LLM (optional — falls back to local deterministic parser)
LLM_PROVIDER=local           # or "openai"
OPENAI_API_KEY=...

# Embedding (optional — falls back to local hash embedding)
EMBEDDING_PROVIDER=local     # or "openai"

# Storage
STORAGE_BACKEND=local        # local filesystem under /app/backend/uploads
STORAGE_LOCAL_ROOT=/app/backend/uploads

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

## Documentation

- Product spec: `docs/REQUIREMENTS.md`
- Backend HLD: `docs/backend/HLD/`
- API contract: `docs/backend/LLD/40-api-contract.md`
- API implementation matrix: `docs/backend/LLD/50-current-api-implementation-matrix.md`
- MVP slices: `docs/mvp-roadmap/slices.md`
- MVP progress: `docs/mvp-roadmap/progress.md`
