# Backend HLD V2: API and Runtime Flow (Run-Only)

## API Surface

Auth:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Normal search:
- `GET /api/jobs`
- `GET /api/cvs`
- `GET /api/candidates`

Matching:
- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

Hybrid matching:
- `POST /api/v2/prototype/matching-hybrid/job/{job_id}/run`
- `POST /api/v2/prototype/matching-hybrid/cv/{cv_id}/run`

GET/DELETE persisted match endpoints are outside run-only prototype scope.

## Catalog Helper Surface

Added to let the frontend browse, look up, and semantically search the V2 prototype dataset before invoking a `run`. All endpoints are **read-only** and therefore preserve the run-only constraint of the matching surface.

Browse (paginated, ordered by id ASC):
- `GET /api/v2/prototype/catalog/jobs?limit=&offset=`
- `GET /api/v2/prototype/catalog/cvs?limit=&offset=`

Detail (404 when id missing):
- `GET /api/v2/prototype/catalog/jobs/{job_id}`
- `GET /api/v2/prototype/catalog/cvs/{cv_id}`

Semantic search (pgvector cosine, blended `title` + `skills`):
- `POST /api/v2/prototype/catalog/jobs/search`
- `POST /api/v2/prototype/catalog/cvs/search`

Body for search: `{q (1..200), top_k (1..50, default 20), blend_skills (0..1, default 0.3), location?, job_type?, seniority?}`. Empty/whitespace `q` short-circuits to `{items:[],total:0}` without touching the database. Query embedding uses local `sentence-transformers/all-MiniLM-L6-v2` through `backend/v2_search/embedder.py`. If the local model files are unavailable, the endpoint returns `503` rather than calling a remote fallback API.

## Normal Search Flow

The normal Find Job / Find CV pages use `GET /api/job/search` and
`GET /api/cv/search`; compatibility aliases `GET /api/jobs`, `GET /api/cvs`,
and `GET /api/candidates` route to the same normal-table search functions.
These endpoints are separate from Matching V2 and catalog semantic search:

1. Read the normal PostgreSQL tables `jobs` and `cvs`.
2. Apply deterministic text/rule filters for keyword, location, industry,
   employment type, experience level, education, working model, skills,
   sort, and pagination where current normal schema fields exist.
3. Accept forward-compatible salary/expected salary/availability params, but
   those are no-ops until the database has dedicated columns.
4. Return `{items,total,page,limit,totalPages}` and no relevance percentage.
5. Do not read V2 scenario JSON, V2 prototype tables, or any MongoDB/Mongoose
   source.

## Run Flow

Original matcher:

1. Validate request (`top_k`, `min_score`).
2. Load anchor by ID from PostgreSQL.
3. Load candidate pool from PostgreSQL.
4. Apply hard filters (`location` strict exact text + business filters).
5. Compute component scores and final score.
6. Build deterministic reasoning text.
7. Sort by `final_score desc`, then deterministic ID asc.
8. Return top-k result with `rank`, score breakdown, reasoning, and runtime metrics.

Hybrid matcher:

1. Validate request (`top_k`, `min_score`, `include_failed`, `strict_filters`).
2. Load the same V2 anchor, pool, and embedding rows from PostgreSQL.
3. Evaluate every pair without early exclusion.
4. Calculate available groups on a 0..100 scale: title, skills, experience,
   seniority, education, certification, location, and job type.
5. Skip unavailable current-schema groups (`project`, `language`, `salary`) and
   skip groups where the JD side has no comparable requirement.
6. Normalize only the weights of valid groups before computing `final_score`.
7. Mark `passed=false` when strict filters fail, optionally include failed pairs,
   sort by `final_score desc`, then deterministic ID asc.

## Auth Flow

Registration validates email/password/role, hashes the password, and writes one
row to `users`. Login verifies the password hash and returns a JWT bearer token
plus user details. `/api/auth/me` validates the bearer token and reloads the
current user from PostgreSQL.

## Runtime Metrics in Response

- `runtime_ms_total`
- `runtime_ms_filter`
- `runtime_ms_scoring`
- `runtime_ms_sort`

## Contract Notes

- Prototype is evaluation-only and does not depend on ingestion pipeline. Test data is inserted directly into PostgreSQL; extract/parse flows are excluded.
- Run-only prototype does not persist results, does not add matching auth/role guard changes, and does not compare against other pipelines.
- No OpenAI, Gemini, Cohere, HuggingFace Inference API, or remote LLM/embedding
  API is used. No OpenAI/Gemini API key is needed.
- Local MiniLM model files must be available in the runtime environment; the
  loader uses local files only and does not download during request handling.
- The original `/matching/*` endpoint contract remains 0..1 and unchanged.
  Hybrid `/matching-hybrid/*` is a parallel contract with 0..100 scores,
  `breakdown`, `skipped_groups`, `failed_filters`, `warnings`, and
  `explanations`.
