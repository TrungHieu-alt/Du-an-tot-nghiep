# Current API Implementation Matrix

## Purpose

This document records the API surface currently implemented in
`backend/src/jobconnect/modules/api/router.py` and compares it with the target
contract in `docs/backend/LLD/40-api-contract.md`.

Use this as an implementation reference while redesigning the production API. Do
not treat it as the final architecture contract.

## Sources

- Runtime app mount: `backend/src/jobconnect/main.py`
- Router registration: `backend/src/jobconnect/app.py`
- Monolithic API router: `backend/src/jobconnect/modules/api/router.py`
- Health router: `backend/src/jobconnect/modules/system/router.py`
- Database schema: `backend/db/migrations/001_production_mvp.sql`
- Target contract: `docs/backend/LLD/40-api-contract.md`
- Runtime flow HLD: `docs/backend/HLD/50-api-and-runtime-flows.md`
- Product requirements: `docs/REQUIREMENTS.md`

## Runtime Boundary

- FastAPI service root is `/`.
- Production API routers are mounted with base prefix `/api`.
- Legacy `/api/v2/prototype/*` routes are not mounted.
- Most business routes are implemented in one monolithic router file.
- API behavior currently uses direct SQL inside route handlers and helper
  functions.

## Contract Status Legend

| Status | Meaning |
|---|---|
| `Aligned` | Implemented endpoint exists and broadly matches the target contract. |
| `Partial` | Endpoint exists, but request or response shape, behavior, or provider depth is simplified. |
| `Drift` | Runtime behavior differs materially from the target contract. |
| `Runtime-only` | Implemented endpoint is runtime/system surface outside the product contract matrix. |

## Cross-Cutting Runtime Notes

| Area | Current implementation | Contract/design note |
|---|---|---|
| Auth | Custom HMAC JWT with `sub`, `role`, `iat`, `exp` (TTL via `JWT_TTL_SECONDS`, default 86400s). Expired tokens rejected with `expired_token`; tokens missing `exp` also rejected. | Aligned with target JWT session policy (Slice 1). Revocation list still future work. |
| Error envelope | `HTTPException` and validation errors are normalized into `{ "error": ... }`. | Broadly aligned with target error envelope. |
| Request validation | Pydantic models use `extra="forbid"`; PATCH endpoints mostly use full request models. | Target describes partial PATCH semantics for resumes/jobs; implementation currently behaves like replace/update with full body. |
| Pagination | Offset pagination with `limit` and `offset` on list endpoints. | Aligned. |
| Uploads | `POST /api/documents` accepts `multipart/form-data` and writes through the Storage adapter (`backend/src/jobconnect/integrations/storage/`). Default backend is `local` (filesystem under `STORAGE_LOCAL_ROOT`); cloud adapters slot in by implementing the same protocol. | Aligned (Slice 4). |
| Parsing | Document create/retry inserts `parse_jobs` rows only. No worker/provider parse execution appears in this router. | Target flow expects extraction, preprocessing, LLM parse, entity creation/update, embeddings. |
| Embeddings | Manual resume/job create and update write deterministic local hash embeddings. | Useful for local matching; provider-backed embedding lifecycle is still future work. |
| Matching rerank | Request has `rerank`, response always reports `rerank_ms: 0.0`; no reranker path. | Target allows optional rerank, but fallback deterministic scoring is acceptable. |
| Email | Notification rows use `email_delivery_status = queued`; no email provider call in this router. | Target requires basic email attempt and failure handling. |
| Admin | Admin endpoints are read-heavy; some admin reads audit access. | Aligned with MVP read-only admin stance. |

## System And Root

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/` | Public | none | `{ message }` | none | none | Runtime-only |
| `GET` | `/api/health` | Public | none | `{ status: "ok" }` | none | none | Runtime-only |

## Auth And Current User

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `POST` | `/api/auth/register` | Public | `RegisterRequest`: email, password, role | `AuthResponse`: access token, `expires_in`, user | Creates user; hashes password; issues JWT with `exp` | `users` insert | Aligned (Slice 1). |
| `POST` | `/api/auth/login` | Public | `LoginRequest`: email, password | `AuthResponse`: access token, `expires_in`, user | Verifies password; blocks disabled user; issues JWT with `exp` | `users` read | Aligned (Slice 1). |
| `POST` | `/api/auth/logout` | Authenticated | bearer token | `204 No Content` | none; client discards token | `users` read through auth dependency | Aligned for stateless token behavior. |
| `GET` | `/api/me` | Authenticated | bearer token | `MeResponse`: user + optional candidate_profile / recruiter_profile + organization | none | `users` read; `candidate_profiles` or `recruiter_profiles` + `organizations` read by role | Aligned (Slice 1). |

## Profiles And Organizations

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/candidate/profile` | candidate | bearer token | `CandidateProfile` | none | `candidate_profiles` read | Aligned (Slice 2): admin role removed; admin must use `/api/admin/users/{user_id}`. |
| `PUT` | `/api/candidate/profile` | candidate | `CandidateProfileRequest` | `CandidateProfile` | Upserts current candidate profile | `candidate_profiles` insert/update | Aligned. |
| `GET` | `/api/recruiter/profile` | recruiter | bearer token | `RecruiterProfile` | none | `recruiter_profiles` read | Aligned (Slice 2): admin role removed; admin must use `/api/admin/users/{user_id}`. |
| `PUT` | `/api/recruiter/profile` | recruiter | `RecruiterProfileRequest` | `RecruiterProfile` | Upserts current recruiter profile after organization check | `organizations` read; `recruiter_profiles` insert/update | Aligned. |
| `GET` | `/api/organizations` | authenticated | `q?`, `limit`, `offset` | paginated `Organization` | none | `organizations` read | Aligned (Slice 3): `q` matches name + slug (ILIKE). |
| `POST` | `/api/organizations` | recruiter, admin | `OrganizationRequest` | `Organization` | Creates organization; writes audit event | `organizations` insert; `audit_logs` insert | Partial: target says recruiter; runtime also allows admin. |
| `GET` | `/api/organizations/{organization_id}` | authenticated | organization id | `Organization` | none | `organizations` read | Aligned. |
| `PATCH` | `/api/organizations/{organization_id}` | recruiter (member), admin | full `OrganizationRequest` | `Organization` | Updates organization; writes audit event | `recruiter_profiles` read (recruiter only); `organizations` update; `audit_logs` insert | Aligned (Slice 2): recruiter must belong to the target organization (`recruiter_profiles.organization_id`); admin bypasses. Non-member recruiter → 404. |

## Candidate Resumes And Resume Search

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/candidate/resumes` | candidate, admin | `status?`, `limit`, `offset` | paginated `ResumeSummary` | none | `candidate_resumes` read | Partial: admin sees all; candidate sees own. |
| `POST` | `/api/candidate/resumes` | candidate | full `ResumeRequest` | `ResumeDetail` | Creates draft resume; upserts hash embeddings | `candidate_resumes` insert; `candidate_resume_embeddings` insert/update | Aligned for manual create; embedding is immediate local hash rather than async queue. |
| `GET` | `/api/candidate/resumes/search` | recruiter, admin | `q?`, `location?`, `job_type?`, `seniority?`, `limit`, `offset` | paginated `ResumeSummary` | none | `candidate_resumes` read | Partial: `q` searches title and skills, not candidate display name/email policy from target. |
| `POST` | `/api/candidate/resumes/semantic-search` | recruiter, admin | `SemanticSearchRequest` | `SemanticResumeSearchResponse` (items are `SemanticResumeItem` with `relevance_score`) | Computes query embedding | `candidate_resumes` read; `candidate_resume_embeddings` read | Aligned (Slice 3): explicit semantic response schema. |
| `GET` | `/api/candidate/resumes/{resume_id}` | candidate, recruiter, admin | resume id | `ResumeDetail` | none | `candidate_resumes` read | Partial: recruiter can read only active resumes; response shape does not apply separate recruiter privacy DTO. |
| `PATCH` | `/api/candidate/resumes/{resume_id}` | candidate | partial `ResumeUpdateRequest` | `ResumeDetail` | Updates owned resume; refreshes hash embeddings from merged row | `candidate_resumes` update; `candidate_resume_embeddings` insert/update | Aligned (Slice 3): true partial update via `exclude_unset`. Empty body returns current row unchanged. |
| `POST` | `/api/candidate/resumes/{resume_id}/activate` | candidate | resume id | `ResumeDetail` | Sets status active if `status in {draft, archived}`; writes audit event | `candidate_resumes` update; `audit_logs` insert | Aligned (Slice 3): enforces `RESUME_STATUS_TRANSITIONS['active']`; 409 otherwise. |
| `POST` | `/api/candidate/resumes/{resume_id}/archive` | candidate | resume id | `ResumeDetail` | Sets status archived if `status in {draft, active}`; writes audit event | `candidate_resumes` update; `audit_logs` insert | Aligned (Slice 3): enforces `RESUME_STATUS_TRANSITIONS['archived']`; 409 otherwise. |

## Jobs And Job Search

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/jobs` | authenticated active user | `status?`, `location?`, `job_type?`, `seniority?`, `q?`, `limit`, `offset` | paginated `JobSummary` | none | `job_posts` read | Aligned (Slice 3): list and search share the same filter helper. |
| `POST` | `/api/jobs` | recruiter, admin | full `JobRequest` | `JobDetail` | Creates draft job; upserts hash embeddings | `organizations` read; `job_posts` insert; `job_post_embeddings` insert/update | Partial: target says recruiter; runtime also allows admin. |
| `GET` | `/api/jobs/search` | authenticated active user | `q?`, `location?`, `job_type?`, `seniority?`, `status?`, `limit`, `offset` | paginated `JobSummary` | none | `job_posts` read; `organizations` read for q-name match | Aligned (Slice 3): `q` matches title, skills, AND organization name. |
| `POST` | `/api/jobs/semantic-search` | authenticated active user | `SemanticSearchRequest` | `SemanticJobSearchResponse` (items are `SemanticJobItem` with `relevance_score`) | Computes query embedding | `job_posts` read; `job_post_embeddings` read | Aligned (Slice 3): explicit semantic response schema. Relevance still uses title embedding only (Slice 7 ownership). |
| `GET` | `/api/jobs/{job_id}` | authenticated active user | job id | `JobDetail` | none | `job_posts` read | Aligned on visibility: candidates published only; recruiters own jobs; admins all. |
| `PATCH` | `/api/jobs/{job_id}` | recruiter (owner), admin | partial `JobUpdateRequest` | `JobDetail` | Updates job; refreshes hash embeddings from merged row | `job_posts` update; `job_post_embeddings` insert/update | Aligned (Slice 3): true partial update. |
| `POST` | `/api/jobs/{job_id}/publish` | recruiter (owner), admin | job id | `JobDetail` | Sets status published if `status == draft`; sets `published_at`; writes audit event | `job_posts` update; `audit_logs` insert | Aligned (Slice 3): enforces `JOB_STATUS_TRANSITIONS['published'] = {draft}`; 409 otherwise. |
| `POST` | `/api/jobs/{job_id}/close` | recruiter (owner), admin | job id | `JobDetail` | Sets status closed if `status in {draft, published}`; writes audit event | `job_posts` update; `audit_logs` insert | Aligned (Slice 3): enforces `JOB_STATUS_TRANSITIONS['closed'] = {draft, published}`; 409 otherwise. |

## Matching

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `POST` | `/api/matching/jobs/{job_id}/run` | recruiter (owner), admin | `MatchingRequest`: `top_k`, `min_score`, `rerank` | `MatchingResponse` with ranked resumes | Computes hard filters, scores, reasoning; no application/invite creation | `job_posts` read; `candidate_resumes` read; `job_post_embeddings` read; `candidate_resume_embeddings` read | Partial (Slice 2 closed ownership): recruiter must own the job anchor; admin bypasses. `rerank` still accepted but not executed (Slice 8). |
| `POST` | `/api/matching/resumes/{resume_id}/run` | candidate (owner), admin | `MatchingRequest`: `top_k`, `min_score`, `rerank` | `MatchingResponse` with ranked jobs | Computes hard filters, scores, reasoning; no application/invite creation | `candidate_resumes` read; `job_posts` read; `candidate_resume_embeddings` read; `job_post_embeddings` read | Partial (Slice 2 closed ownership): candidate must own the resume anchor; admin bypasses. `rerank` still accepted but not executed (Slice 8). |

## Documents And Parse Jobs

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `POST` | `/api/documents` | authenticated active user | `multipart/form-data`: `file` + form fields (`document_type`, optional `resume_id`/`job_id`) | `DocumentUploadResponse: { document: DocumentDetail, parse_job: ParseJobDetail }` | Streams file through Storage adapter; inserts document + queued parse job; writes audit event | object storage write; `uploaded_documents` insert; `parse_jobs` insert; `audit_logs` insert | Aligned (Slice 4): multipart upload via `LocalFilesystemStorage` (`STORAGE_BACKEND=local`). Rejects unsupported MIME (415) and oversize files (413). |
| `GET` | `/api/documents` | authenticated active user | `document_type?`, `parse_status?`, `limit`, `offset` | paginated `DocumentDetail` | none | `uploaded_documents` read; optional `parse_jobs` existence filter | Aligned for visible document listing. List rows leave `parse_jobs` empty by default (cost). |
| `GET` | `/api/documents/{document_id}` | owner or admin | document id | `DocumentDetail` with `parse_jobs: list[ParseJobDetail]` | none | `uploaded_documents` read; `parse_jobs` read | Aligned (Slice 4): detail includes linked parse jobs. |
| `GET` | `/api/documents/{document_id}/download-url` | owner or admin | document id | `DocumentDownloadUrlResponse: { download_url, expires_at }` | none | `uploaded_documents` read | Aligned (Slice 4): URL generated through Storage adapter; `expires_at` is ISO timestamp. Local adapter returns `local://<object_key>`; future cloud adapters will return presigned HTTPS URLs. |
| `GET` | `/api/documents/{document_id}/parse-jobs/{parse_job_id}` | owner or admin | document id, parse job id | `ParseJobDetail` | none | `uploaded_documents` read; `parse_jobs` read | Aligned (Slice 4): explicit response model. |
| `POST` | `/api/documents/{document_id}/parse-jobs` | owner or admin | document id | `ParseJobDetail` | Creates queued parse job retry; writes audit event | `uploaded_documents` read; `parse_jobs` insert; `audit_logs` insert | Aligned (Slice 4): retry audited as `parse_job_retried`. |

## Applications

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/applications` | candidate, recruiter, admin | `status?`, `job_id?`, `resume_id?`, `limit`, `offset` | paginated `ApplicationDetail` | none | `applications` read; `job_posts` read for visibility | Aligned for role-scoped listing. |
| `POST` | `/api/applications` | candidate | `ApplicationRequest`: job id, resume id, optional note | `ApplicationDetail` | Creates application; appends event; notifies recruiter; writes audit event | `candidate_resumes` read; `job_posts` read; `applications` insert; `application_events` insert; `notifications` insert; `audit_logs` insert | Aligned for apply flow. |
| `GET` | `/api/applications/{application_id}` | candidate, recruiter, admin | application id | `ApplicationDetail` with `events: list[ApplicationEvent]` | none | `applications` read; `application_events` read; `job_posts` read for visibility | Aligned (Slice 3): detail now includes event history; list endpoint keeps events empty for cost. |
| `POST` | `/api/applications/{application_id}/status` | authenticated active user | `ApplicationStatusRequest` | `ApplicationDetail` | Updates status; appends event; notifies candidate; writes audit event | `applications` read/update; `job_posts` read; `application_events` insert; `notifications` insert; `audit_logs` insert | Drift: runtime checks role and target status, but does not enforce full allowed transition graph or terminal-state lock. |

## Invites

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/invites` | candidate, recruiter, admin | `status?`, `job_id?`, `resume_id?`, `limit`, `offset` | paginated `InviteDetail` | none | `recruiter_invites` read; `job_posts` read for visibility | Aligned for role-scoped listing. |
| `POST` | `/api/invites` | recruiter | `InviteRequest`: job id, resume id, optional message | `InviteDetail` | Creates pending invite; notifies candidate; writes audit event. Rejects duplicate pending invite with 409 `duplicate_invite`. | `candidate_resumes` read; `job_posts` read; `recruiter_invites` read (dup check) + insert; `notifications` insert; `audit_logs` insert | Aligned (Slice 3). |
| `GET` | `/api/invites/{invite_id}` | candidate, recruiter, admin | invite id | `InviteDetail` | none | `recruiter_invites` read; `job_posts` read for visibility | Aligned. |
| `POST` | `/api/invites/{invite_id}/accept` | candidate | invite id | `InviteAcceptResponse: { invite, application }` | Sets invite accepted; notifies recruiter; writes audit event; creates or returns application | `recruiter_invites` read/update; `notifications` insert; `audit_logs` insert; `candidate_resumes` read; `job_posts` read; `applications` insert/read; `application_events` insert when new | Aligned (Slice 3): explicit response model. |
| `POST` | `/api/invites/{invite_id}/reject` | candidate | optional note | `InviteDetail` | Sets invite rejected; notifies recruiter; writes audit event | `recruiter_invites` read/update; `notifications` insert; `audit_logs` insert | Aligned. |

## Notifications

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/notifications` | authenticated active user | `status?`, `limit`, `offset` | paginated `NotificationDetail` | none | `notifications` read | Aligned. |
| `POST` | `/api/notifications/{notification_id}/read` | notification owner | notification id | `NotificationDetail` | Sets notification read | `notifications` update | Aligned. |
| `POST` | `/api/notifications/read-all` | authenticated active user | bearer token | `NotificationsReadAllResponse: { updated_count }` | Marks current user's unread notifications as read | `notifications` update | Aligned (Slice 3): key renamed from `updated` to `updated_count`. |

## Admin Monitoring

| Method | Path | Roles | Main input | Response | Side effects | DB touchpoints | Contract status |
|---|---|---|---|---|---|---|---|
| `GET` | `/api/admin/users` | admin | `role?`, `status?`, `q?`, `limit`, `offset` | paginated `UserSummary` | Writes admin monitoring audit event | `users` read; `audit_logs` insert | Aligned. |
| `GET` | `/api/admin/users/{user_id}` | admin | user id | `UserSummary` | Writes admin monitoring audit event | `users` read; `audit_logs` insert | Partial: target says detail with profile links and operational summary; runtime returns `UserSummary`. |
| `GET` | `/api/admin/documents` | admin | `limit`, `offset` | paginated `DocumentDetail` | Writes admin monitoring audit event | `uploaded_documents` read; `audit_logs` insert | Partial: target includes filters `document_type`, `parse_status`, `owner_user_id`; runtime does not. |
| `GET` | `/api/admin/parse-jobs` | admin | `status?`, `limit`, `offset` | paginated parse job details | Writes admin monitoring audit event | `parse_jobs` read; `audit_logs` insert | Partial: target includes `document_type?`; runtime does not. |
| `GET` | `/api/admin/applications` | admin | `status?`, `limit`, `offset` | paginated `ApplicationDetail` | none | `applications` read | Partial: target includes `job_id?`, `resume_id?`; runtime does not. |
| `GET` | `/api/admin/invites` | admin | `status?`, `limit`, `offset` | paginated `InviteDetail` | none | `recruiter_invites` read | Partial: target includes `job_id?`, `resume_id?`; runtime does not. |
| `GET` | `/api/admin/notifications` | admin | `status?`, `limit`, `offset` | paginated `NotificationDetail` | none | `notifications` read | Partial: target includes `user_id?`; runtime does not. |
| `GET` | `/api/admin/audit-logs` | admin | `event_type?`, `limit`, `offset` | paginated audit log dicts | none | `audit_logs` read | Partial: target includes `actor_user_id?`, `target_type?`, `target_id?`; runtime only supports `event_type?`. |

## Database Table Coverage By Workflow

| Workflow | Primary tables | Notes |
|---|---|---|
| Auth | `users` | Password hash is PBKDF2 SHA-256. JWT is stateless and custom. |
| Candidate profile | `candidate_profiles` | One row per candidate user. |
| Recruiter profile and organizations | `recruiter_profiles`, `organizations` | Organization ownership is not strongly enforced in update route. |
| Resumes | `candidate_resumes`, `candidate_resume_embeddings` | Manual create/update immediately writes hash embeddings. |
| Jobs | `job_posts`, `job_post_embeddings` | Manual create/update immediately writes hash embeddings. |
| Documents and parsing | `uploaded_documents`, `parse_jobs` | Parse jobs are queued metadata only in current router. |
| Matching and semantic search | `candidate_resumes`, `job_posts`, embedding tables | Matching iterates eligible public pool and applies hard filters before scoring. |
| Applications | `applications`, `application_events`, `notifications`, `audit_logs` | Apply and status update create events, notifications, and audit logs. |
| Invites | `recruiter_invites`, `applications`, `application_events`, `notifications`, `audit_logs` | Accept creates or returns an application. Reject creates no application. |
| Notifications | `notifications` | In-app rows exist; email provider is not implemented here. |
| Admin | Read tables plus optional `audit_logs` | Some admin read routes audit access; not all admin routes do. |

## Gap Impact Classification And Slice Mapping

Generated by Slice 0 Baseline Contract Audit. Each row pairs a contract gap
with the smallest API change classification (`none` / `non-breaking` /
`breaking`) and the target follow-up slice from
`docs/mvp-roadmap/slices.md`.

Classification rules:

- `none`: no client-visible API change required.
- `non-breaking`: additive change (new optional field, new endpoint, new
  optional filter, behavior tightening that adds 4xx errors only on illegal
  inputs) — existing happy-path clients keep working.
- `breaking`: request/response shape change, field rename/removal, required
  field removal, status-code change for valid requests, namespace migration.

### Auth, Session, And `/api/me` (Slice 1)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `POST /api/auth/register` | Response missing `expires_in`. | Add `expires_in` (seconds). | non-breaking |
| `POST /api/auth/login` | Response missing `expires_in`. | Add `expires_in` (seconds). | non-breaking |
| Auth tokens | JWT has no `exp`; expired tokens are accepted. | Embed `exp` and reject expired tokens. | non-breaking |
| `GET /api/me` | Returns `UserSummary` only. | Return user + role-specific bootstrap (candidate profile / recruiter profile + organization). | breaking |
| `POST /api/auth/logout` | Aligned for stateless behavior. | none. | none |

### Ownership And Authorization (Slice 2 — done 2026-05-16)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `GET /api/candidate/profile` | Admin allowed but reads own admin id. | Restrict to `candidate` only; admin uses `/api/admin/users/{user_id}`. | non-breaking |
| `GET /api/recruiter/profile` | Same admin id leakage. | Restrict to `recruiter` only. | non-breaking |
| `PATCH /api/organizations/{id}` | No recruiter ownership check. | Enforce recruiter is member of organization via `recruiter_profiles`; non-member → 404. | non-breaking |
| `POST /api/matching/jobs/{job_id}/run` | No recruiter ownership check on job. | Recruiter must own job (admin bypass). | non-breaking |
| `POST /api/matching/resumes/{resume_id}/run` | No candidate ownership check. | Candidate must own resume (admin bypass). | non-breaking |
| Disabled users | Needed global guard on protected active actions. | Confirmed: `require_roles` chains through `require_active`; all role-gated endpoints reject disabled. | non-breaking |

### API Contract Drift Cleanup (Slice 3 — done 2026-05-16)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `PATCH /api/candidate/resumes/{id}` | Requires full body. | Accept partial body. | non-breaking |
| `PATCH /api/jobs/{id}` | Requires full body. | Accept partial body. | non-breaking |
| `GET /api/organizations` | Missing `q?`. | Add optional `q`. | non-breaking |
| `GET /api/jobs` | Missing `location?`, `job_type?`, `seniority?`, `q?`. | Add optional filters. | non-breaking |
| `GET /api/jobs/search` | `q` only matches title/skills. | Extend to organization name. | non-breaking |
| `GET /api/candidate/resumes/search` | `q` semantics narrow. | Align with target field set. | non-breaking |
| `POST /api/candidate/resumes/semantic-search` | Generic `Paginated` response. | Explicit semantic result schema (`relevance_score`). | non-breaking |
| `POST /api/jobs/semantic-search` | Generic `Paginated` response. | Explicit semantic result schema. | non-breaking |
| `POST /api/notifications/read-all` | Returns `{ updated }`. | Return `{ updated_count }`. | breaking |
| `POST /api/organizations` | Allows admin. | Decide: keep admin or restrict to recruiter. | breaking if restricted |
| `POST /api/jobs` | Allows admin. | Decide: keep admin or restrict to recruiter. | breaking if restricted |
| `GET /api/applications/{id}` | Detail missing event history. | Include event list. | non-breaking |
| `POST /api/jobs/{id}/publish` `close` | No transition guard. | Enforce draft→published, published→closed. | non-breaking |
| `POST /api/candidate/resumes/{id}/activate` `archive` | No lifecycle conflict guard. | Add transition guard. | non-breaking |

### Document Upload Foundation (Slice 4 — done 2026-05-16)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `POST /api/documents` | Accepts JSON metadata for pre-uploaded file. | Accept `multipart/form-data` upload and return `{ document, parse_job }`. | breaking |
| `GET /api/documents/{id}/download-url` | Returns `expires_in_seconds`; may return `object://...`. | Return `expires_at` (ISO timestamp) and signed HTTPS URL. | breaking |
| `GET /api/documents/{id}` | Detail does not include linked parse jobs. | Include parse jobs array. | non-breaking |
| `POST /api/documents/{id}/parse-jobs` | No audit event. | Write audit on retry. | non-breaking |

### Parse Worker And LLM Adapter (Slices 5, 6)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| Parse pipeline | Parse jobs are queued metadata only; no worker execution. | Execute extraction → preprocess → LLM parse → entity create/update. | non-breaking (server-side) |
| LLM provider boundary | No adapter abstraction. | Introduce adapter with fallback per `provider-strategy.md`. | none (internal) |

### Embedding And Semantic Search (Slice 7)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| Resume/job embeddings | Local deterministic hash only. | Plug provider-backed embedding adapter; keep local fallback for dev/test. | non-breaking |
| `POST .../semantic-search` | Query embedding uses hash. | Use provider embeddings; preserve response schema. | non-breaking |

### Matching Production Hardening (Slice 8)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `POST /api/matching/jobs/{job_id}/run` | `rerank` ignored; `rerank_ms` always `0.0`. | Wire rerank path or document permanent fallback. | non-breaking |
| `POST /api/matching/resumes/{resume_id}/run` | Same. | Same. | non-breaking |

### Applications And Invites (Slice 9)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `POST /api/applications/{id}/status` | No full transition graph enforcement. | Enforce graph; reject terminal-state transitions. | non-breaking |
| `POST /api/invites` | No duplicate pending-invite guard. | Reject duplicate pending invite (409). | non-breaking |
| `POST /api/invites/{id}/accept` | Response shape has no explicit model. | Add explicit response model `{ invite, application }`. | non-breaking |
| Closed-job blocks | Not enforced for apply/invite/status. | Reject mutations against closed jobs. | non-breaking |

### Notifications, Email, Audit (Slice 10)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| Email delivery | Notifications stored with `email_delivery_status = queued`; no provider call. | Introduce email adapter; failure must not roll back transaction. | none (internal) |
| Audit consistency | Some admin reads audit; others do not. | Decide and apply consistent policy. | none |

### Admin Monitoring (Slice 11)

| Endpoint | Gap | Fix | Impact |
|---|---|---|---|
| `GET /api/admin/users/{id}` | Returns `UserSummary`. | Return detail with profile links + operational summary. | non-breaking |
| `GET /api/admin/documents` | Missing `document_type`, `parse_status`, `owner_user_id`. | Add optional filters. | non-breaking |
| `GET /api/admin/parse-jobs` | Missing `document_type?`. | Add. | non-breaking |
| `GET /api/admin/applications` | Missing `job_id?`, `resume_id?`. | Add. | non-breaking |
| `GET /api/admin/invites` | Missing `job_id?`, `resume_id?`. | Add. | non-breaking |
| `GET /api/admin/notifications` | Missing `user_id?`. | Add. | non-breaking |
| `GET /api/admin/audit-logs` | Missing `actor_user_id?`, `target_type?`, `target_id?`. | Add. | non-breaking |

### Impact Summary

| Impact | Count | Notes |
|---|---|---|
| `breaking` | 5 confirmed + 2 pending policy decision | `/api/me` shape, `POST /api/documents`, `GET .../download-url`, `POST /api/notifications/read-all`; policy decisions on `POST /api/organizations` and `POST /api/jobs` role scope. |
| `non-breaking` | ~30 | Mostly additive fields, filters, ownership tightening, partial PATCH, transition guards. |
| `none` | 5 | Stateless logout, get-org-by-id, list-resumes, list-jobs-by-id, basic notifications read. |

### Endpoints Not Yet Present In Runtime (Missing)

The router currently covers all named endpoints in the target contract surface
known to this audit. No fully missing endpoint was identified at the path
level. Coverage gaps that are server-side only (parse execution, real
embedding provider, email send) are tracked under their respective slices
above.

## Redesign Priority Notes

| Priority | Area | Reason |
|---|---|---|
| High | Document upload contract | Runtime JSON metadata endpoint differs from product upload flow and target multipart contract. |
| High | Auth/session policy | Current token lacks expiry/revocation behavior visible in implementation. |
| High | Ownership and role boundaries | Matching anchor ownership and organization update ownership should be explicit before frontend wiring. |
| High | PATCH semantics | Runtime uses full request bodies where target says partial updates. |
| High | Application status transitions | Runtime allows role-filtered target statuses but does not enforce complete transition graph. |
| Medium | Response schemas | Several endpoints return generic dicts or simplified details despite explicit target schemas. |
| Medium | Search behavior | Keyword search does not yet cover all identity/title fields described in requirements. |
| Medium | Admin filters | Several target filters are absent from runtime admin endpoints. |
| Medium | Parser, storage, email, rerank providers | Current implementation has queue/status placeholders and local deterministic helpers. |
| Low | Audit consistency | Some read-monitoring routes write audit logs while others do not. Decide policy. |
