# MVP Path Map

This map groups important files by workflow so implementation slices can start
from the right source of truth and runtime paths.

## Product And Planning Sources

| Purpose | Path | Notes |
|---|---|---|
| Product source of truth | `docs/REQUIREMENTS.md` | Read for new features, user-visible behavior, domain logic, and tests. |
| MVP roadmap overview | `docs/mvp-roadmap/README.md` | How to use this roadmap. |
| Implementation slices | `docs/mvp-roadmap/slices.md` | Slice scope, DoD, verification, dependencies. |
| Progress tracker | `docs/mvp-roadmap/progress.md` | Team-maintained status file. |
| Path map | `docs/mvp-roadmap/path-map.md` | This file. |
| Slice execution guide | `docs/mvp-roadmap/slice-execution-guide.md` | Start, scope-control, prompt, and completion rules. |
| Testing strategy | `docs/mvp-roadmap/testing-strategy.md` | Unit, integration, smoke, and acceptance evidence rules. |
| Requirements acceptance | `docs/mvp-roadmap/requirements-acceptance-matrix.md` | Requirement-to-slice traceability and acceptance status. |
| Frontend readiness | `docs/mvp-roadmap/frontend-readiness.md` | Design source-of-truth and frontend implementation gate. |
| Provider strategy | `docs/mvp-roadmap/provider-strategy.md` | Adapter, fallback, and provider failure rules. |
| Worktree readiness | `docs/mvp-roadmap/worktree-readiness.md` | Dirty worktree and checkpoint rules. |

## Backend Architecture And Contracts

| Purpose | Path | Notes |
|---|---|---|
| Backend overview | `docs/backend/HLD/00-overview-and-problem.md` | Product/backend problem framing. |
| Architecture | `docs/backend/HLD/10-architecture-overview.md` | Runtime layers and component responsibilities. |
| Ingestion | `docs/backend/HLD/20-ingestion-and-normalization.md` | Upload, parse, normalization, embeddings. |
| Data/storage | `docs/backend/HLD/30-data-and-storage.md` | Entity invariants and storage ownership. |
| Matching/search | `docs/backend/HLD/40-matching-and-search-pipeline.md` | Eligibility, hard filters, scoring, reasoning. |
| API/runtime flows | `docs/backend/HLD/50-api-and-runtime-flows.md` | Production namespaces and user flows. |
| Security/audit | `docs/backend/HLD/60-security-notifications-audit.md` | Auth, authorization, notifications, audit. |
| Database LLD | `docs/backend/LLD/30-database-schema.md` | Target schema documentation. |
| API contract LLD | `docs/backend/LLD/40-api-contract.md` | Target endpoint-level contract. |
| Current API matrix | `docs/backend/LLD/50-current-api-implementation-matrix.md` | Current runtime vs target contract gap map. |

## Runtime Entry Points

| Purpose | Path | Notes |
|---|---|---|
| Compatibility entrypoint | `backend/main.py` | Wrapper for app import compatibility. |
| FastAPI app entrypoint | `backend/src/jobconnect/main.py` | Main app import path. |
| App assembly | `backend/src/jobconnect/app.py` | Router registration, tags, API prefix. |
| Monolithic API router | `backend/src/jobconnect/modules/api/router.py` | Current business route implementation. |
| Health/system router | `backend/src/jobconnect/modules/system/router.py` | Runtime probes. |
| Database connection | `backend/src/jobconnect/core/database.py` | PostgreSQL connection helper. |
| Settings/security helpers | `backend/src/jobconnect/core/` | Core runtime infrastructure. |
| Shared dependencies/utilities | `backend/src/jobconnect/common/` | Common API utilities and constants. |

## Database And Migrations

| Purpose | Path | Notes |
|---|---|---|
| Production MVP migration | `backend/db/migrations/001_production_mvp.sql` | Executable current schema. |
| Migration runner | `backend/db/apply_migrations.py` | Applies SQL migrations. |
| Docker Compose runtime | `docker-compose.yml` | PostgreSQL and backend services. |
| Backend container | `backend/Dockerfile.dev` | Backend dev image. |

## Feature Ownership Paths

| Workflow | Current path | Notes |
|---|---|---|
| Auth | `backend/src/jobconnect/modules/auth/` | Ownership target; current handlers are in API router. |
| Users/profiles | `backend/src/jobconnect/modules/users/` | Ownership target; current handlers are in API router. |
| Organizations | `backend/src/jobconnect/modules/organizations/` | Ownership target; current handlers are in API router. |
| Documents | `backend/src/jobconnect/modules/documents/` | Ownership target for upload and parse jobs. |
| Resumes | `backend/src/jobconnect/modules/resumes/` | Ownership target for candidate resume lifecycle. |
| Jobs | `backend/src/jobconnect/modules/jobs/` | Ownership target for job post lifecycle. |
| Matching | `backend/src/jobconnect/modules/matching/` | Active matching helpers and future matching ownership. |
| Applications | `backend/src/jobconnect/modules/applications/` | Ownership target for application lifecycle. |
| Invites | `backend/src/jobconnect/modules/invites/` | Ownership target for recruiter invites. |
| Notifications | `backend/src/jobconnect/modules/notifications/` | Ownership target for in-app/email notification behavior. |
| Admin | `backend/src/jobconnect/modules/admin/` | Ownership target for read-only monitoring. |
| Integrations | `backend/src/jobconnect/integrations/` | Provider boundaries for pgvector, storage, parser, embedding, email. |

## Matching-Specific Paths

| Purpose | Path | Notes |
|---|---|---|
| Matching models | `backend/src/jobconnect/modules/matching/models.py` | Internal matching data structures. |
| Hard filters | `backend/src/jobconnect/modules/matching/filters.py` | Job type, location, seniority, education, certification rules. |
| Scoring | `backend/src/jobconnect/modules/matching/scoring.py` | Deterministic score formula helpers. |
| Reasoning | `backend/src/jobconnect/modules/matching/reasoning.py` | Grounded reasoning helpers. |
| Local embedding | `backend/src/jobconnect/modules/matching/embedding.py` | Current deterministic hash embedding. |
| Vector search | `backend/src/jobconnect/modules/matching/vector_search.py` | Vector-search helper boundary. |
| pgvector utility | `backend/src/jobconnect/integrations/pgvector/vector.py` | Postgres vector literal helper. |
| Legacy scenarios | `docs/scenario-matrix.md` | Archived deterministic matching reference. |
| Legacy test cases | `docs/matching-v2-scenario-test-cases.md` | Archived reference for matching behavior. |

## Tests And Verification

| Purpose | Path | Notes |
|---|---|---|
| App surface tests | `backend/tests/test_app_surface.py` | OpenAPI surface and matching contract fields. |
| Matching helper tests | `backend/tests/test_matching_helpers.py` | Hard filter and score formula checks. |
| Future backend tests | `backend/tests/` | Add slice-specific tests here. |

Standard backend verification commands:

```bash
docker compose up -d postgres backend
docker compose exec backend python db/apply_migrations.py
docker compose exec backend python -m unittest discover -s tests
curl http://localhost:8000/api/health
curl http://localhost:8000/openapi.json
```

## Frontend Planning And Future Runtime

| Purpose | Path | Notes |
|---|---|---|
| Archived frontend notes | `docs/frontend/` | Reference only; not source of truth. |
| Archived screen specs | `docs/frontend/screen-specifications.md` | Useful for intent, not direct implementation. |
| Archived user flows | `docs/frontend/user-flows.md` | Useful for flow thinking, not final IA. |
| Future frontend runtime | `frontend/` | Expected root to create later. Currently not active. |

Frontend implementation should be driven by:

- `docs/REQUIREMENTS.md`
- `docs/backend/LLD/40-api-contract.md`
- current OpenAPI output
- the frontend design direction slice

## Slice-To-Path Quick Map

| Slice | Primary paths |
|---|---|
| 0 Baseline Contract Audit | `docs/backend/LLD/50-current-api-implementation-matrix.md`, `backend/src/jobconnect/modules/api/router.py`, `backend/db/migrations/001_production_mvp.sql` |
| 1 Auth, Session, `/api/me` | `backend/src/jobconnect/modules/api/router.py`, `backend/src/jobconnect/core/security.py`, `backend/tests/` |
| 2 Ownership And Authorization | `backend/src/jobconnect/modules/api/router.py`, `backend/tests/`, `docs/backend/HLD/60-security-notifications-audit.md` |
| 3 API Contract Drift Cleanup | `backend/src/jobconnect/modules/api/router.py`, `docs/backend/LLD/40-api-contract.md`, `backend/tests/` |
| 4 Document Upload Foundation | `backend/src/jobconnect/modules/api/router.py`, `backend/src/jobconnect/integrations/`, `backend/tests/` |
| 5 Parse Worker V1 | `backend/src/jobconnect/modules/documents/`, `backend/src/jobconnect/modules/resumes/`, `backend/src/jobconnect/modules/jobs/` |
| 6 LLM Parser Adapter | `backend/src/jobconnect/integrations/`, `backend/src/jobconnect/modules/documents/`, `backend/tests/` |
| 7 Embedding And Semantic Search | `backend/src/jobconnect/modules/matching/`, `backend/src/jobconnect/integrations/`, `backend/tests/` |
| 8 Matching Production Hardening | `backend/src/jobconnect/modules/matching/`, `backend/src/jobconnect/modules/api/router.py`, `backend/tests/` |
| 9 Applications And Invites | `backend/src/jobconnect/modules/api/router.py`, `backend/src/jobconnect/modules/applications/`, `backend/src/jobconnect/modules/invites/` |
| 10 Notifications, Email, Audit | `backend/src/jobconnect/modules/notifications/`, `backend/src/jobconnect/integrations/`, `backend/tests/` |
| 11 Admin Monitoring | `backend/src/jobconnect/modules/admin/`, `backend/src/jobconnect/modules/api/router.py`, `backend/tests/` |
| 12 Backend End-to-End Hardening | `backend/src/jobconnect/`, `backend/tests/`, `docs/backend/LLD/50-current-api-implementation-matrix.md` |
| 13 Frontend Design Direction | `docs/frontend/`, `docs/mvp-roadmap/`, future `frontend/` |
| 14 Frontend Shell And API Client | future `frontend/`, `docker-compose.yml`, `README.md` |
| 15 Frontend Core Workflows | future `frontend/`, `docs/mvp-roadmap/`, current OpenAPI |
| 16 End-to-End MVP Hardening | `backend/`, future `frontend/`, `docs/`, `README.md`, `docker-compose.yml` |
