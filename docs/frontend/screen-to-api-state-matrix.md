# Screen To API And State Matrix

Status: production-like MVP planning  
Documentation language: English  
Visible UI copy: Vietnamese

This matrix is the frontend handoff source for routes, role gates, API usage,
state handling, and blocked actions. API field names and enum values stay in
canonical English; visible UI strings are Vietnamese.

| Screen | Route intent | Role | Primary APIs | Required states | Success navigation | Blocked/error handling |
|---|---|---|---|---|---|---|
| Auth | `/auth` | public | `POST /api/auth/login`, `POST /api/auth/register` | idle, submitting, field_error, auth_error, conflict_error, session_expired | Candidate missing profile -> Candidate Profile; candidate ready -> Job Market; recruiter missing profile -> Recruiter Profile; recruiter ready -> Talent Market; admin -> Admin Monitoring; `return_to` when valid | disabled login -> blocked page `Tài khoản đã bị khóa`; expired token -> `Phiên đăng nhập đã hết hạn...` |
| Candidate Profile Setup | `/candidate/profile/setup` | candidate | `GET /api/me`, `PUT /api/candidate/profile` | loading, typing, submitting, validation_error, success, network_error | Upload + Parse Review CV | field-level errors; missing `full_name` -> `Vui lòng nhập họ và tên.` |
| Recruiter Profile Setup | `/recruiter/profile/setup` | recruiter | `GET /api/me`, `GET /api/organizations?q=`, `PUT /api/recruiter/profile` | loading, searching_org, typing, submitting, validation_error, success | Upload + Parse Review JD or Records Jobs | missing organization -> `Vui lòng chọn tổ chức.`; non-member org update errors use forbidden/not-found shared states |
| Upload + Parse Review CV/JD | `/documents/upload?type=cv|jd` | candidate, recruiter | `POST /api/documents`, `GET /api/documents/{id}`, `GET /api/documents/{id}/parse-jobs/{parse_job_id}`, `POST /api/documents/{id}/parse-jobs`, `GET /api/documents/{id}/download-url`, reviewed entity save via `PATCH /api/candidate/resumes/{id}` or `PATCH /api/jobs/{id}` | idle, uploading, upload_error, parse_queued, parse_processing, parse_failed, parse_succeeded_review_required, review_validation_error, review_confirming, review_confirmed | CV -> Resume Detail; JD -> Job Detail | `413` in dropzone; `415` in dropzone; parse failed -> retry parse CTA and `Không thể phân tích tài liệu...`; parsed-field API extension is required before implementation |
| Resume Detail | `/candidate/resumes/:resume_id` | candidate owner, recruiter active-read, admin | `GET/PATCH /api/candidate/resumes/{id}`, `POST /activate`, `POST /archive`; match launch redirects to Job Market with `resume_id` context | loading, success, updating, update_error, not_found, forbidden, matching_launching, matching_error | Candidate Run Matching -> `/jobs?match_resume_id=:resume_id`; Back to previous list otherwise | Activate only draft/archived; Archive draft/active; inactive matching launch blocked before redirect; backend still handles `400 invalid_anchor` |
| Job Detail | `/jobs/:job_id` | candidate published-read, recruiter owner, admin | `GET/PATCH /api/jobs/{id}`, `POST /publish`, `POST /close`; recruiter match launch redirects to Talent Market with `job_id` context | loading, success, updating, update_error, not_found, forbidden, matching_launching, matching_error | Recruiter Run Matching -> `/talent?match_job_id=:job_id`; publish/close refreshes detail | Publish only draft; close draft/published; closed job blocks apply/invite/match launch through UI and backend |
| Job Market | `/jobs` | candidate | `GET /api/jobs/search`, `POST /api/jobs/semantic-search`, `POST /api/matching/resumes/{resume_id}/run`, `POST /api/applications`; requires job summary organization fields | idle, loading, success, empty, filter_empty, semantic_no_relevance_hits, selecting_resume, matching_running, matching_results_ready, apply_success, apply_error | Apply success -> My Activity Applied Jobs or stay with success toast; row click -> Job Detail; match results stay in Job Market | Match button opens active CV selector; no active resume -> empty CTA `Mở danh sách CV`; duplicate apply -> `Bạn đã ứng tuyển...` |
| Talent Market | `/talent` | recruiter | `GET /api/candidate/resumes/search`, `POST /api/candidate/resumes/semantic-search`, `POST /api/matching/jobs/{job_id}/run`, `POST /api/invites` | idle, loading, success, empty, filter_empty, semantic_no_relevance_hits, selecting_job, matching_running, matching_results_ready, invite_success, invite_error | Invite success updates row status; row click -> Resume Detail; match results stay in Talent Market | Match button opens published JD/job selector; active-only resume visibility label; duplicate invite -> `Ứng viên đã có lời mời...` |
| Records Management | `/records` | candidate, recruiter, admin | `GET /api/jobs`, `GET /api/candidate/resumes`, search and semantic endpoints by role | loading, success, empty, filter_empty, session_expired, forbidden | Open Detail routes; lifecycle shortcuts refresh row; match shortcuts redirect to Job Market or Talent Market with anchor context | row actions hidden when status/role disallows them |
| My Activity | `/activity` | candidate | `GET /api/applications`, `GET /api/invites`, `GET /api/applications/{id}`, `GET /api/invites/{id}`, `POST /api/invites/{id}/accept`, `POST /api/invites/{id}/reject`; requires list row display summaries | loading, success, empty, accepting, rejecting, action_error | Accept invite -> Application detail; Reject -> stays on Invites tab with updated row | reject note optional; non-pending invite -> `409 invalid_state` message |
| Recruiter Application Management | `/recruiter/applications` | recruiter | `GET /api/applications?job_id=&status=`, `GET /api/applications/{id}`, `POST /api/applications/{id}/status`; requires application display summaries and event timeline on detail | loading, success, empty, filter_empty, updating_status, update_error_invalid_transition | status change refreshes detail timeline | invalid transitions disabled in UI and handled from `409 invalid_transition` |
| Notifications | `/settings/notifications` or notification panel | authenticated active user | `GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all` | loading, success, empty, marking_read, error | remains on same screen | email delivery failure has no user-blocking fallback in MVP; business action remains successful |
| Account Settings | `/settings` | candidate, recruiter | `GET /api/me`, `PUT /api/candidate/profile`, `PUT /api/recruiter/profile`, notifications APIs, `POST /api/auth/logout` | loading, success, empty, error_validation, saving, session_expired | save stays in current subsection; logout -> Auth | unsupported settings are disabled, not persistable |
| Admin Monitoring | `/admin` | admin | all `/api/admin/*` endpoints | loading, success, empty, filter_empty, forbidden, not_found, error | list row -> detail when available | read-only only; non-admin -> forbidden shared state |

## Cross-Screen Acceptance Checks

- Every mutation action has a disabled state and a backend error fallback.
- Every list has `empty` and `filter_empty` states.
- Every protected screen handles `401`, `403`, and `404` using
  `screen/shared-states.md`.
- Vietnamese UI copy is used for all visible text.

## Required API Extensions For Production FE

- `JobSummary` in job list/search/semantic responses must include
  `organization_name`, `organization_logo_url`, and optionally
  `organization_slug`.
- Document parse detail must expose reviewed parsed fields, extracted text or
  extracted text URL, parser/embedding metadata, and enough target entity IDs to
  save reviewed CV/JD data without client-side guessing.
- Application and invite list/detail responses must include denormalized display
  summaries for linked job/resume/organization plus `applied_at`, `created_at`,
  and `updated_at` where relevant.
- Recruiter onboarding keeps the `Khác` organization option; DB seed/migration
  must provide the predefined Independent organization ID used by that option.
