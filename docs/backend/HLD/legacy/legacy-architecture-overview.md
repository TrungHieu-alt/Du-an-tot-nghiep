# Backend HLD V2: Architecture Overview

> Legacy prototype HLD. This file documents the current V2 run-only prototype
> component shape. Use
> `docs/backend/HLD/10-architecture-overview.md` for target MVP work.

## Runtime Layers

- Router layer: FastAPI contracts and request validation.
- Matching layer: hard filters, scoring, deterministic reasoning, and response
  assembly in `backend/matching_v2/`.
- Data access layer: direct PostgreSQL reads through `psycopg`.
- Seed/tooling layer: SQL/SQLAlchemy scripts under `backend/db_v2/`.

## Main Runtime Components

```text
backend/main.py
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
| `backend/main.py` | App creation, CORS, v2 router mounting |
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
- The backend exposes no non-v2 business lifecycle endpoints in the current
  repository state.

## Related Docs

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/legacy/legacy-matching-pipeline.md`
- `docs/backend/HLD/legacy/legacy-data-and-storage.md`
- `docs/backend/HLD/legacy/legacy-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`
