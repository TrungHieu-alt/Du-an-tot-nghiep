# LLD: Match Query Enrichment and Cleanup Flows

## Source Anchors
- `backend/routers/match_router.py`
- `backend/services/match_service.py`
- `backend/repositories/match_repo.py`
- `backend/repositories/cv_repo.py`
- `backend/repositories/job_repo.py`

## Scope Boundary
This file owns read/query/delete semantics for persisted matches.
Run orchestration and algorithm formulas are documented in separate matching LLD files.

## Read Matches for Job
Endpoint:
- `GET /api/matching/job/{job_id}/matches`

Inputs:
- `min_score` in `[0,1]`
- `limit` in `[1,100]`
- `skip >= 0`

Service flow:
1. Read sorted `MatchResult` rows by `job_id` and `score >= min_score`.
2. For each row, fetch CV by `cv_id`.
3. Return enriched payload embedding CV summary fields.

Returned enriched CV fields:
- `title`, `location`, `experience`, `skills`, `user_id`

## Read Matches for CV
Endpoint:
- `GET /api/matching/cv/{cv_id}/matches`

Service flow mirrors job read:
1. Read `MatchResult` rows for `cv_id`.
2. Fetch Job by `job_id` per row.
3. Return enriched payload with Job summary.

Returned enriched Job fields:
- `title`, `role`, `location`, `job_type`, `experience_level`, `skills`, `recruiter_id`

## Pagination and Counts
Router additionally queries counts from repository:
- `count_by_job_id(job_id, min_score)`
- `count_by_cv_id(cv_id, min_score)`

Response includes `total` + current page `matches` list.

## Delete All Matches for Anchor Entity
Endpoints:
- `DELETE /api/matching/cv/{cv_id}/matches`
- `DELETE /api/matching/job/{job_id}/matches`

Service behavior:
- CV delete endpoint uses `MatchRepository.delete_by_cv_id`
- Job delete endpoint uses `MatchRepository.delete_by_job_id`

Intended use in service docstring:
- cascade delete when CV/Job is deleted
- not normal re-run path (re-run uses top-k cleanup)

## Drift Note (Docstring mismatch)
Router delete endpoint docstrings mention usage for re-running matching.
Service notes explicitly state these are cascade-delete operations and re-run should rely on TOP-K sync cleanup.

## Related LLD
- Run orchestration and top-k sync: `matching-orchestration-and-topk-sync.md`
- API response schema inventory: `../api/backend-endpoint-schema-matrix.md`
