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
  ├─ routers/match_hybrid_router.py
  └─ routers/system_router.py

routers/match_v2_router.py
  └─ matching_v2/runner.py
       ├─ matching_v2/db.py
       ├─ matching_v2/filters.py
       ├─ matching_v2/scoring.py
       └─ matching_v2/reasoning.py

routers/match_hybrid_router.py
  └─ matching_v2/hybrid_runner.py
       ├─ matching_v2/db.py
       ├─ matching_v2/hybrid_scoring.py
       ├─ matching_v2/hybrid_utils.py
       └─ matching_v2/skill_normalizer.py

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
| `routers/match_hybrid_router.py` | Additive hybrid matching contract with 0..100 explainable scores |
| `routers/v2_catalog_router.py` | Read-only browse/detail/search contract |
| `matching_v2/db.py` | PostgreSQL loaders for v2 records and embeddings |
| `matching_v2/filters.py` | Hard-filter rules |
| `matching_v2/scoring.py` | Component and final score formulas |
| `matching_v2/reasoning.py` | Rule-based reasoning strings |
| `matching_v2/hybrid_*` | Parallel hybrid matching utilities, scoring, and response assembly |
| `v2_search/` | Local MiniLM query embedding and pgvector literal helpers |
| `db_v2/` | Migrations, seed/reset scripts, scenario validation |

## Boundaries

- PostgreSQL is the runtime source of truth for v2 prototype JD/CV records and
  embeddings.
- Runtime embedding generation uses only local
  `sentence-transformers/all-MiniLM-L6-v2`; no external AI API key is required.
- Matching and catalog endpoints are read-only except for seed/reset tooling run
  outside request handling.
- Matching results are returned directly and are not persisted.
- Hybrid matching is additive under `/api/v2/prototype/matching-hybrid/*` and
  does not modify the original `/matching/*` score scale or response fields.
- Auth is an additive app surface and does not guard Matching V2 endpoints yet.

## Related Docs

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/20-matching-pipeline.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`
