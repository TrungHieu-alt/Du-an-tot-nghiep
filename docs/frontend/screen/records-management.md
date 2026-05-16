# Records Management Screen Specification (Jobs + CVs)

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide one secondary operational library screen to manage both:
  - job records
  - resume (CV) records
- Support fast list triage and navigation to detail screens.
- This screen is not the primary candidate workspace entry.

## 2) Backend Alignment

Jobs data:

- `GET /api/jobs`
- `GET /api/jobs/search`
- `POST /api/jobs/semantic-search` (when semantic mode is enabled)

CV data:

- `GET /api/candidate/resumes` (candidate own list)
- `GET /api/candidate/resumes/search` (recruiter/admin discovery list)
- `POST /api/candidate/resumes/semantic-search` (when semantic mode is enabled)

## 3) Layout

- Top controls:
  - record type switch: `Jobs` / `CVs`
  - search mode switch: `Exact` / `Semantic`
  - search input
  - compact filters
- Main body:
  - table/list of records
  - row-level quick actions

## 4) Data Views

## 4.1 Jobs View

Columns (compact):

- title
- organization (with logo slot when available)
- location
- job_type
- seniority
- status
- updated/published hint

## 4.2 CVs View

Columns (compact):

- title
- candidate display text (if available by role)
- location
- job_type
- seniority
- status
- updated hint

No avatar/face column in MVP.

## 5) Filters (MVP)

Shared:

- `location`
- `job_type`
- `seniority`

View-specific:

- jobs: `status` (`draft|published|closed`) when role allows
- CVs: `status` (`draft|active|archived`) for owner views

## 6) Row Actions

Jobs rows:

- `Open Detail`
- `Run Matching` (recruiter-owned published jobs only; redirect to Talent Market
  with `match_job_id`)
- lifecycle shortcut (`Publish`/`Close`) as allowed

CV rows:

- `Open Detail`
- `Run Matching` (candidate-owned active CVs only; redirect to Job Market with
  `match_resume_id`)
- lifecycle shortcut (`Activate`/`Archive`) as allowed

Navigation requirement:

- `Open Detail` always navigates to dedicated route:
  - jobs -> `job-detail`
  - CVs -> `resume-detail`

## 7) Reuse Rules

- Reuse the same result-row component shell for both Jobs and CVs.
- Reuse the same list-toolbar component shell (type switch, mode switch, query,
  filters).
- Route detail actions to shared-pattern detail screens:
  - `job-detail`
  - `resume-detail`

Back-navigation rule:

- Returning from detail restores the previous list context
  (record type tab, mode, filters, and scroll position).

## 8) States

- `loading`
- `success`
- `empty`
- `error_network`
- `error_server`
- `session_expired`
- `forbidden`

## 9) Acceptance Checklist

- One screen can switch between Jobs and CV records.
- Screen is positioned as a secondary library/operations view.
- Exact/Semantic mode is explicit and functional per record type.
- Shared filters remain minimal and enum-safe with backend.
- Row actions navigate to detail screens and respect role/status constraints.

## 10) Production Vietnamese UI Copy

- Page title: `Hồ sơ và tin tuyển dụng`
- Jobs tab: `Tin tuyển dụng`
- CVs tab: `CV`
- Exact mode: `Tìm chính xác`
- Semantic mode: `Tìm theo ngữ nghĩa`
- Open detail CTA: `Mở chi tiết`
- Run matching CTA: `Chạy matching`
- Publish shortcut: `Đăng tuyển`
- Close shortcut: `Đóng tin`
- Activate shortcut: `Kích hoạt`
- Archive shortcut: `Lưu trữ`
- Empty jobs title: `Chưa có tin tuyển dụng`
- Empty CVs title: `Chưa có CV`
- Filter empty body: `Không có kết quả phù hợp với bộ lọc hiện tại.`

Production behavior:

- Candidate CV view lists own resumes and highlights whether any resume is
  active.
- Recruiter Jobs view lists own draft/published/closed jobs and highlights
  which jobs can receive applications/invites.
- Records Management never renders matching results itself. It only launches
  matching in the correct market screen so users keep one canonical result
  surface per role.
