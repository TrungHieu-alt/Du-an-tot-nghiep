# Backend HLD V2: API and Runtime Flow (Run-Only)

## API Surface

Namespace: `/api/v2/prototype/matching`

- `POST /job/{job_id}/run`
- `POST /cv/{cv_id}/run`

GET/DELETE persisted match endpoints are outside run-only prototype scope.

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
- Route v2 runs independently from production matching routes.
- Run-only prototype does not persist results, does not add auth/role guard changes, and does not compare old-vs-v2.
