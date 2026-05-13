# Backend V2

FastAPI backend for the Matching V2 prototype.

## Active Modules

- `main.py` mounts normal Job/CV CRUD/search, the v2 catalog, original v2
  matching, hybrid matching, auth, and health routers.
- `routers/auth.py` exposes PostgreSQL-backed register/login/Google-login/current-user endpoints.
- `routers/job_router.py` exposes normal Job CRUD and public multi-industry
  search over the `jobs` table.
- `routers/cv_router.py` exposes normal CV CRUD and PDF CV upload over the
  `cvs` table.
- `routers/normal_search_router.py` keeps `/api/jobs`, `/api/cvs`, and
  `/api/candidates` compatibility aliases pointed at normal tables.
- `routers/match_v2_router.py` exposes run-only matching endpoints.
- `routers/match_hybrid_router.py` exposes additive hybrid matching endpoints.
- `routers/v2_catalog_router.py` exposes read-only browse/detail/search helpers.
- `matching_v2/` contains hard filters, scoring, deterministic reasoning, and
  PostgreSQL loaders for the original matcher plus isolated hybrid scoring
  modules.
- `v2_search/` contains local MiniLM query embedding helpers for catalog
  semantic search. It uses `sentence-transformers/all-MiniLM-L6-v2` from local
  model files only.
- `db_v2/` contains migrations, seed/reset tooling, ORM mappings for seed
  scripts, and scenario validation.

## Runtime

```bash
docker compose up -d postgres backend
```

The API is available at `http://localhost:8000`.

## Tests

```bash
docker compose exec backend python -m unittest discover -s tests
```

## Live Smoke

```bash
bash scripts/smoke_match_v2_live.sh
```

The backend has no application workflow, advanced role guard, or persisted
match result endpoints in the current prototype surface. Hybrid
matching is run-only and does not write match results. Normal search endpoints
read the normal `jobs`/`cvs` tables and do not call matching, pgvector search,
or embedding code. PDF CV upload stores file metadata only; PDF parsing is not
implemented yet.

Registration does not accept client-selected roles; new users default to
`role='user'`. Google login is available at `POST /api/auth/google` and verifies
Google ID tokens server-side with `GOOGLE_CLIENT_ID`. If that variable is empty,
Google login returns a clear configuration error while password login continues
to work.

No external AI API is used. The backend does not require OpenAI/Gemini API
keys, does not call remote LLM or embedding services, and keeps explanations
deterministic. MiniLM model files must be present in the local
`sentence-transformers` cache/container because runtime loading uses local
files only.
