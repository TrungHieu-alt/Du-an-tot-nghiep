# LLD: Matching Orchestration and TOP-K Sync

## Source Anchors
- `backend/services/match_service.py`
- `backend/repositories/match_repo.py`
- `backend/repositories/job_repo.py`
- `backend/repositories/cv_repo.py`
- `backend/models/matchResult.py`

## Scope Boundary
This file owns run-matching orchestration and persistence lifecycle.
Algorithm stage internals are owned by:
- `matching-core-algorithm-details.md`

## Run Matching for Job
Entry:
- `POST /api/matching/job/{job_id}/run`

Service flow (`run_matching_for_job`):
1. Retrieve candidate CV matches from `JobRepository.find_matching_cvs(job_id, top_k)`.
2. For each candidate:
   - require `cv_id`
   - compute final score (same hybrid formula used here)
   - skip below `min_score`
   - build metadata: `cosine_ann`, `weighted_sim`, `llm_score`, `reason`
   - upsert via `MatchRepository.create_or_update`
3. Cleanup tail records with `delete_matches_outside_top_k_for_job`.
4. Return summary with top-10 preview only.

## Run Matching for CV
Entry:
- `POST /api/matching/cv/{cv_id}/run`

Service flow mirrors job flow:
1. Read `CVRepository.find_matching_jobs`.
2. Score threshold filtering + upsert.
3. Cleanup using `delete_matches_outside_top_k_for_cv`.
4. Return summary preview.

## Upsert Contract (`create_or_update`)
Repository behavior:
- unique key: `(cv_id, job_id)`
- existing row -> update score/metadata + `updated_at`
- missing row -> generate `match_id=max+1`, insert

## TOP-K Cleanup Contract
- job anchor cleanup deletes low-score rows beyond top_k for that `job_id`
- cv anchor cleanup deletes low-score rows beyond top_k for that `cv_id`

Data guarantee:
- after run, anchor entity has at most `top_k` stored matches.

## Threshold and Score Semantics
`min_score` is applied in service before persistence.
Formula in service matches current algorithm weights:
- `0.2*cosine_ann + 0.5*weighted_sim + 0.3*(llm_score/100)`

## Failure Behavior
- service catches and logs exceptions, then re-raises to router.
- router returns HTTP 500 with raw exception text in `detail`.

## Persistence Model
Stored document includes:
- ids: `match_id`, `cv_id`, `job_id`
- `score`
- `metadata` (component scores + reason)
- timestamps

Indexes are owned by data LLD.

## Related LLD
- Matching algorithm details: `matching-core-algorithm-details.md`
- Query/read/delete semantics: `match-query-enrichment-and-cleanup-flows.md`
- Match model/index contracts: `../data/mongodb-model-id-and-index-contracts.md`
