# LLD: Job Manual CRUD Flow

## Source Anchors
- `backend/routers/job_router.py`
- `backend/services/job_service.py`
- `backend/repositories/job_repo.py`
- `backend/models/jobPost.py`

## Scope Boundary
This file owns manual Job CRUD behavior only.
Job ingestion internals are owned by:
- `job-upload-parse-embed-store-flow.md`

## Data Contract
`JobPost` key fields:
- `job_id` (manual integer sequence)
- `recruiter_id`
- title, role, location, job_type, experience_level
- skills, salary range, full_text, pdf_url
- timestamps

Collection: `job_posts`

## Create Job (Manual JSON)
Endpoint:
- `POST /api/jobs/create/{recruiter_id}`

Execution:
1. Router validates `JobPostRequest`.
2. Service forwards to repository `create`.
3. Repository computes `job_id=max+1`, inserts record.

Note:
- No parse/embed/vector-store activity in this path.

## Read Flows
Endpoints:
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/recruiter/{recruiter_id}`

Execution:
- all jobs list
- single by id (404 on missing)
- per recruiter list

## Update Job
Endpoint:
- `PUT /api/jobs/{job_id}`

Execution:
1. Router accepts full request body.
2. Repository applies `$set` + refreshes `updated_at`.
3. Returns updated row.

Failure:
- missing job -> HTTP 404

## Delete Job
Endpoint:
- `DELETE /api/jobs/{job_id}`

Execution:
1. Repository loads job row.
2. Best-effort delete Chroma record `jd_{job_id}`.
3. Deletes Mongo row.

Failure:
- missing job -> HTTP 404

## Matching Entry Endpoints in Job Router
Endpoints:
- `GET /api/jobs/match/{job_id}/cvs`
- `GET /api/jobs/match/{job_id}/cvs/{cv_id}`

Ownership note:
- This file tracks route entry only.
- Algorithm/persistence details belong to matching LLD.

## Related LLD
- Job ingestion pipeline: `job-upload-parse-embed-store-flow.md`
- Matching algorithm: `../matching/matching-core-algorithm-details.md`
- Match orchestration/persistence: `../matching/matching-orchestration-and-topk-sync.md`
