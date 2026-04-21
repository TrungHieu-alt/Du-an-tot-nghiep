# LLD: App Bootstrap and Router Map

## Source Anchors
- `backend/main.py`
- `backend/db.py`
- `backend/routers/*.py`

## Runtime Bootstrap Flow
1. FastAPI app is created with title/version and lifespan handler.
2. Lifespan startup executes `init_db()` from `backend/db.py`.
3. `init_db()` initializes Beanie with all document models:
   - `User`, `CandidateProfile`, `RecruiterProfile`, `JobPost`, `CandidateResume`, `MatchResult`, `Application`.
4. API routers are mounted with common prefix `/api`.
5. Root endpoint `/` remains outside `/api` and returns service greeting.

## CORS Contract
Configured in `main.py` via `CORSMiddleware`:
- Allowed origins:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- `allow_credentials=True`
- `allow_methods=["*"]`
- `allow_headers=["*"]`

Operational implication:
- Frontend local dev is allowed.
- Production origins are not yet configurable via env in current implementation.

## Mounted Router Inventory
All below are mounted under `/api`:
- `user_router` -> `/users`
- `candidate_router` -> `/candidate`
- `recruiter_router` -> `/recruiter`
- `job_router` -> `/jobs`
- `cv_router` -> `/cv`
- `application_router` -> `/applications`
- `match_router` -> `/matching`
- `system_router` -> no local prefix, exposes `/health`

## Endpoint Count by Router
- users: 5
- candidate: 4
- recruiter: 3
- jobs: 10
- cv: 10
- applications: 5
- matching: 6
- system: 1

## Layer Invocation Pattern
For most flows, call chain is:
- Router -> Service -> Repository -> Model or RAG modules

Exceptions:
- Some matching retrieval endpoints in `cv_router` and `job_router` call service methods that delegate directly to repository static methods and RAG logic.

## Startup/Shutdown Observability
`main.py` emits simple print logs:
- startup success: `Database initialized`
- shutdown success: `Shutdown complete`

No structured logging or health probes are triggered during startup itself.

## Non-goals in Current Runtime
- No dependency injection container.
- No per-request auth guard dependencies on routes.
- No centralized exception middleware.

## Related LLD
- Error and response behavior: `runtime/router-contract-and-error-patterns.md`
- API matrix: `api/backend-endpoint-schema-matrix.md`
- Data initialization details: `data/mongodb-model-id-and-index-contracts.md`
