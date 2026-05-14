from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import (
    application_router,
    auth,
    cv_router,
    job_router,
    match_hybrid_router,
    match_v2_router,
    normal_search_router,
    system_router,
    v2_catalog_router,
)


API_DESCRIPTION = """\
Backend API for the JobConnect Matching V2 prototype.

The active prototype surface is V2 matching/catalog, with additive auth and
normal search endpoints for the JobConnect UI:

* `POST /api/v2/prototype/matching/job/{job_id}/run`
* `POST /api/v2/prototype/matching/cv/{cv_id}/run`
* `POST /api/v2/prototype/matching-hybrid/job/{job_id}/run`
* `POST /api/v2/prototype/matching-hybrid/cv/{cv_id}/run`
* `GET /api/v2/prototype/catalog/{jobs,cvs}`
* `GET /api/v2/prototype/catalog/{jobs,cvs}/{id}`
* `POST /api/v2/prototype/catalog/{jobs,cvs}/search`
* `GET /api/jobs`
* `GET /api/cvs`
* `GET /api/candidates`
* `POST /api/job`
* `POST /api/job/extract`
* `GET /api/job/my`
* `GET /api/job/search`
* `GET /api/employer/requests/my`
* `POST /api/employer/requests`
* `POST /api/cv`
* `GET /api/cv/my`
* `GET /api/cvs/my`
* `POST /api/cv/upload`
* `POST /api/cvs/extract-pdf`
* `POST /api/applications`
* `GET /api/applications/me`
* `GET /api/job/{job_id}/applications`
* `PATCH /api/applications/{application_id}/status`
* `POST /api/auth/register`
* `POST /api/auth/login`
* `POST /api/auth/google`
* `GET /api/auth/me`

The prototype reads PostgreSQL + pgvector tables directly, returns run results
synchronously, and does not persist match results or call an LLM at runtime.
Embeddings use local sentence-transformers/all-MiniLM-L6-v2 only; no external
AI API key is required.
Authentication is additive and does not guard the V2 prototype endpoints yet.
"""

OPENAPI_TAGS = [
    {
        "name": "catalog-v2-prototype",
        "description": (
            "V2 Prototype · Read-only catalog over `job_posts_v2` / "
            "`candidate_profiles_v2`. Supports paginated browse, detail "
            "lookup, and pgvector-backed semantic search."
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
    {
        "name": "matching-v2-hybrid-prototype",
        "description": (
            "V2 Prototype · Additive hybrid matcher. Uses current V2 tables, "
            "returns 0..100 scores with normalized weighted breakdown, "
            "skipped groups, failed filters, warnings, and explanations."
        ),
    },
    {
        "name": "normal-search",
        "description": (
            "JobConnect normal search · Paginated non-vector job/CV search "
            "for the Find Job and Find CV pages. Does not return matching "
            "percentages or call embedding paths."
        ),
    },
    {
        "name": "normal-job",
        "description": (
            "JobConnect normal Job CRUD and public multi-industry job search. "
            "Jobs are owned by users through `created_by`."
        ),
    },
    {
        "name": "normal-cv",
        "description": (
            "JobConnect normal CV CRUD and PDF CV upload. CVs are owned by "
            "users through `created_by`."
        ),
    },
    {
        "name": "normal-cv-management",
        "description": (
            "CamelCase normal CV management aliases for candidate-owned CV "
            "collections. Backed by PostgreSQL `cvs`."
        ),
    },
    {
        "name": "normal-employer-request-management",
        "description": (
            "CamelCase employer recruitment request management aliases. "
            "Backed by PostgreSQL `jobs` and isolated from V2."
        ),
    },
    {
        "name": "normal-applications",
        "description": (
            "Normal candidate applications linking PostgreSQL `jobs`, `cvs`, "
            "candidate users, and recruiter users. No matching scores."
        ),
    },
    {
        "name": "auth",
        "description": (
            "JobConnect authentication. PostgreSQL-backed registration, "
            "password login, Google login, and JWT current-user lookup."
        ),
    },
    {"name": "system", "description": "Health checks and runtime probes."},
    {"name": "root", "description": "Service root."},
]


app = FastAPI(
    title="Job Matcher API",
    description=API_DESCRIPTION,
    version="2.0.0",
    openapi_tags=OPENAPI_TAGS,
    contact={"name": "JobConnect Engineering"},
)

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

app.include_router(match_v2_router.router, prefix="/api")
app.include_router(match_hybrid_router.router, prefix="/api")
app.include_router(v2_catalog_router.router, prefix="/api")
app.include_router(job_router.router, prefix="/api")
app.include_router(job_router.employer_requests_router, prefix="/api")
app.include_router(cv_router.router, prefix="/api")
app.include_router(cv_router.cvs_router, prefix="/api")
app.include_router(application_router.router, prefix="/api")
app.include_router(normal_search_router.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")


@app.get(
    "/",
    tags=["root"],
    summary="Service root",
    description=(
        "Service banner endpoint. Returns a welcome payload; use "
        "`GET /api/health` for the liveness probe used by Docker Compose."
    ),
)
async def root():
    return {"message": "Job Matcher API V2"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
