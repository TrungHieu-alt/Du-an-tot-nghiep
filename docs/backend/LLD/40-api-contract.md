# Production LLD: API Contract

## Purpose And Sources

This document defines the target production API contract for the recruiting
marketplace MVP. It is design documentation for implementation and OpenAPI
generation, not executable code.

Canonical sources:

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-matching-and-search-pipeline.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`
- `docs/backend/HLD/60-security-notifications-audit.md`
- `docs/backend/LLD/30-database-schema.md`

If this LLD conflicts with `docs/REQUIREMENTS.md`, the requirements document
wins.

## Contract Conventions

### Runtime Boundary

- Base path: `/api`.
- Production namespaces are under `/api`.
- This is a breaking API migration from the removed prototype runtime.
- IDs are `BIGINT` database identifiers and are represented as JSON numbers.
- Timestamps are ISO 8601 strings with timezone.
- Request and response schemas must be explicit in OpenAPI.
- Unknown request fields are rejected unless an endpoint explicitly allows
  metadata JSON.

### Authentication

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

The access token is a JWT. Disabled users cannot publish, activate, apply,
invite, or run matching.

### Canonical Enums

All enum-like fields must be represented in OpenAPI.

```text
role: candidate | recruiter | admin
user_status: active | invited | disabled
candidate_resume_status: draft | active | archived
job_post_status: draft | published | closed
application_status: submitted | shortlisted | rejected | hired | withdrawn
recruiter_invite_status: pending | accepted | rejected
parse_job_status: queued | processing | succeeded | failed
notification_status: unread | read
location: ha_noi | tp_hcm | da_nang
job_type: remote | fulltime | parttime
seniority: intern | fresher | junior | mid | senior | lead
education: lop_9 | lop_12 | dai_hoc | thac_si | tien_si
```

### Pagination, Sorting, And Filtering

List endpoints use offset pagination unless an endpoint says otherwise:

```text
limit: integer, default 20, min 1, max 100
offset: integer, default 0, min 0
```

List responses use:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

Structured filters use query parameters. Semantic search uses a request body.
Exact or keyword search and semantic search remain separate APIs.

### Standard Error Envelope

All non-validation and business errors use this envelope. Validation errors
should be normalized into the same envelope before production release.

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed.",
    "fields": {
      "email": "Invalid email address."
    },
    "request_id": "req_01hxyz"
  }
}
```

Standard status meanings:

| Status | Meaning |
|---|---|
| `400` | Invalid business request or invalid state transition |
| `401` | Missing or invalid JWT |
| `403` | Authenticated user lacks role, status, or ownership permission |
| `404` | Resource not found or not visible to the current user |
| `409` | Duplicate or conflicting lifecycle state |
| `413` | Uploaded file exceeds configured maximum size |
| `415` | Unsupported upload MIME type |
| `422` | Schema validation error |
| `500` | Unexpected server error |

### Common Resource Shapes

`UserSummary`

```json
{
  "user_id": 1,
  "email": "candidate@example.com",
  "role": "candidate",
  "status": "active",
  "created_at": "2026-05-14T10:00:00Z"
}
```

`CandidateResumeSummary`

```json
{
  "resume_id": 101,
  "title": "Backend Engineer",
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "mid",
  "education": "dai_hoc",
  "skills": ["python", "fastapi", "postgresql"],
  "certifications": [],
  "is_primary": true,
  "status": "active",
  "created_at": "2026-05-14T10:00:00Z",
  "updated_at": "2026-05-14T10:00:00Z"
}
```

`JobPostSummary`

```json
{
  "job_id": 201,
  "organization_id": 10,
  "organization_name": "Example Tech",
  "organization_logo_url": "https://example.com/logo.png",
  "organization_slug": "example-tech",
  "title": "Backend Engineer",
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "mid",
  "education": "dai_hoc",
  "skills": ["python", "fastapi", "postgresql"],
  "required_certifications": [],
  "status": "published",
  "published_at": "2026-05-14T10:00:00Z"
}
```

`organization_name`, `organization_logo_url`, and `organization_slug` are
included in job list/search/semantic responses so frontend job cards do not need
per-row organization detail fetches. `organization_logo_url` and
`organization_slug` are optional and may be `null`.

`ApplicationSummary`

Application list/detail responses include:
`application_id`, `job_id`, `candidate_user_id`, `resume_id`, `status`,
`applied_at`, `updated_at`, `job_summary`, and `resume_summary`.
The linked summaries are read models for FE table stability and must respect the
same role/privacy rules as the linked resource endpoints.

`InviteSummary`

Invite list/detail responses include:
`invite_id`, `job_id`, `resume_id`, `candidate_user_id`, `recruiter_user_id`,
`status`, `message`, `created_at`, `updated_at`, `job_summary`, and
`resume_summary`.

## Auth And Current User

### `POST /api/auth/register`

Roles: public.

Purpose: create a candidate, recruiter, or admin user account. Admin creation
may be restricted by deployment configuration.

Request:

```json
{
  "email": "candidate@example.com",
  "password": "password-value",
  "role": "candidate"
}
```

Response `201`:

```json
{
  "user": {
    "user_id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "status": "active",
    "created_at": "2026-05-14T10:00:00Z"
  },
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Errors: `400`, `409`, `422`.

Side effects: creates `users`; password is stored only as a secure hash.

### `POST /api/auth/login`

Roles: public.

Purpose: exchange email and password for a JWT.

Request:

```json
{
  "email": "candidate@example.com",
  "password": "password-value"
}
```

Response `200`:

```json
{
  "user": {
    "user_id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "status": "active",
    "created_at": "2026-05-14T10:00:00Z"
  },
  "access_token": "jwt",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Errors: `400`, `401`, `403`.

### `POST /api/auth/logout`

Roles: authenticated.

Purpose: allow clients to end the current session. If tokens are stateless, this
returns success and clients discard the token.

Response `204`: no body.

Errors: `401`.

### `GET /api/me`

Roles: authenticated.

Purpose: return the current account and any role-specific profile bootstrap
data.

Response `200`:

```json
{
  "user": {
    "user_id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "status": "active",
    "created_at": "2026-05-14T10:00:00Z"
  },
  "candidate_profile": {
    "user_id": 1,
    "full_name": "Nguyen Van A",
    "phone": "0900000000",
    "current_location": "ha_noi",
    "total_experience_years": 3,
    "headline": "Backend Engineer"
  },
  "recruiter_profile": null
}
```

Errors: `401`.

## Candidate Profile And Resumes

### `GET /api/candidate/profile`

Roles: candidate.

Purpose: read the current candidate profile.

Response `200`: candidate profile object.

Errors: `401`, `403`, `404`.

### `PUT /api/candidate/profile`

Roles: candidate.

Purpose: create or replace the current candidate profile.

Request:

```json
{
  "full_name": "Nguyen Van A",
  "phone": "0900000000",
  "current_location": "ha_noi",
  "total_experience_years": 3,
  "headline": "Backend Engineer"
}
```

Response `200`: candidate profile object.

Errors: `401`, `403`, `422`.

Side effects: upserts `candidate_profiles`.

### `GET /api/candidate/resumes`

Roles: candidate.

Purpose: list resumes owned by the current candidate.

Query: `status?`, `limit`, `offset`.

Response `200`: paginated `CandidateResumeSummary`.

Errors: `401`, `403`, `422`.

### `POST /api/candidate/resumes`

Roles: candidate.

Purpose: manually create a draft resume after review or without file upload.

Request:

```json
{
  "title": "Backend Engineer",
  "summary": "Builds APIs and data services.",
  "experience": "3 years with Python and PostgreSQL.",
  "skills": ["python", "fastapi", "postgresql"],
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "mid",
  "education": "dai_hoc",
  "certifications": [],
  "is_primary": false
}
```

Response `201`: candidate resume detail.

Errors: `401`, `403`, `422`.

Side effects: creates `candidate_resumes` with `status = draft`; embedding
generation may be queued if the implementation supports async indexing.

### `GET /api/candidate/resumes/{resume_id}`

Roles: candidate, recruiter, admin.

Purpose: read a resume detail. Candidates can read their own resumes.
Recruiters can read active resumes in the public pool. Admins can read all
resumes.

Response `200`: candidate resume detail.

Errors: `401`, `403`, `404`.

Privacy: recruiter-visible resume detail excludes candidate contact fields
unless an application or invite flow grants that visibility.

### `PATCH /api/candidate/resumes/{resume_id}`

Roles: candidate.

Purpose: update editable resume metadata and parsed fields.

Request: partial candidate resume fields except immutable IDs and owner.

Response `200`: candidate resume detail.

Errors: `400`, `401`, `403`, `404`, `422`.

Side effects: updates `candidate_resumes`; queues embedding refresh when fields
used for matching or semantic search change.

### `POST /api/candidate/resumes/{resume_id}/activate`

Roles: candidate.

Purpose: move a draft or archived resume into the public candidate pool.

Response `200`: candidate resume detail with `status = active`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `candidate_resumes.status = active`; active resumes become
eligible for public resume search and job -> resume matching; writes audit event
`resume_activated`.

### `POST /api/candidate/resumes/{resume_id}/archive`

Roles: candidate.

Purpose: remove a resume from the public candidate pool.

Response `200`: candidate resume detail with `status = archived`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `candidate_resumes.status = archived`; archived resumes are
excluded from public resume search and matching; writes audit event
`resume_archived`.

## Recruiter Profile, Organizations, And Jobs

### `GET /api/recruiter/profile`

Roles: recruiter.

Purpose: read the current recruiter profile.

Response `200`: recruiter profile object.

Errors: `401`, `403`, `404`.

### `PUT /api/recruiter/profile`

Roles: recruiter.

Purpose: create or replace the current recruiter profile.

Request:

```json
{
  "organization_id": 10,
  "full_name": "Tran Thi B",
  "title": "Technical Recruiter",
  "phone": "0900000001"
}
```

Response `200`: recruiter profile object.

Errors: `401`, `403`, `404`, `422`.

Side effects: upserts `recruiter_profiles`.

Independent organization rule:

- Recruiter onboarding supports a visible `Khác` / independent option.
- That option maps to one predefined `organizations` row for independent,
  freelance, or agency recruiters who do not belong to a named employer.
- The frontend must discover the real `organization_id` through bootstrap/config
  or organization lookup. It must not hard-code an environment-specific ID.
- If the predefined row is missing, the API should expose an operational setup
  error rather than accepting an invalid `organization_id`.

### `GET /api/organizations`

Roles: authenticated.

Purpose: browse organizations for recruiter profile setup and job display.

Query: `q?`, `limit`, `offset`.

Response `200`: paginated organization summaries.

The predefined Independent organization must be returned by this endpoint and
must be searchable by its canonical name/slug and by the Vietnamese UI label
`Khác` when the implementation supports alias search.

Errors: `401`, `422`.

### `POST /api/organizations`

Roles: recruiter.

Purpose: create an employer organization profile.

Request:

```json
{
  "name": "Example Tech",
  "slug": "example-tech",
  "logo_url": "https://example.com/logo.png",
  "about": "Software company."
}
```

Response `201`: organization detail.

Errors: `401`, `403`, `409`, `422`.

Side effects: creates `organizations`; writes audit event `organization_created`.

### `GET /api/organizations/{organization_id}`

Roles: authenticated.

Purpose: read organization detail.

Response `200`: organization detail.

Errors: `401`, `404`.

### `PATCH /api/organizations/{organization_id}`

Roles: recruiter.

Purpose: update organization profile fields for the recruiter's organization.

Response `200`: organization detail.

Errors: `401`, `403`, `404`, `409`, `422`.

Side effects: updates `organizations`; writes audit event
`organization_updated`.

### `GET /api/jobs`

Roles: authenticated.

Purpose: list jobs. Candidates see published jobs. Recruiters see their own
jobs, including draft and closed records. Admins see all jobs.

Query: `status?`, `location?`, `job_type?`, `seniority?`, `q?`, `limit`,
`offset`.

Response `200`: paginated `JobPostSummary`.

Every item must include `organization_name`, `organization_logo_url`, and
`organization_slug` from the linked organization. This is an additive response
contract used by `Job Market`, records tables, and application/invite summary
cards.

Errors: `401`, `422`.

### `POST /api/jobs`

Roles: recruiter.

Purpose: manually create a draft job post.

Request:

```json
{
  "organization_id": 10,
  "title": "Backend Engineer",
  "requirement": "Build APIs and data services.",
  "skills": ["python", "fastapi", "postgresql"],
  "location": "ha_noi",
  "job_type": "remote",
  "seniority": "mid",
  "education": "dai_hoc",
  "required_certifications": []
}
```

Response `201`: job detail.

Errors: `401`, `403`, `404`, `422`.

Side effects: creates `job_posts` with `status = draft`; embedding generation
may be queued if the implementation supports async indexing.

### `GET /api/jobs/{job_id}`

Roles: authenticated.

Purpose: read a job detail. Candidates can read published jobs. Recruiters can
read their own jobs. Admins can read all jobs.

Response `200`: job detail.

Errors: `401`, `403`, `404`.

### `PATCH /api/jobs/{job_id}`

Roles: recruiter.

Purpose: update an owned job while preserving lifecycle constraints.

Request: partial job fields except immutable IDs and owner fields.

Response `200`: job detail.

Errors: `400`, `401`, `403`, `404`, `422`.

Side effects: updates `job_posts`; queues embedding refresh when fields used for
matching or semantic search change.

### `POST /api/jobs/{job_id}/publish`

Roles: recruiter.

Purpose: move a draft job into the public job pool.

Response `200`: job detail with `status = published`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `job_posts.status = published` and `published_at` when first
published; published jobs become eligible for public job search and resume ->
job matching; writes audit event `job_published`.

### `POST /api/jobs/{job_id}/close`

Roles: recruiter.

Purpose: close a published or draft job.

Response `200`: job detail with `status = closed`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `job_posts.status = closed`; closed jobs are excluded from
public job search and matching and cannot receive new applications or invites;
writes audit event `job_closed`.

## Documents And Parse Jobs

### `POST /api/documents`

Roles: candidate, recruiter.

Purpose: upload an original CV or JD file and create an async parse job.

Content type: `multipart/form-data`.

Accepted MIME types: `application/pdf`; `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
only if DOCX extraction is enabled and tested.

Request fields:

```text
document_type: candidate_resume | job_post
file: binary
```

Response `201`:

```json
{
  "document": {
    "document_id": 301,
    "owner_user_id": 1,
    "document_type": "candidate_resume",
    "mime_type": "application/pdf",
    "file_size_bytes": 120000,
    "latest_parse_status": "queued",
    "created_at": "2026-05-14T10:00:00Z"
  },
  "parse_job": {
    "parse_job_id": 401,
    "document_id": 301,
    "target_entity_type": "candidate_resume",
    "resume_id": null,
    "job_id": null,
    "status": "queued",
    "error_message": null
  }
}
```

Errors: `400`, `401`, `403`, `413`, `415`, `422`.

Side effects: writes original file to object storage; creates
`uploaded_documents`; creates `parse_jobs` with `status = queued` and no linked
resume/job yet. The parse worker later extracts text, preprocesses text,
normalizes skills, runs structured parse, creates or updates the target
`candidate_resumes` or `job_posts` row, links the document and parse job to that
entity, and generates embeddings. `latest_parse_status` is a response-derived
field from the latest linked parse job, not a stored `uploaded_documents`
column.

### `GET /api/documents`

Roles: candidate, recruiter, admin.

Purpose: list visible uploaded documents. Candidates and recruiters see their
own documents. Admins see all documents.

Query: `document_type?`, `parse_status?`, `limit`, `offset`.

Response `200`: paginated document summaries.

Errors: `401`, `403`, `422`.

### `GET /api/documents/{document_id}`

Roles: candidate, recruiter, admin.

Purpose: read uploaded document metadata and parse status.

Response `200`: document detail with linked parse jobs.

Errors: `401`, `403`, `404`.

### `GET /api/documents/{document_id}/download-url`

Roles: owner, admin.

Purpose: return a short-lived URL for the original uploaded file.

Response `200`:

```json
{
  "download_url": "https://object-storage.example/signed-url",
  "expires_at": "2026-05-14T10:05:00Z"
}
```

Errors: `401`, `403`, `404`.

### `GET /api/documents/{document_id}/parse-jobs/{parse_job_id}`

Roles: owner, admin.

Purpose: read a specific parse job, actionable failure details, and parse review
payload when parsing succeeds.

Response `200`:

```json
{
  "parse_job_id": 401,
  "document_id": 301,
  "target_entity_type": "candidate_resume",
  "resume_id": 101,
  "job_id": null,
  "status": "succeeded",
  "error_message": null,
  "parser_version": "local-v1",
  "embedding_version_requested": "hash-v1",
  "extracted_text": "Candidate resume text...",
  "extracted_text_url": null,
  "review_payload": {
    "normalized_fields": {},
    "hard_filter_fields": {},
    "embedding_fields": {},
    "warnings": []
  },
  "created_at": "2026-05-14T10:00:00Z",
  "updated_at": "2026-05-14T10:01:00Z"
}
```

For `target_entity_type = candidate_resume`, `review_payload.normalized_fields`
uses the CV schema: `title`, `summary`, `experience`, `skills`, `location`,
`job_type`, `seniority`, `education`, and `certifications`.

For `target_entity_type = job_post`, `review_payload.normalized_fields` uses
the job schema: `title`, `requirement`, `skills`, `location`, `job_type`,
`seniority`, `education`, and `required_certifications`. The `embedding_fields`
targets are `title`, `skills`, and `requirement`.

`review_payload` also includes:

- `hard_filter_fields`: the subset requiring user confirmation.
- `embedding_fields`: target groups and embedding version/status metadata.
- `warnings`: parser warnings or confidence notes when available.

Review save path:

- CV review saves user corrections through
  `PATCH /api/candidate/resumes/{resume_id}`.
- JD review saves user corrections through `PATCH /api/jobs/{job_id}`.
- Activation and publishing remain separate lifecycle actions on the detail
  screens; saving review data must not automatically activate or publish.

Errors: `401`, `403`, `404`.

### `POST /api/documents/{document_id}/parse-jobs`

Roles: owner.

Purpose: retry parsing for a failed or corrected document.

Response `201`: parse job detail with `status = queued`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: creates a new `parse_jobs` row; writes audit event
`parse_job_retried`. If the later parse fails, create notification and attempt
email for parse failure; write audit event `parse_job_failed`.

## Search And Matching

### `GET /api/jobs/search`

Roles: candidate, recruiter, admin.

Purpose: exact or keyword job search for job title, organization name,
recruiter-visible organization metadata, and structured fields. Candidates only
see published jobs. Recruiters can search their own draft/published/closed jobs;
admins can search all jobs.

Query: `q?`, `location?`, `job_type?`, `seniority?`, `status?`, `limit`,
`offset`.

`q` matches job title and organization name. It may match recruiter profile
name/title only for admin responses; candidate-facing responses must not expose
or search private recruiter contact fields.

Response `200`: paginated `JobPostSummary`.

For job-list UIs, include `organization_name`, `organization_logo_url`, and
`organization_slug` when available so company branding can be rendered directly
in search results without N+1 organization fetches.

Errors: `401`, `403`, `422`.

### `POST /api/jobs/semantic-search`

Roles: candidate, recruiter, admin.

Purpose: semantic job search for description-style queries. Relevance score is
not the final matching score.

Request:

```json
{
  "query": "backend API work with PostgreSQL",
  "top_k": 20,
  "filters": {
    "location": "ha_noi",
    "job_type": "remote",
    "seniority": "mid"
  }
}
```

Response `200`:

```json
{
  "items": [
    {
      "job": {
        "job_id": 201,
        "organization_id": 10,
        "organization_name": "Example Tech",
        "organization_logo_url": "https://example.com/logo.png",
        "organization_slug": "example-tech",
        "title": "Backend Engineer",
        "location": "ha_noi",
        "job_type": "remote",
        "seniority": "mid",
        "education": "dai_hoc",
        "skills": ["python", "fastapi", "postgresql"],
        "required_certifications": [],
        "status": "published",
        "published_at": "2026-05-14T10:00:00Z"
      },
      "relevance_score": 0.82
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

Errors: `401`, `403`, `422`.

### `GET /api/candidate/resumes/search`

Roles: recruiter, admin.

Purpose: exact or keyword resume search over resume title, candidate display
name, and allowed candidate identity fields. Recruiters only see active resumes
in the public pool.

Query: `q?`, `location?`, `job_type?`, `seniority?`, `limit`, `offset`.

`q` matches resume title and candidate profile display name. Candidate email may
be searched only when permitted by role/privacy policy, such as admin
monitoring or a later application/invite visibility grant. Recruiter responses
must not include candidate email or phone unless that visibility has been
granted by the application/invite flow.

Response `200`: paginated public resume summaries.

Errors: `401`, `403`, `422`.

Privacy: candidate email and phone are not included unless a later application
or invite flow grants that visibility.

### `POST /api/candidate/resumes/semantic-search`

Roles: recruiter, admin.

Purpose: semantic resume search for capability-style queries. Relevance score is
not the final matching score.

Request:

```json
{
  "query": "fastapi postgresql backend engineer",
  "top_k": 20,
  "filters": {
    "location": "ha_noi",
    "job_type": "remote",
    "seniority": "mid"
  }
}
```

Response `200`: paginated public resume summaries with `relevance_score`,
`total`, `limit`, and `offset`.

Errors: `401`, `403`, `422`.

### `POST /api/matching/jobs/{job_id}/run`

Roles: recruiter, admin.

Purpose: anchor a published job and rank active candidate resumes.

Frontend integration: recruiter-facing matching results are rendered in
`Talent Market`. Job detail and records screens launch this endpoint by
redirecting to `Talent Market` with `match_job_id`; they do not render a
separate matching result page.

Request:

```json
{
  "top_k": 10,
  "min_score": 0.7,
  "rerank": false
}
```

Response `200`:

```json
{
  "anchor": {
    "type": "job",
    "job_id": 201,
    "status": "published"
  },
  "items": [
    {
      "rank": 1,
      "resume": {
        "resume_id": 101,
        "title": "Backend Engineer",
        "location": "ha_noi",
        "job_type": "remote",
        "seniority": "mid",
        "education": "dai_hoc",
        "skills": ["python", "fastapi", "postgresql"],
        "certifications": [],
        "status": "active"
      },
      "final_score": 0.86,
      "score_breakdown": {
        "title_sim": 0.8,
        "skills_sim": 0.9,
        "req_exp_sim": 0.84,
        "req_summary_sim": 0.7,
        "bonus_exact_skill": 0.0,
        "penalty_missing_required": 0.0
      },
      "exact_skill_overlap": ["python", "fastapi", "postgresql"],
      "hard_filter_notes": [
        "remote job skips location hard filter",
        "seniority matched",
        "education requirement satisfied"
      ],
      "reasoning": "Strong skill and title alignment with required backend stack.",
      "missing_embedding_notes": []
    }
  ],
  "runtime": {
    "total_ms": 35,
    "retrieval_ms": 4,
    "filter_ms": 5,
    "scoring_ms": 25,
    "rerank_ms": 1,
    "candidates_total": 120,
    "candidates_after_filter": 24,
    "rerank_applied": true,
    "warnings": []
  }
}
```

Errors: `400`, `401`, `403`, `404`, `422`.

Side effects: matching results are recommendations only; no application,
invite, notification, or audit row is created by the run itself. Operational
metrics record request count and latency.

### `POST /api/matching/resumes/{resume_id}/run`

Roles: candidate, admin.

Purpose: anchor an active resume and rank published jobs.

Frontend integration: candidate-facing matching results are rendered in
`Job Market`. Resume detail and records screens launch this endpoint by
redirecting to `Job Market` with `match_resume_id`; they do not render a
separate matching result page. A candidate must select one active owned resume
before this endpoint is called.

Request: same shape as job-anchor matching.
`rerank` is accepted for backward compatibility; runtime attempts rerank by
default and falls back to deterministic scoring if reranker is unavailable.

Response `200`: same shape as job-anchor matching with `anchor.type = resume`
and ranked jobs.

Errors: `400`, `401`, `403`, `404`, `422`.

Side effects: matching results are recommendations only; no application,
invite, notification, or audit row is created by the run itself. Operational
metrics record request count and latency.

## Applications

### `GET /api/applications`

Roles: candidate, recruiter, admin.

Purpose: list applications visible to the current user. Candidates see their
own applications. Recruiters see applications for their jobs. Admins see all.

Query: `status?`, `job_id?`, `resume_id?`, `limit`, `offset`.

Response `200`: paginated `ApplicationSummary` rows. List responses must include
linked `job_summary` and `resume_summary` display fields plus `applied_at` and
`updated_at`. The frontend must not fetch every linked job and resume row by row
to render application tables.

Errors: `401`, `403`, `422`.

### `POST /api/applications`

Roles: candidate.

Purpose: apply to a published job with an active resume.

Request:

```json
{
  "job_id": 201,
  "resume_id": 101
}
```

Response `201`: `ApplicationSummary`.

Errors: `400`, `401`, `403`, `404`, `409`, `422`.

Side effects: creates `applications` with `status = submitted`; appends
`application_events`; creates notification and attempts email for application
submitted; writes audit event `candidate_applied`. Duplicate `(job_id,
resume_id)` applications are rejected with `409`.

### `GET /api/applications/{application_id}`

Roles: candidate, recruiter, admin.

Purpose: read application detail and event history.

Response `200`: application detail with the same linked summaries as
`ApplicationSummary` plus `events`.

Errors: `401`, `403`, `404`.

### `POST /api/applications/{application_id}/status`

Roles: candidate, recruiter.

Purpose: transition application status.

Allowed transitions:

```text
recruiter: submitted -> shortlisted | rejected | hired
recruiter: shortlisted -> rejected | hired
candidate: submitted | shortlisted -> withdrawn
terminal: rejected | hired | withdrawn cannot move further
```

Request:

```json
{
  "status": "shortlisted",
  "note": "Strong backend match."
}
```

Response `200`: application detail with latest status, linked summaries, and
event history after refresh.

Invalid transition behavior:

- role-disallowed target status returns `403 forbidden`.
- state-disallowed target status returns `409 invalid_transition`.
- terminal statuses `rejected`, `hired`, and `withdrawn` never transition
  further.

Errors: `400`, `401`, `403`, `404`, `409`, `422`.

Side effects: updates `applications.status`; appends `application_events`;
creates notification and attempts email for application status changed; writes
audit event `application_status_changed`.

## Invites

### `GET /api/invites`

Roles: candidate, recruiter, admin.

Purpose: list recruiter invites visible to the current user. Candidates see
invites sent to their resumes. Recruiters see invites they sent. Admins see all.

Query: `status?`, `job_id?`, `resume_id?`, `limit`, `offset`.

Response `200`: paginated `InviteSummary` rows. List responses must include
linked `job_summary` and `resume_summary` display fields plus `created_at` and
`updated_at`.

Errors: `401`, `403`, `422`.

### `POST /api/invites`

Roles: recruiter.

Purpose: invite an active candidate resume to apply to a published job.

Request:

```json
{
  "job_id": 201,
  "resume_id": 101,
  "message": "We think this role may fit your backend experience."
}
```

Response `201`: `InviteSummary`.

Errors: `400`, `401`, `403`, `404`, `409`, `422`.

Side effects: creates `recruiter_invites` with `status = pending`; creates
notification and attempts email for invite sent; writes audit event
`recruiter_invite_sent`. Pending invite does not create an application.

### `GET /api/invites/{invite_id}`

Roles: candidate, recruiter, admin.

Purpose: read invite detail.

Response `200`: invite detail with linked job/resume summaries.

Errors: `401`, `403`, `404`.

### `POST /api/invites/{invite_id}/accept`

Roles: candidate.

Purpose: accept a pending recruiter invite.

Response `200`: `{ "invite": InviteSummary, "application": ApplicationSummary }`.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `recruiter_invites.status = accepted`; creates application
with `status = submitted` when no `(job_id, resume_id)` application exists;
appends `application_events` when an application is created; creates
notification and attempts email for invite accepted; writes audit event
`invite_accepted`.

Duplicate behavior: if the `(job_id, resume_id)` application already exists, the
endpoint still returns `200` with the accepted invite and the existing
application, without creating a second `applications` or `application_events`
row. Return `409` only when the invite is not pending or another lifecycle
state conflict prevents acceptance.

### `POST /api/invites/{invite_id}/reject`

Roles: candidate.

Purpose: reject a pending recruiter invite.

Request:

```json
{
  "note": "Not interested at this time."
}
```

Response `200`: invite detail with `status = rejected` and linked summaries.

Errors: `400`, `401`, `403`, `404`, `409`.

Side effects: sets `recruiter_invites.status = rejected`; creates notification
and attempts email for invite rejected; writes audit event `invite_rejected`.
Rejected invite creates no application.

## Notifications

### `GET /api/notifications`

Roles: authenticated.

Purpose: list notifications for the current user.

Query: `status?`, `limit`, `offset`.

Response `200`: paginated notifications.

Errors: `401`, `422`.

### `POST /api/notifications/{notification_id}/read`

Roles: owner.

Purpose: mark one notification as read.

Response `200`: notification detail with `status = read`.

Errors: `401`, `403`, `404`.

Side effects: updates `notifications.status = read`.

### `POST /api/notifications/read-all`

Roles: authenticated.

Purpose: mark all current-user unread notifications as read.

Response `200`:

```json
{
  "updated_count": 5
}
```

Errors: `401`.

Side effects: updates current user's unread notifications to `read`.

## Admin Read-Only Monitoring

Admin MVP is read-only unless requirements change.

### `GET /api/admin/users`

Roles: admin.

Purpose: monitor users by role and status.

Query: `role?`, `status?`, `q?`, `limit`, `offset`.

Response `200`: paginated `UserSummary`.

Errors: `401`, `403`, `422`.

### `GET /api/admin/users/{user_id}`

Roles: admin.

Purpose: read user detail with profile links and operational summary.

Response `200`: admin user detail.

```json
{
  "user": {
    "user_id": 1,
    "email": "candidate@example.com",
    "role": "candidate",
    "status": "active",
    "created_at": "2026-05-14T10:00:00Z"
  },
  "candidate_profile": null,
  "recruiter_profile": null,
  "organization": null,
  "ops_summary": {
    "resumes": 0,
    "jobs": 0,
    "applications": 0,
    "invites": 0,
    "documents": 0,
    "parse_failures": 0
  }
}
```

Errors: `401`, `403`, `404`.

### `GET /api/admin/documents`

Roles: admin.

Purpose: monitor uploaded documents and parse outcomes.

Query: `document_type?`, `parse_status?`, `owner_user_id?`, `limit`, `offset`.

Response `200`: paginated document summaries.

Errors: `401`, `403`, `422`.

### `GET /api/admin/parse-jobs`

Roles: admin.

Purpose: monitor parse queue status and failure reasons.

Query: `status?`, `document_type?`, `limit`, `offset`.

Response `200`: paginated parse job summaries.

Errors: `401`, `403`, `422`.

### `GET /api/admin/applications`

Roles: admin.

Purpose: monitor application lifecycle state.

Query: `status?`, `job_id?`, `resume_id?`, `limit`, `offset`.

Response `200`: paginated application summaries.

Errors: `401`, `403`, `422`.

### `GET /api/admin/invites`

Roles: admin.

Purpose: monitor recruiter invite lifecycle state.

Query: `status?`, `job_id?`, `resume_id?`, `limit`, `offset`.

Response `200`: paginated invite summaries.

Errors: `401`, `403`, `422`.

### `GET /api/admin/notifications`

Roles: admin.

Purpose: monitor notification creation and email delivery failures.

Query: `status?`, `user_id?`, `limit`, `offset`.

Response `200`: paginated notification summaries.

Errors: `401`, `403`, `422`.

### `GET /api/admin/audit-logs`

Roles: admin.

Purpose: inspect business audit events.

Query: `actor_user_id?`, `target_type?`, `target_id?`, `event_type?`, `limit`,
`offset`.

Response `200`: paginated audit log summaries.

Errors: `401`, `403`, `422`.

Side effects: may write audit event `admin_monitoring_access` if operationally
useful.

## Core Flow Endpoint Coverage

Candidate CV flow:

```text
register/login
  -> POST /api/documents
  -> GET /api/documents/{document_id}/parse-jobs/{parse_job_id}
  -> PATCH /api/candidate/resumes/{resume_id}
  -> POST /api/candidate/resumes/{resume_id}/activate
  -> POST /api/matching/resumes/{resume_id}/run
  -> POST /api/applications OR POST /api/invites/{invite_id}/accept
```

Recruiter JD flow:

```text
register/login
  -> PUT /api/recruiter/profile
  -> GET /api/organizations (or use predefined Independent organization)
  -> POST /api/organizations when creating a new employer profile
  -> POST /api/documents OR POST /api/jobs
  -> GET /api/documents/{document_id}/parse-jobs/{parse_job_id}
  -> PATCH /api/jobs/{job_id}
  -> POST /api/jobs/{job_id}/publish
  -> POST /api/matching/jobs/{job_id}/run
  -> POST /api/invites OR POST /api/applications/{application_id}/status
```

Search-first flow:

```text
GET /api/jobs/search
POST /api/jobs/semantic-search
GET /api/candidate/resumes/search
POST /api/candidate/resumes/semantic-search
GET /api/jobs/{job_id}
GET /api/candidate/resumes/{resume_id}
POST /api/matching/resumes/{resume_id}/run -> render in Job Market
POST /api/matching/jobs/{job_id}/run -> render in Talent Market
```

## OpenAPI Implementation Checklist

- Every route above has explicit request and response schemas.
- Canonical enum values are declared as reusable schema components.
- Bearer JWT security scheme is attached to every protected route.
- Upload limits and MIME types are documented on `POST /api/documents`.
- Parse job detail exposes parsed review payload, extracted text reference,
  parser metadata, embedding metadata, and target entity linkage.
- Job list/search/semantic schemas include organization name/logo/slug for
  direct card rendering.
- Matching responses include rank, final score, score breakdown, exact skill
  overlap, hard-filter notes, missing embedding notes, reasoning, and runtime.
- Application and invite mutation endpoints document allowed status
  transitions.
- Application and invite list/detail schemas include linked job/resume display
  summaries and timestamps for production frontend table rendering.
- Recruiter onboarding documents the predefined Independent organization used
  by the `Khác` option.
- Production `/api/*` rollout includes a breaking migration note from
  `/api/v2/prototype/*`.
