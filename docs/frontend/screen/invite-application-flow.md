# Invite + Application Flow Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide one operational flow for candidate-facing:
  - applied jobs list
  - incoming invites list
- Ensure each list item navigates to dedicated detail pages.

## 2) Navigation Model (Required)

- Entry from navbar/user menu: `My Activity`.
- Recommended candidate IA placement:
  - primary workspace entry: `Job Market`
  - secondary activity entry: `My Activity`
- Internal tabs:
  - `Applied Jobs`
  - `Invites For Me`
- Item-level action:
  - `View Detail` must navigate to a dedicated detail route (not inline-only).

Route targets:

- job-focused detail: `job-detail`
- resume-focused detail (when needed by context/permissions): `resume-detail`

## 3) Backend Alignment

Primary endpoints:

- `GET /api/applications`
- `GET /api/invites`
- `GET /api/applications/{application_id}`
- `GET /api/invites/{invite_id}`
- `POST /api/invites/{invite_id}/accept`
- `POST /api/invites/{invite_id}/reject`

Required production response fields:

- Application list/detail items must include:
  - `application_id`, `job_id`, `resume_id`, `status`, `applied_at`,
    `updated_at`
  - `job_summary`: title, organization name/logo, location, job type,
    seniority
  - `resume_summary`: title and selected hard-filter fields
- Invite list/detail items must include:
  - `invite_id`, `job_id`, `resume_id`, `status`, `message`, `created_at`,
    `updated_at`
  - `job_summary`: title, organization name/logo, location, job type,
    seniority
  - `resume_summary`: title and selected hard-filter fields

These summaries are part of the application/invite API contract for FE speed.
Do not require the client to fetch every linked job and resume row by row.

## 4) List Views

## 4.1 Applied Jobs Tab

Each row should show:

- job title
- organization display name
- application status
- applied date
- resume title used for the application
- quick action: `View Detail`

## 4.2 Invites For Me Tab

Each row should show:

- job title
- organization display name
- invite status
- created date
- resume title targeted by the invite
- quick actions:
  - `View Detail`
  - `Accept` / `Reject` (when pending)

## 5) Detail Experience Rules

- Public/cross-user viewing should use clean read-focused detail layout.
- Owner self-management can include editable extracted fields and PDF/source view.
- Detail rendering should respect role/ownership visibility from backend.

## 6) State And Back Navigation

- Preserve active tab and list filters when returning from detail page.
- Preserve scroll position for usability on long lists.

States:

- `loading`
- `success`
- `empty`
- `error_network`
- `error_server`
- `session_expired`
- `forbidden`

## 7) Acceptance Checklist

- Candidate can switch between Applied and Invites tabs.
- Every `View Detail` action navigates to a dedicated detail page route.
- Returning from detail restores previous tab/filter/scroll state.
- Invite accept/reject actions update row state without breaking navigation.

## 8) Production Vietnamese UI Copy

- Page title: `Hoạt động của tôi`
- Applied tab: `Đã ứng tuyển`
- Invites tab: `Lời mời dành cho tôi`
- View detail CTA: `Xem chi tiết`
- Accept CTA: `Chấp nhận`
- Reject CTA: `Từ chối`
- Applied empty title: `Chưa có hồ sơ ứng tuyển`
- Applied empty body: `Ứng tuyển mới sẽ xuất hiện tại đây.`
- Invites empty title: `Chưa có lời mời`
- Invites empty body: `Lời mời từ nhà tuyển dụng sẽ xuất hiện tại đây.`
- Accept success: `Đã chấp nhận lời mời và tạo hồ sơ ứng tuyển.`
- Reject success: `Đã từ chối lời mời.`
- Invalid invite state: `Lời mời này không còn ở trạng thái chờ.`

Production behavior:

- Accept invite routes to the created or existing application detail.
- Reject note is optional.
