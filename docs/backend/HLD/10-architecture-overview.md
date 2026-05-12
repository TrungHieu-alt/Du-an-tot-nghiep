# Backend HLD V2: Architecture Overview

## Runtime Layers

- Router layer: FastAPI contracts and request validation.
- Matching layer: hard filters, scoring, deterministic reasoning, and response
  assembly in `backend/matching_v2/`.
- Data access layer: direct PostgreSQL reads through `psycopg`.
- Seed/tooling layer: SQL/SQLAlchemy scripts under `backend/db_v2/`.

## Main Runtime Components

```text
backend/main.py
  ├─ routers/auth.py
  ├─ routers/v2_catalog_router.py
  ├─ routers/match_v2_router.py
  └─ routers/system_router.py

routers/match_v2_router.py
  └─ matching_v2/runner.py
       ├─ matching_v2/db.py
       ├─ matching_v2/filters.py
       ├─ matching_v2/scoring.py
       └─ matching_v2/reasoning.py

routers/v2_catalog_router.py
  ├─ matching_v2/db.py
  └─ v2_search/*
```

## Component Responsibilities

| Component | Responsibility |
|---|---|
| `backend/main.py` | App creation, CORS, auth and v2 router mounting |
| `routers/auth.py` | PostgreSQL-backed register/login/current-user contract |
| `routers/match_v2_router.py` | Matching request/response contract |
| `routers/v2_catalog_router.py` | Read-only browse/detail/search contract |
| `matching_v2/db.py` | PostgreSQL loaders for v2 records and embeddings |
| `matching_v2/filters.py` | Hard-filter rules |
| `matching_v2/scoring.py` | Component and final score formulas |
| `matching_v2/reasoning.py` | Rule-based reasoning strings |
| `v2_search/` | Deterministic query embedding and pgvector literal helpers |
| `db_v2/` | Migrations, seed/reset scripts, scenario validation |

## Boundaries

- PostgreSQL is the runtime source of truth for v2 prototype JD/CV records and
  embeddings.
- Matching and catalog endpoints are read-only except for seed/reset tooling run
  outside request handling.
- Matching results are returned directly and are not persisted.
- Auth is an additive app surface and does not guard Matching V2 endpoints yet.

## Related Docs

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/20-matching-pipeline.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`
