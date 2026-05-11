# Codemap (Workflow-Centric)

Purpose: workflow ownership and path mapping. Policy and process rules are canonical in `AGENTS.md`.

## Documentation Map
- Backend architecture and matching HLD index:
  - `docs/agent-rules/doc-map.md`

## 1) Platform Bootstrap and API Surface
- `backend/main.py`
  - FastAPI app creation and lifespan startup.
  - CORS configuration.
  - Router mounting under `/api`.
- Router layer (`backend/routers/*_router.py`)
  - External API contracts and request/response entrypoints.

## 2) Identity and Access Workflow
- `backend/routers/user_router.py`
- `backend/services/user_service.py`, `backend/repositories/user_repo.py`
- `backend/auth.py`

## 3) CV Ingestion Workflow (File/Text -> Structured -> Vector + Mongo)
- `backend/routers/cv_router.py`
- `backend/services/cv_service.py`, `backend/repositories/cv_repo.py`
- `backend/ragmodel/dataPreprocess/resumePreprocess.py`
- `backend/ragmodel/dataPreprocess/resumeParser.py`
- `backend/ragmodel/logics/embedder.py`
- `backend/ragmodel/db/vectorStore.py`
- `backend/models/candidateResume.py`

## 4) Job Ingestion Workflow (File/Text -> Structured -> Vector + Mongo)
- `backend/routers/job_router.py`
- `backend/services/job_service.py`, `backend/repositories/job_repo.py`
- `backend/ragmodel/dataPreprocess/jobPreprocess.py`
- `backend/ragmodel/dataPreprocess/jobParser.py`
- `backend/ragmodel/logics/embedder.py`
- `backend/ragmodel/db/vectorStore.py`
- `backend/models/jobPost.py`

## 5) Matching Workflow (Retrieve -> Rerank -> LLM Evaluate -> Persist)
Legacy/current production matching path. Do not use this workflow for Matching V2 run-only prototype unless a task explicitly asks for legacy comparison or migration work.

- `backend/routers/match_router.py`
- `backend/routers/cv_router.py` and `backend/routers/job_router.py` match endpoints
- `backend/ragmodel/logics/matchingLogic.py`
- `backend/ragmodel/logics/llmEvaluate.py`
- `backend/services/match_service.py`
- `backend/repositories/match_repo.py`
- `backend/models/matchResult.py`

## 5A) Matching V2 Prototype Workflow (Run-Only PostgreSQL + pgvector)
Use this workflow for `/api/v2/prototype/{matching,catalog}/*` and Slice 6 work.

Primary docs:
- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/20-matching-pipeline.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`

Runtime boundary:
- Prototype data lives in PostgreSQL V2 tables: `job_posts_v2`, `candidate_profiles_v2`, `job_embeddings_v2`, `candidate_embeddings_v2`.
- Vector storage/scoring uses pgvector in PostgreSQL.
- Matching returns run results directly from the V2 prototype endpoints and does not persist match results.

Expected code areas vary by slice:
- DB/schema/seed tooling: `backend/db_v2/*` and related tests.
- V2 API/runtime: V2 prototype matching router/service/runner modules if present in `backend/`.
- V2 catalog router (read-only helpers used by frontend): `backend/routers/v2_catalog_router.py` + `backend/schemas/v2_catalog_schema.py`.
- V2 search runtime helpers: `backend/v2_search/*` (`embed_query`, `vector_to_pg_literal`). Uses same hash-based 384-d embedder as the seed data, so query vectors are cosine-comparable with stored embeddings.
- OpenAPI contract checks: FastAPI generated `/openapi.json`.

Out of scope for V2 run-only prototype unless the task says otherwise:
- MongoDB business entity lifecycle.
- ChromaDB retrieval.
- Gemini/LLM evaluation.
- `match_results_v2` or persisted result query/delete APIs.
- Legacy matching route changes.

## 6) Application Tracking Workflow
- `backend/routers/application_router.py`
- `backend/services/application_service.py`
- `backend/repositories/application_repo.py`
- `backend/models/application.py`

## 7) Data Ownership Boundaries
Legacy/current production boundaries:
- MongoDB is source of truth for business entities and lifecycle status.
- ChromaDB is retrieval infrastructure and semantic index.
- AI outputs are advisory ranking signals; persisted decisions live in MongoDB match records.

Matching V2 run-only prototype exception:
- PostgreSQL is source of truth for prototype JD/CV records and embeddings.
- pgvector in PostgreSQL is the prototype vector storage/scoring layer.
- Run results are returned directly and are not persisted.

## 8) Integration Boundary For Frontend
- Frontend integrates through `/api/*` contracts.
- Contract evolution is OpenAPI-first and documented when changed.
