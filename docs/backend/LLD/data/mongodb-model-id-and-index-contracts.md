# LLD: MongoDB Model ID and Index Contracts

## Source Anchors
- `backend/models/*.py`
- `backend/db.py`
- `backend/repositories/*.py`

## Initialized Document Models
Beanie initialization includes:
- `User`
- `CandidateProfile`
- `RecruiterProfile`
- `JobPost`
- `CandidateResume`
- `MatchResult`
- `Application`

## Collection Mapping
- `users`
- `candidate_profiles`
- `recruiter_profiles`
- `job_posts`
- `candidate_resumes`
- `match_results`
- `applications`

## Manual Numeric ID Strategy
Repository classes mostly use max+1 allocation:
- `user_id`
- `cv_id`
- `job_id`
- `match_id`
- `app_id`

Behavioral consequence:
- susceptible to race conditions under concurrent writers.
- no transactional allocator or counters collection exists.

## Domain Key Usage
- Candidate/Recruiter profiles key by `user_id`.
- CV key by `cv_id` with foreign key `user_id`.
- Job key by `job_id` with foreign key `recruiter_id`.
- Application key by `app_id` with cross refs (`job_id`, `candidate_id`, `cv_id`).
- Match key by `match_id` and pair (`cv_id`, `job_id`).

## MatchResult Index Contract
Explicit indexes in model settings:
1. unique compound: `(cv_id, job_id)`
2. sort-support index: `(cv_id, score desc)`
3. sort-support index: `(job_id, score desc)`

Usage:
- prevents duplicate pair rows
- supports fast ranking reads and top-k cleanup

## Timestamp Defaults
Most models use `datetime.utcnow()` directly in field defaults.
Operational caution:
- this pattern can freeze default timestamps at import time in plain Python dataclass semantics.
- `Application` uses `Field(default_factory=datetime.utcnow)` which is safer.

(Documentation note only; no behavior change applied here.)

## Related LLD
- Cross-store consistency: `cross-store-consistency-and-failure-modes.md`
- Match orchestration using these indexes: `../matching/matching-orchestration-and-topk-sync.md`
- API matrix using ID fields: `../api/backend-endpoint-schema-matrix.md`
