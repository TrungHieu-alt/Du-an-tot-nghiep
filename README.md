# JobConnect Matching V2

This repository contains the v2-only Matching prototype: a FastAPI backend,
PostgreSQL + pgvector storage, and a React/Vite frontend for catalog search and
run-only matching, plus an additive PostgreSQL/JWT authentication surface.

## Active Product Scope

- Browse and search seeded v2 job and CV records with local MiniLM query
  embeddings.
- Open job/CV detail pages from the v2 catalog.
- Run synchronous JD -> CV or CV -> JD matching from an existing integer ID.
- Return top matches with score breakdown, deterministic reasoning, and runtime
  metrics.
- Run the additive hybrid matcher for explainable 0..100 scoring without
  changing the original V2 matcher contract.
- Register, login, Google login, and load the current user through `/api/auth/*`.
- Show the JobConnect landing homepage at `/`.

Out of scope for the current repository state: application tracking, advanced
role authorization, LLM scoring, vector-store sidecars, and persisted match
results.

Embedding and AI boundary:

- Runtime embeddings use only local `sentence-transformers/all-MiniLM-L6-v2`.
- No OpenAI, Gemini, Cohere, HuggingFace Inference API, or remote LLM/embedding
  API is required.
- No OpenAI/Gemini API key is needed for matching, search, embedding, or
  reasoning.
- MiniLM model files must be available in the local `sentence-transformers`
  cache/container; runtime loading uses local files only.
- Reasoning/explanations are deterministic and rule-based.

## Runtime Architecture

- **Backend**: FastAPI (`backend/main.py`).
- **Database**: PostgreSQL with pgvector, exposed on host port `5433`.
- **Tables**: `job_posts_v2`, `candidate_profiles_v2`,
  `job_embeddings_v2`, `candidate_embeddings_v2`, plus `users` for auth.
- **Matching**: original V2 hard-filter matcher plus an additive hybrid matcher
  that reuses the same four V2 tables.
- **Embeddings**: local MiniLM (`sentence-transformers/all-MiniLM-L6-v2`),
  cached lazily in-process and stored as 384-dim pgvector-compatible lists.
- **Frontend**: React + Vite. User-facing routes are `/`, `/login`,
  `/register`, `/v2/search`, `/v2/jobs/:id`, `/v2/cvs/:id`, and `/v2/matching`.

`/` renders the JobConnect homepage.

## API Surface

Matching:

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`
- `POST /api/v2/prototype/matching-hybrid/job/{job_id}/run`
- `POST /api/v2/prototype/matching-hybrid/cv/{cv_id}/run`

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
- `POST /api/auth/google`
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
Registration no longer accepts a client-selected role; new users default to
`role='user'`. Google login requires `GOOGLE_CLIENT_ID` on the backend and
`VITE_GOOGLE_CLIENT_ID` on the frontend. Email/password login continues to work
when those Google variables are empty.

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
  -d '{"email":"user@example.com","password":"12345678","full_name":"Nguyen Van A"}'

curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345678"}'

curl -X POST "http://localhost:8000/api/auth/google" \
  -H "Content-Type: application/json" \
  -d '{"credential":"<google-id-token>"}'
```

## Documentation

- Product spec: `docs/REQUIREMENTS.md`
- V2 database notes: `backend/db_v2/README.md`
- Frontend v2 notes: `frontend/README.md`
- API examples: `frontend/apiExamples.md`
