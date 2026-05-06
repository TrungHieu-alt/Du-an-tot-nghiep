# Backend HLD V2: API and Runtime Flow (Matching-Only)

## API Surface

Namespace: `/api/v2/prototype/matching`

- `POST /job/{job_id}/run`
- `POST /cv/{cv_id}/run`
- `GET /job/{job_id}/matches`
- `GET /cv/{cv_id}/matches`
- `DELETE /job/{job_id}/matches`
- `DELETE /cv/{cv_id}/matches`

## Run Flow

1. Validate request (`top_k`, `min_score`, `scoring_version`).
2. Load anchor by ID from PostgreSQL.
3. Query candidate pool through pgvector.
4. Apply hard filters (`location` strict exact text + business filters).
5. Compute component scores and final score.
6. Build deterministic reasoning text.
7. Persist top 10 to `match_results_v2`.
8. Return result with score breakdown and runtime metrics.

## Runtime Metrics in Response

- `runtime_ms_total`
- `runtime_ms_filter`
- `runtime_ms_scoring`
- `runtime_ms_sort`

## Contract Notes

- Prototype is evaluation-only and does not depend on ingestion pipeline. Test data is inserted directly into PostgreSQL; extract/parse flows are excluded.
- Route v2 runs independently from production matching routes.
