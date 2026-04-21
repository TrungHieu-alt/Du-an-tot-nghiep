# LLD: Application Create Query Status Flow

## Source Anchors
- `backend/routers/application_router.py`
- `backend/services/application_service.py`
- `backend/repositories/application_repo.py`
- `backend/models/application.py`

## Scope Boundary
This file owns application create/query/status-update lifecycle.
Delete drift is isolated in:
- `application-delete-flow-drift-note.md`

## Data Contract
`Application` fields:
- `app_id` (manual sequence)
- `job_id`, `candidate_id`, `cv_id`
- optional `match_id`
- `cover_letter` (max 5000)
- `status` in `pending|viewed|interviewing|rejected|hired`
- timestamps

Collection: `applications`

## Create Application
Endpoint:
- `POST /api/applications/`

Service validation sequence:
1. Cover letter length <= 5000.
2. Job exists (`JobRepository.get_by_id`).
3. Candidate exists (`CandidateRepository.get_by_user_id`).
4. CV exists and CV `user_id == candidate_id`.
5. No duplicate application for same `(cv_id, job_id)`.

Repository create behavior:
- re-check duplicate `(cv_id, job_id)`
- assign `app_id=max+1`
- insert with initial status `pending`

Response shape:
- application router wraps with `{ success: true, data: ... }`.

## Query by Job
Endpoint:
- `GET /api/applications/job/{job_id}`

Behavior:
- optional status filter validated against allowed statuses
- sorted by `created_at desc`
- pagination using `limit` and `skip`
- response includes `total`, `limit`, `skip`, `applications`

## Query by Candidate
Endpoint:
- `GET /api/applications/candidate/{candidate_id}`

Behavior mirrors job query with candidate-scoped filters.

## Update Status
Endpoint:
- `PATCH /api/applications/{app_id}/status`

Behavior:
1. Validate status against allowed list.
2. Repository update status + `updated_at`.
3. Return app id, new status, updated timestamp.

Failure conditions:
- invalid status -> HTTP 400
- app not found -> HTTP 400 via ValueError mapping

## Related LLD
- Application delete drift: `application-delete-flow-drift-note.md`
- Runtime API behavior patterns: `../runtime/router-contract-and-error-patterns.md`
- Model/id contracts: `../data/mongodb-model-id-and-index-contracts.md`
