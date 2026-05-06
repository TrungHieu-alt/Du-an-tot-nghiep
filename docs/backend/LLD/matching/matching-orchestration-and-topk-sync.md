# LLD V2: Matching Orchestration and TOP-K Sync

## Scope

Mô tả service-level orchestration cho route prototype v2.

## Entry Endpoints

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

## Orchestration Steps

1. Validate input (`top_k`, `min_score`).
2. Load anchor entity + embeddings.
3. Retrieve candidates qua pgvector ANN.
4. Hard filter candidates.
5. Compute component scores + final score.
6. Persist `match_results_v2` với upsert theo cặp `(cv_id, job_id)`.
7. Cleanup rows ngoài top_k cho anchor.
8. Return summary + preview.

## Persistence Contract

Lưu các trường:
- `final_score`
- `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`
- `exact_skill_bonus`, `required_penalty`
- `scoring_version`, `feature_version`, `embedding_model_version`

## Query Endpoints

- `GET /api/v2/prototype/matching/job/{job_id}/matches`
- `GET /api/v2/prototype/matching/cv/{cv_id}/matches`

Các endpoint query trả dữ liệu enriched và có filter `min_score`, `limit`, `offset`.
