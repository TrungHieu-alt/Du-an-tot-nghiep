# JobConnect Matching V2

This repository contains the v2-only Matching prototype: a FastAPI backend,
PostgreSQL + pgvector storage, and a React/Vite frontend for catalog search and
run-only matching, plus an additive PostgreSQL/JWT authentication surface.

## Active Product Scope

- Browse and search seeded v2 job and CV records.
- Open job/CV detail pages from the v2 catalog.
- Run synchronous JD -> CV or CV -> JD matching from an existing integer ID.
- Return top matches with score breakdown, deterministic reasoning, and runtime
  metrics.
- Register, login, and load the current user through `/api/auth/*`.
- Show the JobConnect landing homepage at `/`.

Out of scope for the current repository state: document upload, parsing,
application tracking, OAuth, advanced role authorization, LLM scoring,
vector-store sidecars, and persisted match results.

## Runtime Architecture

- **Backend**: FastAPI (`backend/main.py`).
- **Database**: PostgreSQL with pgvector, exposed on host port `5433`.
- **Tables**: `job_posts_v2`, `candidate_profiles_v2`,
  `job_embeddings_v2`, `candidate_embeddings_v2`, plus `users` for auth.
- **Matching**: hard filters + exhaustive pgvector-compatible scoring +
  deterministic rerank.
- **Frontend**: React + Vite. User-facing routes are `/`, `/login`,
  `/register`, `/v2/search`, `/v2/jobs/:id`, `/v2/cvs/:id`, and `/v2/matching`.

`/` renders the JobConnect homepage.

## API Surface

Matching:

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

Catalog:

- `GET /api/v2/prototype/catalog/jobs`
- `GET /api/v2/prototype/catalog/jobs/{job_id}`
- `POST /api/v2/prototype/catalog/jobs/search`
- `GET /api/v2/prototype/catalog/cvs`
- `GET /api/v2/prototype/catalog/cvs/{cv_id}`
- `POST /api/v2/prototype/catalog/cvs/search`

System:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/health`
- `GET /openapi.json`

## Setup

Create `.env` from the example:

```bash
cp .env.example .env
```

Start the app with Docker Compose:

```bash
docker compose up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL: `localhost:5433`

## Seed Data

PostgreSQL starts empty unless a persisted Docker volume already contains data.
Seed the v2 dataset from the backend container:

```bash
docker compose up -d postgres backend
docker compose exec backend python db_v2/reset.py
```

Auth data is not seeded. The same migration pass creates an empty `users` table;
register through the frontend or `POST /api/auth/register`.

For the compact scenario profile:

```bash
docker compose exec backend python db_v2/reset.py --profile scenario
docker compose exec backend python db_v2/validate_scenario_dataset.py --db
```

## Verification

Backend unit tests:

```bash
docker compose exec backend python -m unittest discover -s tests
```

Frontend tests:

```bash
docker compose run --rm frontend npm run test:run
```

Frontend build:

```bash
docker compose run --rm frontend npm run build
```

Live v2 smoke:

```bash
bash scripts/smoke_match_v2_live.sh
```

Auth smoke after starting the stack:

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345678","full_name":"Nguyen Van A","role":"candidate"}'

curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345678"}'
```

## Documentation

- Product spec: `docs/REQUIREMENTS.md`
- V2 database notes: `backend/db_v2/README.md`
- Frontend v2 notes: `frontend/README.md`
- API examples: `frontend/apiExamples.md`
