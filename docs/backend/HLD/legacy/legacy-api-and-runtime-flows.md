# Backend HLD V2: API and Runtime Flow (Run-Only)

> Legacy prototype HLD. This file documents current `/api/v2/prototype/*`
> runtime behavior. Use `docs/backend/HLD/50-api-and-runtime-flows.md`
> for target MVP API/runtime architecture.

## API Surface

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

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

Body for search: `{q (1..200), top_k (1..50, default 20), blend_skills (0..1, default 0.3), location?, job_type?, seniority?}`. Empty/whitespace `q` short-circuits to `{items:[],total:0}` without touching the database. Embedder reused from `backend/v2_search/embedder.py` — the same hash-based 384-d algorithm that seeded the stored embeddings, so query vectors are cosine-comparable.

## Run Flow

1. Validate request (`top_k`, `min_score`).
2. Load anchor by ID from PostgreSQL.
3. Load candidate pool from PostgreSQL.
4. Apply hard filters (`location` strict exact text + business filters).
5. Compute component scores and final score.
6. Build deterministic reasoning text.
7. Sort by `final_score desc`, then deterministic ID asc.
8. Return top-k result with `rank`, score breakdown, reasoning, and runtime metrics.

## Runtime Metrics in Response

- `runtime_ms_total`
- `runtime_ms_filter`
- `runtime_ms_scoring`
- `runtime_ms_sort`

## Contract Notes

- Prototype is evaluation-only and does not depend on ingestion pipeline. Test data is inserted directly into PostgreSQL; extract/parse flows are excluded.
- Run-only prototype does not persist results, does not add auth/role guard changes, and does not compare against other pipelines.
