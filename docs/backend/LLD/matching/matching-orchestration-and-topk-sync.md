# LLD V2: Matching Run-Only Orchestration

## Scope

Service orchestration cho prototype run-only: input `job_id` hoặc `cv_id`, output ranked matches có điểm + reasoning.

## Endpoints

- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`

## Flow

1. Validate request (`top_k`, `min_score`).
2. Load anchor record by ID.
3. Load candidate pool from PostgreSQL.
4. Apply hard filters (`location` strict exact text + domain filters).
5. Compute component/final scores.
6. Build reasoning template.
7. Keep top 10 (or `top_k` <= 10 for experiments).
8. Add deterministic rank after sorting by `final_score desc`, then candidate ID asc.
9. Return summary + score breakdown + reasoning + runtime metrics.

## Persistence

Run-only prototype does not persist match results.

Do not create, upsert, delete, or query `match_results_v2` unless `docs/REQUIREMENTS.md` is expanded for a later phase.
