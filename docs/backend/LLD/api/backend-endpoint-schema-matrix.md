# LLD: Backend API Reference For Frontend Wiring

## Source of Truth
- `backend/main.py`
- `backend/routers/*.py`
- `backend/schemas/*.py`
- `backend/services/*.py`
- `backend/repositories/*.py`

## Base URL and Global Behavior
- Base path for frontend integration: `/api`
- Health route: `GET /api/health`
- Additional non-API root route: `GET /`
- CORS allows:
  - `http://localhost:5173`
  - `http://127.0.0.1:5173`
- Auth enforcement: no route-level dependency guards are currently declared in routers.

## Common Response/Error Shapes
- Most non-application routes return either:
  - a Pydantic response model (object/list), or
  - a simple message object for deletes.
- FastAPI/HTTPException error shape:

```json
{
  "detail": "Error message"
}
```

- Application routes use envelope responses:

```json
{
  "success": true,
  "data": {}
}
```

or

```json
{
  "success": true,
  "message": "...",
  "data": {}
}
```

## Shared Schemas

### `UserRegisterRequest`
```json
{
  "email": "user@example.com",
  "password": "string",
  "role": "candidate | recruiter | null"
}
```

### `UserLoginRequest`
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

### `UserResponse`
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "role": "candidate",
  "created_at": "2026-04-21T00:00:00Z",
  "updated_at": "2026-04-21T00:00:00Z"
}
```

### `TokenResponse`
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### `CandidateProfileRequest`
```json
{
  "full_name": "string",
  "location": "string | null",
  "experience_years": 0,
  "skills": ["Python", "FastAPI"],
  "summary": "string | null"
}
```

### `CandidateProfileResponse`
```json
{
  "user_id": 1,
  "full_name": "string",
  "location": "string | null",
  "experience_years": 3,
  "skills": ["Python"],
  "summary": "string | null",
  "created_at": "2026-04-21T00:00:00Z",
  "updated_at": "2026-04-21T00:00:00Z"
}
```

### `RecruiterProfileRequest`
```json
{
  "company_name": "string",
  "recruiter_title": "string",
  "company_logo": "string | null",
  "about_company": "string | null",
  "hiring_fields": ["Backend", "AI"]
}
```

### `RecruiterProfileResponse`
```json
{
  "user_id": 2,
  "company_name": "string",
  "recruiter_title": "string",
  "company_logo": "string | null",
  "about_company": "string | null",
  "hiring_fields": ["Backend"],
  "created_at": "2026-04-21T00:00:00Z",
  "updated_at": "2026-04-21T00:00:00Z"
}
```

### `CandidateResumeRequest`
```json
{
  "title": "Senior Backend CV",
  "location": "HCMC",
  "experience": "5 years",
  "skills": ["Python", "MongoDB"],
  "summary": "string | null",
  "full_text": "string | null",
  "pdf_url": "string | null",
  "is_main": false
}
```

### `CandidateResumeResponse`
```json
{
  "cv_id": 10,
  "user_id": 1,
  "title": "Senior Backend CV",
  "location": "HCMC",
  "experience": "5 years",
  "skills": ["Python", "MongoDB"],
  "summary": "string | null",
  "full_text": "string | null",
  "pdf_url": "string | null",
  "is_main": false,
  "created_at": "2026-04-21T00:00:00Z",
  "updated_at": "2026-04-21T00:00:00Z"
}
```

### `JobPostRequest`
```json
{
  "title": "Backend Engineer",
  "role": "Software Engineer",
  "location": "HCMC",
  "job_type": "Full-time",
  "experience_level": "Mid-level",
  "skills": ["Python", "FastAPI"],
  "salary_min": 1000,
  "salary_max": 2500,
  "full_text": "string | null",
  "pdf_url": "string | null"
}
```

### `JobPostResponse`
```json
{
  "job_id": 100,
  "recruiter_id": 2,
  "title": "Backend Engineer",
  "role": "Software Engineer",
  "location": "HCMC",
  "job_type": "Full-time",
  "experience_level": "Mid-level",
  "skills": ["Python", "FastAPI"],
  "salary_min": 1000,
  "salary_max": 2500,
  "full_text": "string | null",
  "pdf_url": "string | null",
  "created_at": "2026-04-21T00:00:00Z",
  "updated_at": "2026-04-21T00:00:00Z"
}
```

### Matching schemas

`RunMatchingRequest` (inline in router):
```json
{
  "top_k": 50,
  "min_score": 0.7
}
```

`RunMatchingResponse`:
```json
{
  "cv_id": 10,
  "job_id": null,
  "total_found": 50,
  "total_saved": 12,
  "min_score": 0.7,
  "matches": [
    {
      "match_id": 1,
      "cv_id": null,
      "job_id": 100,
      "score": 0.84,
      "reason": "Strong skills match"
    }
  ]
}
```

`JobMatchesResponse`:
```json
{
  "total": 3,
  "matches": [
    {
      "match_id": 1,
      "cv_id": 10,
      "score": 0.82,
      "metadata": {
        "cosine_ann": 0.8,
        "weighted_sim": 0.81,
        "llm_score": 85,
        "reason": "Good fit"
      },
      "created_at": "2026-04-21T00:00:00Z",
      "updated_at": "2026-04-21T00:00:00Z",
      "cv": {
        "title": "Senior Backend CV",
        "location": "HCMC",
        "experience": "5 years",
        "skills": ["Python"],
        "user_id": 1
      }
    }
  ]
}
```

`CVMatchesResponse`:
```json
{
  "total": 3,
  "matches": [
    {
      "match_id": 1,
      "job_id": 100,
      "score": 0.82,
      "metadata": {
        "cosine_ann": 0.8,
        "weighted_sim": 0.81,
        "llm_score": 85,
        "reason": "Good fit"
      },
      "created_at": "2026-04-21T00:00:00Z",
      "updated_at": "2026-04-21T00:00:00Z",
      "job": {
        "title": "Backend Engineer",
        "role": "Software Engineer",
        "location": "HCMC",
        "job_type": "Full-time",
        "experience_level": "Mid-level",
        "skills": ["Python"],
        "recruiter_id": 2
      }
    }
  ]
}
```

### Application inline request schemas

`CreateApplicationRequest` (inline in router):
```json
{
  "job_id": 100,
  "candidate_id": 1,
  "cv_id": 10,
  "cover_letter": "string"
}
```

`UpdateApplicationStatusRequest` (inline in router):
```json
{
  "status": "pending | viewed | interviewing | rejected | hired"
}
```

## Route Catalog

## Users (`/api/users`)

### `POST /api/users/register`
- Request body: `UserRegisterRequest`
- Success `201`: `UserResponse`
- Common errors:
  - `400` email already exists (`detail`)

### `POST /api/users/login`
- Request body: `UserLoginRequest`
- Success `200`: `TokenResponse`
- Common errors:
  - `401` invalid credentials (`detail`)

### `GET /api/users/{user_id}`
- Path params: `user_id: int`
- Success `200`: `UserResponse`
- Common errors:
  - `404` user not found

### `DELETE /api/users/{user_id}`
- Path params: `user_id: int`
- Success `200`:
```json
{ "message": "User deleted" }
```
- Common errors:
  - `404` user not found

### `PUT /api/users/{user_id}/role`
- Path params: `user_id: int`
- Request body (raw dict):
```json
{ "role": "candidate | recruiter" }
```
- Success `200`: `UserResponse`
- Common errors:
  - `400` invalid role
  - `404` user not found

## Candidate (`/api/candidate`)

### `POST /api/candidate/profile/{user_id}`
- Path params: `user_id: int`
- Request body: `CandidateProfileRequest`
- Success `201`: `CandidateProfileResponse`
- Common errors:
  - `400` profile already exists

### `GET /api/candidate/profile/{user_id}`
- Path params: `user_id: int`
- Success `200`: `CandidateProfileResponse`
- Common errors:
  - `404` profile not found

### `PUT /api/candidate/profile/{user_id}`
- Path params: `user_id: int`
- Request body: `CandidateProfileRequest`
- Success `200`: `CandidateProfileResponse`
- Common errors:
  - `404` profile not found

### `GET /api/candidate/profiles`
- Success `200`: `CandidateProfileResponse[]`

## Recruiter (`/api/recruiter`)

### `POST /api/recruiter/profile/{user_id}`
- Path params: `user_id: int`
- Request body: `RecruiterProfileRequest`
- Success `201`: `RecruiterProfileResponse`
- Common errors:
  - `400` profile already exists

### `GET /api/recruiter/profile/{user_id}`
- Path params: `user_id: int`
- Success `200`: `RecruiterProfileResponse`
- Common errors:
  - `404` profile not found

### `PUT /api/recruiter/profile/{user_id}`
- Path params: `user_id: int`
- Request body: `RecruiterProfileRequest`
- Success `200`: `RecruiterProfileResponse`
- Common errors:
  - `404` profile not found

## CV (`/api/cv`)

### `POST /api/cv/create/{user_id}`
- Path params: `user_id: int`
- Request body: `CandidateResumeRequest`
- Success `201`: `CandidateResumeResponse`

### `POST /api/cv/upload/{user_id}`
- Path params: `user_id: int`
- Content type: `multipart/form-data`
- Form fields:
  - `file: UploadFile` (required)
  - `is_main: bool` (optional, default `false`)
- Success `200`: `CandidateResumeResponse`
- Common errors:
  - `400` upload/parse failure

### `POST /api/cv/upload-text/{user_id}`
- Path params: `user_id: int`
- Content type: `multipart/form-data`
- Form fields:
  - `full_text: str` (required)
  - `title: str | null` (optional)
  - `is_main: bool` (optional, default `false`)
- Success `200`: `CandidateResumeResponse`
- Common errors:
  - `400` upload/parse failure

### `GET /api/cv/{cv_id}`
- Path params: `cv_id: int`
- Success `200`: `CandidateResumeResponse`
- Common errors:
  - `404` CV not found

### `GET /api/cv/user/{user_id}`
- Path params: `user_id: int`
- Success `200`: `CandidateResumeResponse[]`

### `GET /api/cv/main/user/{user_id}`
- Path params: `user_id: int`
- Success `200`: `CandidateResumeResponse`
- Common errors:
  - `404` Main CV not found

### `PUT /api/cv/{cv_id}`
- Path params: `cv_id: int`
- Request body: `CandidateResumeRequest`
- Success `200`: `CandidateResumeResponse`
- Common errors:
  - `404` CV not found

### `DELETE /api/cv/{cv_id}`
- Path params: `cv_id: int`
- Success `200`:
```json
{ "message": "CV deleted successfully" }
```
- Common errors:
  - `404` CV not found

### `GET /api/cv/match/{cv_id}/jobs`
- Path params: `cv_id: int`
- Query params:
  - `top_k: int` (default `5`, range `1..20`)
- Success `200`: `List[Dict]`
- Returned item structure (from matching pipeline):
```json
{
  "id": "jd_100",
  "jd": { "...": "raw JD metadata from Chroma" },
  "cosine_ann": 0.81,
  "weighted_sim": 0.84,
  "llm_score": 87.0,
  "reason": "Strong alignment in required skills",
  "job_id": 100
}
```
- Notes:
  - On internal failures, service returns `[]` instead of raising.

### `GET /api/cv/match/{cv_id}/jobs/{job_id}`
- Path params:
  - `cv_id: int`
  - `job_id: int`
- Success `200`: `Dict`
- Response structure:
```json
{
  "cv_id": 10,
  "job_id": 100,
  "jd_id": "jd_100",
  "scores": {
    "skills": 0.9,
    "experience_requirement": 0.8,
    "summary_description": 0.85,
    "job_title": 0.75,
    "full": 0.8,
    "location": 0.7
  },
  "final_score": 0.83,
  "error": "optional"
}
```

## Jobs (`/api/jobs`)

### `POST /api/jobs/create/{recruiter_id}`
- Path params: `recruiter_id: int`
- Request body: `JobPostRequest`
- Success `201`: `JobPostResponse`

### `POST /api/jobs/upload/{recruiter_id}`
- Path params: `recruiter_id: int`
- Content type: `multipart/form-data`
- Form fields:
  - `file: UploadFile` (required)
  - `title: str | null` (optional)
  - `role: str | null` (optional)
  - `location: str | null` (optional)
  - `job_type: str | null` (optional)
  - `experience_level: str | null` (optional)
  - `salary_min: float | null` (optional)
  - `salary_max: float | null` (optional)
- Success `200`: `JobPostResponse`
- Common errors:
  - `400` upload/parse failure

### `POST /api/jobs/upload-text/{recruiter_id}`
- Path params: `recruiter_id: int`
- Content type: `multipart/form-data`
- Form fields:
  - `full_text: str` (required)
  - `title: str | null` (optional)
  - `role: str | null` (optional)
  - `location: str | null` (optional)
  - `job_type: str | null` (optional)
  - `experience_level: str | null` (optional)
  - `salary_min: float | null` (optional)
  - `salary_max: float | null` (optional)
- Success `200`: `JobPostResponse`
- Common errors:
  - `400` upload/parse failure

### `GET /api/jobs`
- Success `200`: `JobPostResponse[]`

### `GET /api/jobs/{job_id}`
- Path params: `job_id: int`
- Success `200`: `JobPostResponse`
- Common errors:
  - `404` Job not found

### `GET /api/jobs/recruiter/{recruiter_id}`
- Path params: `recruiter_id: int`
- Success `200`: `JobPostResponse[]`

### `PUT /api/jobs/{job_id}`
- Path params: `job_id: int`
- Request body: `JobPostRequest`
- Success `200`: `JobPostResponse`
- Common errors:
  - `404` Job not found

### `DELETE /api/jobs/{job_id}`
- Path params: `job_id: int`
- Success `200`:
```json
{ "message": "Job deleted successfully" }
```
- Common errors:
  - `404` Job not found

### `GET /api/jobs/match/{job_id}/cvs`
- Path params: `job_id: int`
- Query params:
  - `top_k: int` (default `5`, range `1..20`)
- Success `200`: `List[Dict]`
- Returned item structure (from matching pipeline):
```json
{
  "id": "cv_10",
  "cv": { "...": "raw CV metadata from Chroma" },
  "cosine_ann": 0.8,
  "weighted_sim": 0.82,
  "llm_score": 86.0,
  "reason": "Strong skill overlap",
  "cv_id": 10,
  "user_id": 1
}
```
- Notes:
  - On internal failures, service returns `[]` instead of raising.

### `GET /api/jobs/match/{job_id}/cvs/{cv_id}`
- Path params:
  - `job_id: int`
  - `cv_id: int`
- Success `200`: `Dict`
- Response structure:
```json
{
  "job_id": 100,
  "cv_id": 10,
  "jd_id": "jd_100",
  "scores": {
    "skills": 0.9,
    "experience_requirement": 0.8,
    "summary_description": 0.85,
    "job_title": 0.75,
    "full": 0.8,
    "location": 0.7
  },
  "final_score": 0.83,
  "error": "optional"
}
```

## Matching (`/api/v2/prototype/matching`)

### `POST /api/v2/prototype/matching/job/{job_id}/run`
- Path params: `job_id: int`
- Request body: `RunMatchingV2Request`
- Success `200`: `RunMatchingV2Response`
- Errors: `400`, `404`, `500`

### `POST /api/v2/prototype/matching/cv/{cv_id}/run`
- Path params: `cv_id: int`
- Request body: `RunMatchingV2Request`
- Success `200`: `RunMatchingV2Response`
- Errors: `400`, `404`, `500`

Persisted match query/delete endpoints are outside the run-only prototype scope.

### Matching V2 schemas

`RunMatchingV2Request`:
```json
{
  "top_k": 10,
  "min_score": 0.7
}
```

`RunMatchingV2Response`:
```json
{
  "anchor_type": "job",
  "anchor_id": 100,
  "total_candidates": 500,
  "total_after_filter": 73,
  "total_returned": 10,
  "runtime_ms_total": 182,
  "runtime_ms_filter": 21,
  "runtime_ms_scoring": 134,
  "runtime_ms_sort": 4,
  "matches": [
    {
      "rank": 1,
      "cv_id": 10,
      "job_id": 100,
      "final_score": 0.84,
      "title_score": 0.9,
      "skills_score": 0.83,
      "req_exp_score": 0.79,
      "req_summary_score": 0.75,
      "reasoning": "Strong title and skills alignment; requirement-experience fit is good."
    }
  ]
}
```

## Catalog V2 Prototype (`/api/v2/prototype/catalog`)

Read-only helpers added to support the frontend V2 search & detail pages. They do not violate the run-only scope of the matching surface — no writes, no persistence.

### `GET /api/v2/prototype/catalog/jobs`
- Query params: `limit (int, 1..200, default 50)`, `offset (int, >=0, default 0)`
- Success `200`: `JobV2ListResponse` — `{items: JobV2ListItem[], total: int}`
- Errors: `422` on invalid pagination

### `GET /api/v2/prototype/catalog/jobs/{job_id}`
- Path params: `job_id: int`
- Success `200`: `JobV2Detail`
- Errors: `404 {"detail":"job not found"}`

### `GET /api/v2/prototype/catalog/cvs`
- Query params: same as `/jobs`
- Success `200`: `CVV2ListResponse`

### `GET /api/v2/prototype/catalog/cvs/{cv_id}`
- Path params: `cv_id: int`
- Success `200`: `CVV2Detail`
- Errors: `404 {"detail":"cv not found"}`

### `POST /api/v2/prototype/catalog/jobs/search`
- Request body: `CatalogSearchRequest`
- Success `200`: `JobSearchResponse` — `{items: JobSearchItem[], total: int}`
- Errors: `422` on out-of-range fields or unknown enum values; `500` on DB error
- Behavior: trimmed-empty `q` short-circuits to `{items:[],total:0}` without DB call. SQL CTE joins `job_posts_v2` with `job_embeddings_v2`, requires `emb_title IS NOT NULL`, blends `(1 - blend_skills) * cos(emb_title, q_vec) + blend_skills * cos(emb_skills, q_vec)`. Optional filters appended to the CTE WHERE.

### `POST /api/v2/prototype/catalog/cvs/search`
- Mirror of `/jobs/search` against `candidate_profiles_v2 + candidate_embeddings_v2`.
- Success `200`: `CVSearchResponse`.

### Catalog V2 schemas

`CatalogSearchRequest`:
```json
{
  "q": "backend devops",
  "top_k": 20,
  "blend_skills": 0.3,
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "senior"
}
```
- `q`: string, 1..200 chars
- `top_k`: int, 1..50
- `blend_skills`: float, 0..1
- `location`: optional, one of `{ha_noi, tp_hcm, da_nang}`
- `job_type`: optional, one of `{remote, fulltime, parttime}`
- `seniority`: optional, one of `{intern, fresher, junior, mid, senior, lead}`

`JobV2ListItem`:
```json
{
  "job_id": 4001,
  "title": "Senior Backend DevOps Engineer",
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "senior",
  "skills": ["python", "docker", "kubernetes"]
}
```

`JobV2Detail` extends the list item with `requirement: str`, `education: str`, `required_certifications: list[str]`.

`CVV2ListItem` mirrors `JobV2ListItem` with `cv_id` instead of `job_id`. `CVV2Detail` adds `summary`, `experience`, `education`, `certifications`.

`JobSearchItem` / `CVSearchItem` extend the list shapes with `score: float (clamped to [0,1])`. Response wrappers `JobSearchResponse` / `CVSearchResponse` are `{items, total}` with `total = len(items)` (post-`top_k`).

## Applications (`/api/applications`)

### `POST /api/applications/`
- Request body: `CreateApplicationRequest`
- Success `200`:
```json
{
  "success": true,
  "data": {
    "app_id": 1,
    "job_id": 100,
    "candidate_id": 1,
    "cv_id": 10,
    "status": "pending",
    "created_at": "2026-04-21T00:00:00Z"
  }
}
```
- Errors:
  - `400` validation/business rule error
  - `500` unexpected error

### `GET /api/applications/job/{job_id}`
- Path params: `job_id: int`
- Query params:
  - `status: str | null` (optional; one of `pending|viewed|interviewing|rejected|hired`)
  - `limit: int` (default `50`, range `1..100`)
  - `skip: int` (default `0`, min `0`)
- Success `200`:
```json
{
  "success": true,
  "data": {
    "total": 12,
    "limit": 50,
    "skip": 0,
    "applications": [
      {
        "app_id": 1,
        "candidate_id": 1,
        "cv_id": 10,
        "status": "pending",
        "created_at": "2026-04-21T00:00:00Z"
      }
    ]
  }
}
```
- Errors:
  - `400` invalid status
  - `500` unexpected error

### `GET /api/applications/candidate/{candidate_id}`
- Path params: `candidate_id: int`
- Query params:
  - `status: str | null` (optional; one of `pending|viewed|interviewing|rejected|hired`)
  - `limit: int` (default `50`, range `1..100`)
  - `skip: int` (default `0`, min `0`)
- Success `200`:
```json
{
  "success": true,
  "data": {
    "total": 8,
    "limit": 50,
    "skip": 0,
    "applications": [
      {
        "app_id": 1,
        "job_id": 100,
        "cv_id": 10,
        "status": "pending",
        "created_at": "2026-04-21T00:00:00Z"
      }
    ]
  }
}
```
- Errors:
  - `400` invalid status
  - `500` unexpected error

### `PATCH /api/applications/{app_id}/status`
- Path params: `app_id: int`
- Request body: `UpdateApplicationStatusRequest`
- Success `200`:
```json
{
  "success": true,
  "data": {
    "app_id": 1,
    "status": "interviewing",
    "updated_at": "2026-04-21T00:00:00Z"
  }
}
```
- Errors:
  - `400` invalid status or app not found
  - `500` unexpected error

### `DELETE /api/applications/{app_id}`
- Path params: `app_id: int`
- Intended success response shape:
```json
{
  "success": true,
  "message": "Application deleted successfully",
  "data": {}
}
```
- Runtime status note:
  - `ApplicationService.delete_application` is currently missing, so this route raises internal error at runtime.
  - Treat as unstable until service implementation is added.

## System (`/api`)

### `GET /api/health`
- Success `200`:
```json
{ "status": "ok" }
```

## Non-API Root Route

### `GET /`
- Success `200`:
```json
{ "message": "Welcome to Job Matcher API" }
```

## Known Contract/Runtime Drift
- `DELETE /api/applications/{app_id}` is exposed in router but current service implementation is missing (`ApplicationService.delete_application`), so runtime behavior does not match intended contract.

## Related LLD
- Router behavior and error patterns: `../runtime/router-contract-and-error-patterns.md`
- Application delete drift note: `../applications/application-delete-flow-drift-note.md`
