# LLD: CV Manual CRUD and Main CV Flow

## Source Anchors
- `backend/routers/cv_router.py`
- `backend/services/cv_service.py`
- `backend/repositories/cv_repo.py`
- `backend/models/candidateResume.py`

## Scope Boundary
This file owns manual CRUD and main-CV retrieval behavior only.
Upload/parse/embed internals are owned by:
- `cv-upload-parse-embed-store-flow.md`

## Data Contract
`CandidateResume` key fields:
- `cv_id` (manual integer sequence)
- `user_id`
- title/location/experience/skills/summary/full_text
- `pdf_url`, `is_main`
- timestamps

Collection: `candidate_resumes`

## Create CV (Manual JSON)
Endpoint:
- `POST /api/cv/create/{user_id}`

Execution:
1. Router validates `CandidateResumeRequest`.
2. Service forwards fields to repository `create`.
3. Repository computes `cv_id=max+1` and inserts record.

Notes:
- This path does not preprocess, parse, or generate embeddings.
- `embedding` field in model remains unused for vector retrieval.

## Read Flows
Endpoints:
- `GET /api/cv/{cv_id}`
- `GET /api/cv/user/{user_id}`
- `GET /api/cv/main/user/{user_id}`

Execution:
- Get-by-id returns 404 if missing.
- Get-by-user returns all CV rows for user.
- Main-CV flow loads user CV list and returns first `is_main=True`; if none, returns 404.

## Update CV
Endpoint:
- `PUT /api/cv/{cv_id}`

Execution:
1. Router accepts full `CandidateResumeRequest`.
2. Service delegates to repository `update`.
3. Repository applies `$set` and sets `updated_at=datetime.utcnow()`.

Failure:
- missing CV -> HTTP 404

## Delete CV
Endpoint:
- `DELETE /api/cv/{cv_id}`

Execution:
1. Repository loads CV by `cv_id`.
2. Attempts Chroma delete for `cv_{cv_id}` (logs warning on failure).
3. Deletes Mongo document.

Failure:
- missing CV -> HTTP 404

## Matching Entry Endpoints in CV Router
Endpoints:
- `GET /api/cv/match/{cv_id}/jobs`
- `GET /api/cv/match/{cv_id}/jobs/{job_id}`

Ownership note:
- Algorithm and scoring are documented in matching LLD files.
- This file only records endpoint presence in CV domain.

## Related LLD
- CV upload pipeline: `cv-upload-parse-embed-store-flow.md`
- Matching algorithm: `../matching/matching-core-algorithm-details.md`
- Match orchestration and persistence: `../matching/matching-orchestration-and-topk-sync.md`
