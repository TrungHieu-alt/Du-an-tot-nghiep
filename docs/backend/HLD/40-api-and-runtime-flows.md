# Backend HLD V2: API Surface and Runtime Flows

## Prototype API Surface

Namespace: `/api/v2/prototype/matching`

- `POST /job/{job_id}/run`
- `POST /cv/{cv_id}/run`
- `GET /job/{job_id}/matches`
- `GET /cv/{cv_id}/matches`
- `DELETE /job/{job_id}/matches`
- `DELETE /cv/{cv_id}/matches`

## Run Flow

1. Validate request (`top_k`, `min_score`, version flags nếu có).
2. Read anchor record + embeddings from PostgreSQL.
3. Apply hard filters.
4. Calculate semantic+exact component scores.
5. Apply rule rerank.
6. Persist top-k to `match_results_v2`.
7. Return summary + score breakdown preview.

## Runtime Contract

- V2 routes chạy độc lập với production matching routes.
- Lỗi matching trả về error contract rõ ràng theo router schema.
- Read endpoints trả enriched payload để frontend quan sát kết quả.
