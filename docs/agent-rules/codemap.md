# Codemap (Workflow-Centric)

Purpose: workflow ownership and path mapping. Policy and process rules are
canonical in `AGENTS.md`.

## Documentation Map

- Backend architecture and matching HLD index:
  - `docs/agent-rules/doc-map.md`

## 1) Platform Bootstrap and API Surface

- `backend/main.py`
  - FastAPI app creation.
  - CORS configuration.
  - Auth, system, catalog, and matching router mounting under `/api`.
- Router layer:
  - `backend/routers/auth.py`
  - `backend/routers/match_v2_router.py`
  - `backend/routers/v2_catalog_router.py`
  - `backend/routers/system_router.py`

## 1A) Authentication Workflow

Use this workflow for `/api/auth/*`.

Runtime boundary:

- PostgreSQL `users` table is the source of truth for auth accounts.
- Passwords are stored only as hashes.
- JWT access tokens identify the current user.
- Role values are stored for later authorization but current Matching V2 routes
  are not role-guarded.

Expected code areas:

- `backend/routers/auth.py`
- `backend/db_v2/migrations/*auth*.sql`
- `frontend/src/services/authApi.ts`
- `frontend/contexts/AuthContext.tsx`
- `frontend/pages/Login.tsx`
- `frontend/pages/Register.tsx`

## 2) Matching V2 Prototype Workflow (Run-Only PostgreSQL + pgvector)

Use this workflow for `/api/v2/prototype/matching/*` and the additive
`/api/v2/prototype/matching-hybrid/*` surface.

Primary docs:

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/20-matching-pipeline.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`

Runtime boundary:

- Prototype data lives in PostgreSQL V2 tables: `job_posts_v2`,
  `candidate_profiles_v2`, `job_embeddings_v2`, `candidate_embeddings_v2`.
- Vector storage/scoring uses pgvector in PostgreSQL.
- Runtime embedding uses local `sentence-transformers/all-MiniLM-L6-v2` only;
  no external AI/embedding API clients or API keys are part of the backend.
- Matching returns run results directly from the V2 prototype endpoints and
  does not persist match results.
- The original `/matching/*` contract remains on the `0..1` score scale. The
  parallel `/matching-hybrid/*` contract returns `0..100` scores with skipped
  groups, failed filters, warnings, and explanations.

Expected code areas:

- DB/schema/seed tooling: `backend/db_v2/*` and related tests.
- V2 matching runtime: `backend/matching_v2/*`.
- V2 matching router/schema: `backend/routers/match_v2_router.py`,
  `backend/schemas/match_v2_schema.py`.
- Hybrid matching router/schema: `backend/routers/match_hybrid_router.py`,
  `backend/schemas/match_hybrid_schema.py`.
- OpenAPI contract checks: FastAPI generated `/openapi.json`.

Out of scope for V2 run-only prototype unless the task says otherwise:

- Document ingestion, parsing, or upload flows.
- Runtime LLM scoring/reasoning or remote embedding/LLM API calls.
- `match_results_v2` or persisted result query/delete APIs.
- Auth/role guard changes.

## 3) V2 Catalog and Search Workflow

Use this workflow for `/api/v2/prototype/catalog/*` and frontend browse/search.

Runtime boundary:

- Read-only helpers over the same four V2 PostgreSQL tables.
- Search uses local MiniLM query embeddings from `backend/v2_search/*`.
- Search score is catalog relevance only and is not the matching final score.

Expected code areas:

- `backend/routers/v2_catalog_router.py`
- `backend/schemas/v2_catalog_schema.py`
- `backend/v2_search/*`
- `frontend/src/api/v2.ts`
- `frontend/lib/api-routes.ts`
- `frontend/pages/V2Search.tsx`
- `frontend/pages/V2JobDetail.tsx`
- `frontend/pages/V2CvDetail.tsx`
- `frontend/components/v2/*`

## 4) Frontend V2 Routing Workflow

- `frontend/App.tsx`
  - `/` redirects to `/v2/search`.
  - Active user-facing routes:
    - `/v2/search`
    - `/v2/jobs/:id`
    - `/v2/cvs/:id`
    - `/v2/matching`
- `frontend/components/Header.tsx` and `frontend/components/Footer.tsx`
  - Navigation must point only to V2 user-facing routes.

## 5) Data Ownership Boundaries

- PostgreSQL is source of truth for prototype JD/CV records and embeddings.
- pgvector in PostgreSQL is the prototype vector storage/scoring layer.
- Run results are returned directly and are not persisted.

## 6) Integration Boundary For Frontend

- Frontend integrates through `/api/v2/prototype/*` contracts.
- Contract evolution is OpenAPI-first and documented when changed.
