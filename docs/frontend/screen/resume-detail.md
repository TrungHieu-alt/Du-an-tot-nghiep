# Resume Detail Screen Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Show full resume record for review and decision-making.
- Serve as the primary screen for candidate self CV adjustment in MVP.
- Support activate/archive lifecycle actions with clear status visibility.
- Reuse the same detail-screen structure used by Job Detail.

## 2) Shared Detail Pattern (Reuse Contract)

This screen must reuse the same structural pattern as `job-detail`:

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

- `GET /api/candidate/resumes/{resume_id}`
- `PATCH /api/candidate/resumes/{resume_id}`
- `POST /api/candidate/resumes/{resume_id}/activate`
- `POST /api/candidate/resumes/{resume_id}/archive`

Related:

- Matching is launched by redirecting to Job Market with `match_resume_id`.
  Job Market owns the matching request and result rendering.

## 4) Layout

- Top header:
  - resume title
  - status badge (`draft | active | archived`)
  - primary actions
- Main column:
  - summary and experience
  - skills and certifications
  - hard-filter fields
- Right rail:
  - candidate quick profile summary (text-only, no avatar logic)
  - lifecycle controls
  - matching shortcut

## 4.1 Entry Points And Back Navigation

Entry points:

- `Talent Market` result click / view action
- `Records Management` CV row `Open Detail`
- `Job Market` in-page matching result item (when deep view is allowed)

Back behavior:

- Return to previous list screen context with preserved tab/filter/scroll state.

## 5) Required Field Groups

- Core:
  - `title`
  - `summary`
  - `experience`
  - `skills`
  - `certifications`
- Hard filters:
  - `location`
  - `job_type`
  - `seniority`
  - `education`
- Lifecycle/meta:
  - `status`
  - `is_primary`

## 6) Actions

- `Edit resume` (patch flow)
- `Activate resume` (from draft/archived)
- `Archive resume` (from draft/active)
- `Run matching` (redirect to Job Market)

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

- Uses shared detail-screen structure consistent with Job Detail.
- Screen is the canonical destination for candidate-side CV adjustment.
- Displays all required hard-filter fields clearly.
- Lifecycle actions reflect current status and allowed transitions.
- No avatar/face extraction logic is required.

## 9) Production Vietnamese UI Copy

- Page title fallback: `Chi tiết CV`
- Edit CTA: `Chỉnh sửa CV`
- Activate CTA: `Kích hoạt CV`
- Archive CTA: `Lưu trữ CV`
- Run matching CTA: `Tìm việc phù hợp`
- Draft status: `Bản nháp`
- Active status: `Đang hoạt động`
- Archived status: `Đã lưu trữ`
- Save success: `Đã lưu CV.`
- Activate success: `CV đã được đưa vào kho ứng viên công khai.`
- Archive success: `CV đã được rút khỏi kho ứng viên công khai.`
- Invalid transition: `Trạng thái CV hiện tại không cho phép thao tác này.`
- Embedding refresh hint: `Đang cập nhật dữ liệu matching.`

Production behavior:

- Show Activate only for `draft` and `archived`.
- Show Archive for `draft` and `active`.
- Show matching action only when status is `active`.
- Matching action routes to `/jobs?match_resume_id=:resume_id`; Job Market then
  calls `POST /api/matching/resumes/{resume_id}/run` and renders results in
  the market context.
