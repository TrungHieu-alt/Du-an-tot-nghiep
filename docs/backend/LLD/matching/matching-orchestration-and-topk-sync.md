# LLD V2: Matching Orchestration and TOP-10 Sync

## Scope

Service orchestration cho prototype matching-only.

## Endpoints

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

## Flow

1. Validate request (`top_k`, `min_score`, `scoring_version`).
2. Load anchor record by ID.
3. Retrieve candidate pool via pgvector ANN.
4. Apply hard filters (`location` strict exact text + domain filters).
5. Compute component/final scores.
6. Build reasoning template.
7. Keep top 10 (or `top_k` <= 10 for experiments).
8. Upsert `match_results_v2` by `(cv_id, job_id)`.
9. Remove rows outside current top-k for anchor.
10. Return summary + score breakdown + runtime metrics.

## Persistence fields

- IDs: `cv_id`, `job_id`
- `final_score`
- `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`
- `exact_skill_bonus`, `required_penalty`
- `reasoning`
- runtime metrics fields
- `scoring_version`, `feature_version`, timestamps
