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
- `backend/routers/match_router.py`
- `backend/routers/cv_router.py` and `backend/routers/job_router.py` match endpoints
- `backend/ragmodel/logics/matchingLogic.py`
- `backend/ragmodel/logics/llmEvaluate.py`
- `backend/services/match_service.py`
- `backend/repositories/match_repo.py`
- `backend/models/matchResult.py`

## 6) Application Tracking Workflow
- `backend/routers/application_router.py`
- `backend/services/application_service.py`
- `backend/repositories/application_repo.py`
- `backend/models/application.py`

## 7) Data Ownership Boundaries
- MongoDB is source of truth for business entities and lifecycle status.
- ChromaDB is retrieval infrastructure and semantic index.
- AI outputs are advisory ranking signals; persisted decisions live in MongoDB match records.

## 8) Integration Boundary For Frontend
- Frontend integrates through `/api/*` contracts.
- Contract evolution is OpenAPI-first and documented when changed.
