# Job Detail Screen Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Show full job record for review and decision-making.
- Support publish/close lifecycle actions with clear status visibility.
- Reuse the same detail-screen structure used by Resume Detail.

## 2) Shared Detail Pattern (Reuse Contract)

This screen must reuse the same structural pattern as `resume-detail`:

- Header: title + status + primary actions
- Main content: grouped field sections
- Side panel: quick facts + lifecycle actions + matching shortcuts

Only field groups and action set differ by entity type.

Reuse scope with upload preview:

- Reuse field section and hard-filter render patterns from
  `upload-parse-review`.
- Keep detail-specific action rail independent from preview action flow.

## 3) Backend Alignment

Primary endpoints:

- `GET /api/jobs/{job_id}`
- `PATCH /api/jobs/{job_id}`
- `POST /api/jobs/{job_id}/publish`
- `POST /api/jobs/{job_id}/close`

Related:

- Recruiter matching is launched by redirecting to Talent Market with
  `match_job_id`. Talent Market owns the matching request and result rendering.

## 4) Layout

- Top header:
  - job title
  - status badge (`draft | published | closed`)
  - primary actions
- Main column:
  - requirement and skill content
  - hard-filter fields
  - metadata
- Right rail:
  - organization summary
  - lifecycle controls
  - matching shortcut

## 4.1 Entry Points And Back Navigation

Entry points:

- `Job Market` result click / view action
- `Records Management` jobs row `Open Detail`
- `Invite + Application` flow item `View Detail`

Back behavior:

- Return to previous list screen context with preserved tab/filter/scroll state.

## 5) Required Field Groups

- Core:
  - `title`
  - `requirement`
  - `skills`
- Hard filters:
  - `location`
  - `job_type`
  - `seniority`
  - `education`
  - `required_certifications`
- Lifecycle/meta:
  - `status`
  - `published_at`
  - `expires_at`
  - `organization_id`

## 6) Actions

- `Edit job` (patch flow)
- `Publish job` (from draft)
- `Close job` (from draft/published)
- `Run matching` (recruiter redirect to Talent Market)

All actions must reflect backend transition/role constraints.

## 7) States

- `loading`
- `success`
- `not_found`
- `forbidden`
- `error_network`
- `error_server`
- `updating`
- `update_success`
- `update_error`
- `matching_launching`
- `matching_launch_blocked`

## 8) Acceptance Checklist

- Uses shared detail-screen structure consistent with Resume Detail.
- Displays all required hard-filter fields clearly.
- Lifecycle actions reflect current status and allowed transitions.
- Matching shortcut is visible when allowed.

## 9) Production Vietnamese UI Copy

- Page title fallback: `Chi tiết tin tuyển dụng`
- Edit CTA: `Chỉnh sửa tin`
- Publish CTA: `Đăng tuyển`
- Close CTA: `Đóng tin`
- Run matching CTA: `Tìm ứng viên phù hợp`
- Draft status: `Bản nháp`
- Published status: `Đang đăng`
- Closed status: `Đã đóng`
- Publish success: `Tin tuyển dụng đã được đưa lên thị trường.`
- Close success: `Tin tuyển dụng đã đóng. Ứng viên không thể ứng tuyển và nhà tuyển dụng không thể gửi lời mời mới.`
- Invalid transition: `Trạng thái tin tuyển dụng hiện tại không cho phép thao tác này.`
- Embedding refresh hint: `Đang cập nhật dữ liệu matching.`

Production behavior:

- Show Publish only for `draft`.
- Show Close for `draft` and `published`.
- Show Apply/Invite-related entry points only when status is `published`.
- Show recruiter matching action only when status is `published`.
- Recruiter matching action routes to `/talent?match_job_id=:job_id`; Talent
  Market then calls `POST /api/matching/jobs/{job_id}/run` and renders results
  in the market context.
