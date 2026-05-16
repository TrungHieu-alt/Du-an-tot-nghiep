# Recruiter Application Management Specification

Status: production-like MVP planning  
Priority: Core MVP  
Documentation language: English  
Visible UI copy: Vietnamese

## 1) Purpose

Provide the recruiter workspace for reviewing applications by job, changing
application status, and inspecting the event timeline for each application.

## 2) Backend Alignment

Primary endpoints:

- `GET /api/applications?job_id=&status=&limit=&offset=`
- `GET /api/applications/{application_id}`
- `POST /api/applications/{application_id}/status`
- `GET /api/jobs`
- `GET /api/jobs/{job_id}`

Required production response fields:

- Application list items must include denormalized display data:
  - `application_id`, `status`, `applied_at`, `updated_at`
  - `job_summary`: title, organization name/logo, status
  - `resume_summary`: title, candidate display name when allowed, location,
    job type, seniority
- Application detail must include the same summaries plus
  `ApplicationDetail.events`.
- This denormalization is required for FE speed and table stability; do not
  make the table fetch job/resume details per row.

Allowed recruiter transitions:

- `submitted -> shortlisted | rejected | hired`
- `shortlisted -> rejected | hired`
- terminal `rejected | hired | withdrawn` cannot move further

## 3) Layout

- Top toolbar:
  - job selector
  - status filter
  - compact search-by-visible-text client filter for the loaded page only
- Main body:
  - application table grouped by selected job
  - row actions for allowed status changes
- Detail drawer or route:
  - application facts
  - linked job summary
  - linked resume summary when the recruiter has permission
  - event timeline from `ApplicationDetail.events`

## 4) Vietnamese UI Copy

| UI element | Copy |
|---|---|
| Page title | `Quản lý ứng tuyển` |
| Job selector label | `Tin tuyển dụng` |
| Status filter label | `Trạng thái` |
| Empty title | `Chưa có hồ sơ ứng tuyển` |
| Empty body | `Khi ứng viên ứng tuyển hoặc chấp nhận lời mời, hồ sơ sẽ xuất hiện tại đây.` |
| Shortlist action | `Đưa vào danh sách chọn` |
| Reject action | `Từ chối` |
| Hire action | `Tuyển dụng` |
| Timeline title | `Lịch sử trạng thái` |
| Invalid transition message | `Trạng thái hiện tại không cho phép thao tác này.` |
| Success message | `Đã cập nhật trạng thái ứng tuyển.` |

## 5) States

- `loading`
- `success`
- `empty`
- `filter_empty`
- `updating_status`
- `update_success`
- `update_error_invalid_transition`
- `session_expired`
- `forbidden`
- `not_found`
- `error_network`
- `error_server`

## 6) Interaction Rules

- Recruiter can see only applications for their own jobs through the API
  visibility boundary.
- Disable status actions that are not valid for the current application status.
- If the backend still returns `409 invalid_transition`, refresh application
  detail and show the invalid transition message.
- Every status change must append a timeline event after refresh.
- Closed jobs remain readable, but status actions should be disabled if backend
  rejects downstream mutations.

## 7) Acceptance Checklist

- Recruiter can filter applications by job and status.
- Invalid transitions are blocked in the UI and still handled from backend `409`.
- Application detail shows event timeline.
- Vietnamese copy is used for all visible controls and feedback.
