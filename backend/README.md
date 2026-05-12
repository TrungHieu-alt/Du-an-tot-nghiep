# Backend V2

FastAPI backend for the Matching V2 prototype.

## Active Modules

- `main.py` mounts the v2 catalog, original v2 matching, hybrid matching, and
  health routers.
- `routers/auth.py` exposes PostgreSQL-backed register/login/current-user endpoints.
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

The backend has no document ingestion, application, OAuth, advanced role guard,
or persisted match result endpoints in the current v2-only surface. Hybrid
matching is run-only and does not write match results.

No external AI API is used. The backend does not require OpenAI/Gemini API
keys, does not call remote LLM or embedding services, and keeps explanations
deterministic. MiniLM model files must be present in the local
`sentence-transformers` cache/container because runtime loading uses local
files only.
