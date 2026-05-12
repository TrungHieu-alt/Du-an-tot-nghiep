# Backend V2

FastAPI backend for the Matching V2 prototype.

## Active Modules

- `main.py` mounts the v2 catalog, v2 matching, and health routers.
- `routers/match_v2_router.py` exposes run-only matching endpoints.
- `routers/v2_catalog_router.py` exposes read-only browse/detail/search helpers.
- `matching_v2/` contains hard filters, scoring, deterministic reasoning, and
  PostgreSQL loaders.
- `v2_search/` contains deterministic query embedding helpers for catalog
  semantic search.
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

The backend has no document ingestion, account, application, or persisted match
result endpoints in the current v2-only surface.
