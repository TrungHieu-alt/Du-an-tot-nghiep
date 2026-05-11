from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware   # ← thêm dòng này
from db import init_db
from routers import (
    user_router,
    candidate_router,
    recruiter_router,
    job_router,
    cv_router,
    application_router,
    match_router,
    match_v2_router,
    system_router,
    v2_catalog_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    print("✓ Database initialized")
    yield
    # Shutdown
    print("✓ Shutdown complete")


# ---------------------------------------------------------------------------
# OpenAPI metadata — kept in one place so Swagger UI groups + orders endpoints
# deterministically. Tag names below MUST match the strings used in each
# router's APIRouter(tags=[...]) declaration; if you rename a tag here, also
# update the router and any test that asserts on tag presence.
# ---------------------------------------------------------------------------

API_DESCRIPTION = """\
Backend API powering the JobConnect platform.

The surface is split into two generations that coexist intentionally:

* **V1 (production)** — MongoDB-backed business endpoints used by the live
  product: users, candidate / recruiter profiles, jobs, CVs, applications,
  and the original Gemini-based matching pipeline.
* **V2 Prototype** — Postgres + pgvector experimental surface. Run-only,
  scope-locked to 4 tables (`job_posts_v2`, `candidate_profiles_v2`, plus
  their embeddings). All identifiers are integers, all enum fields are
  strict literals. Used by the `/v2/*` frontend pages.

See `frontend/apiExamples.md` for curl examples and `AGENTS.md` for the
current surface map.
"""

OPENAPI_TAGS = [
    # ---- V1 (production) ----
    {"name": "users", "description": "V1 · Authentication and user account management (MongoDB)."},
    {"name": "candidate", "description": "V1 · Candidate profile CRUD."},
    {"name": "recruiter", "description": "V1 · Recruiter profile CRUD."},
    {"name": "jobs", "description": "V1 · Job-post lifecycle (create / list / upload / delete) plus per-job match views."},
    {"name": "cv", "description": "V1 · Candidate resume lifecycle plus per-CV match views."},
    {"name": "applications", "description": "V1 · Job applications between candidates and jobs."},
    {"name": "matching", "description": "V1 · Gemini-backed matching (sync, async, queued jobs)."},
    # ---- V2 Prototype ----
    {
        "name": "catalog-v2-prototype",
        "description": (
            "V2 Prototype · Read-only catalog over `job_posts_v2` / "
            "`candidate_profiles_v2`. Supports paginated browse, detail "
            "lookup, and pgvector-backed semantic search with optional "
            "location / job_type / seniority filters."
        ),
    },
    {
        "name": "matching-v2-prototype",
        "description": (
            "V2 Prototype · Synchronous run-only matching. No persistence, "
            "no LLM. Anchor a job_id or cv_id and receive top-K matches "
            "with score breakdown."
        ),
    },
    # ---- Cross-cutting ----
    {"name": "system", "description": "Health checks and runtime probes."},
    {"name": "root", "description": "Service root."},
]


app = FastAPI(
    title="Job Matcher API",
    description=API_DESCRIPTION,
    version="1.1.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "JobConnect Engineering",
    },
)

# ------------------------------
# 🔥 Enable CORS here
# ------------------------------
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],           
    allow_headers=["*"],           
)
# ------------------------------


# Include routers
app.include_router(user_router.router, prefix="/api")
app.include_router(candidate_router.router, prefix="/api")
app.include_router(recruiter_router.router, prefix="/api")
app.include_router(job_router.router, prefix="/api")
app.include_router(cv_router.router, prefix="/api")
app.include_router(application_router.router, prefix="/api")
app.include_router(match_router.router, prefix="/api")
app.include_router(match_v2_router.router, prefix="/api")
app.include_router(v2_catalog_router.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")



@app.get(
    "/",
    tags=["root"],
    summary="Service root",
    description=(
        "Service banner endpoint. Returns a welcome payload — use this to "
        "verify the FastAPI process is reachable. For dependency-aware "
        "liveness, prefer `GET /api/health`."
    ),
)
async def root():
    return {"message": "Welcome to Job Matcher API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
