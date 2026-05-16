# Job Market Screen Specification (Candidate)

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide a simple candidate-facing job discovery screen.
- Serve as the primary candidate workspace entry in MVP.
- Keep search behavior explicit with two distinct modes:
  - `Exact`
  - `Semantic`
- Serve as the candidate-side matching result surface.
- Keep surface data-first and low-noise.

## 2) Backend/DB Alignment

Primary endpoints:

- `GET /api/jobs/search` (exact/keyword mode)
- `POST /api/jobs/semantic-search` (embedding mode)
- `POST /api/matching/resumes/{resume_id}/run` (candidate match mode)
- `POST /api/applications`

Current agreed exact-search UX policy for this screen:

- User-facing copy should position exact search around job title and company.
- Runtime currently matches `title`, `skills`, and organization name; this is
  acceptable for now but should be tracked as behavior detail.
- Production FE requires job list/search/semantic responses to include
  `organization_name`, `organization_logo_url`, and optionally
  `organization_slug` so cards do not need N+1 organization fetches.

Filter enums must follow backend values:

- `location`: `ha_noi | tp_hcm | da_nang`
- `job_type`: `remote | fulltime | parttime`
- `seniority`: `intern | fresher | junior | mid | senior | lead`

## 3) Layout

- Top toolbar:
  - mode switch (`Exact` / `Semantic`)
  - search input
  - compact filter controls
- Main body:
  - job result list
- Inline/side result region for matching run output (same screen context)
- Optional right-side panel (later phase): CV improvement hints for selected job

No heavy side modules in MVP.

## 4) Search Modes

## 4.1 Exact Mode

- Endpoint: `GET /api/jobs/search`
- Input: `q`, `location`, `job_type`, `seniority`, `status?` (if needed),
  `limit`, `offset`.
- UX:
  - one-line search input
  - pagination or load-more behavior

## 4.2 Semantic Mode

- Endpoint: `POST /api/jobs/semantic-search`
- Input:
  - `query`
  - `top_k`
  - `filters`: `location`, `job_type`, `seniority`
- UX:
  - same visible filter controls as exact mode
  - result cards may show `relevance_score`

## 5) Filters (MVP)

- `location`
- `job_type`
- `seniority`

Deferred:

- direct `matching_score` filter on this page (not currently part of jobs search
  contract).

## 6) Job Card Content

Required:

- `title`
- company name
- `location`
- `job_type`
- `seniority`
- `education` (compact display)
- publish/status hint when available

Company logo:

- Required source: `organization_logo_url` in `JobSummary` for list/search and
  semantic-search responses.
- If logo is null, render a neutral organization placeholder.
- Do not fetch each organization individually just to render the list.

Actions:

- `Apply`
- `View Detail`
- page-level `Run Matching`

## 7) CV Improvement Hook (Design-Ready)

Candidate-side hook for future enhancement:

- action: `Improve CV for this job`
- output categories:
  - hard-filter gaps
  - skill gaps
  - summary/experience clarity gaps

Rule:

- suggestions update draft CV flow only; never auto-overwrite active resume.

## 8) States

- `idle`
- `loading`
- `success`
- `empty`
- `error_network`
- `error_server`
- `session_expired`
- `forbidden`

Mode-specific:

- `semantic_no_relevance_hits`
- `matching_running`
- `matching_results_ready`
- `matching_no_results_above_threshold`
- `matching_error`

## 9) Interaction Rules

- Mode switch preserves current typed query when possible.
- Filter changes trigger refetch for active mode.
- Clearing filters resets to default list for active mode.
- Result click navigates to dedicated Job Detail page route.
- Clicking `Run Matching` opens an active-CV selector, then keeps user on Job
  Market and renders ranked matching results in-page.
- Matching region should show:
  - rank order
  - final score
  - score breakdown/reasoning summary (compact)
  - action to open matched job detail
  - action to apply with the selected active CV

## 9.1 In-Screen Matching Flow

- Anchor: selected active owned resume.
- API: `POST /api/matching/resumes/{resume_id}/run` with `top_k`, `min_score`.
- Entry points:
  - user clicks page-level `Run Matching` and chooses one active CV.
  - another screen redirects here with `match_resume_id`; validate that the
    resume is active and owned before running.
- Output mode:
  - switch local view from `search_results` to `matching_results` without route
    change.
- Back behavior:
  - user can return to original search results with previous query/filter state
    preserved.

## 9.2 Route Connectivity

- `Job Market` -> `Job Detail` (on row click / view action)
- `Resume Detail` -> `Job Market` with `match_resume_id` when candidate runs
  matching from an active CV.
- Returning from detail pages restores:
  - active mode (`Exact`/`Semantic`)
  - query/filter state
  - matching sub-view state when present

## 10) Acceptance Checklist

- Screen has explicit `Exact` and `Semantic` search modes.
- Screen is treated as the canonical `Workspace` for candidate-side MVP entry.
- MVP filters are limited to location/job_type/seniority.
- Job cards render core fields consistently.
- Company logo slot exists with fallback when logo data is missing.
- No candidate avatar/face logic appears in this screen.
- State coverage includes loading/empty/error/session-expired.
- Matching results are rendered inside Job Market after `Run Matching` (no
  separate matching-results screen required for MVP).
- Matching always uses a selected active owned CV as the backend anchor.
- Job cards show organization name/logo from the list response contract.

## 11) Production Vietnamese UI Copy

- Page title: `Việc làm`
- Exact mode: `Tìm chính xác`
- Semantic mode: `Tìm theo ngữ nghĩa`
- Search placeholder: `Tìm theo vị trí, công ty hoặc kỹ năng`
- Run matching CTA: `Chạy matching`
- Apply CTA: `Ứng tuyển`
- View detail CTA: `Xem chi tiết`
- Empty title: `Chưa có công việc phù hợp`
- Empty body: `Thử thay đổi từ khóa hoặc bộ lọc tìm kiếm.`
- No active resume title: `Chưa có CV đang hoạt động`
- No active resume body: `Kích hoạt một CV để nhận kết quả matching và ứng tuyển.`
- Duplicate apply: `Bạn đã ứng tuyển công việc này bằng CV đã chọn.`
- Apply success: `Đã gửi hồ sơ ứng tuyển.`
- Matching invalid anchor: `CV cần được kích hoạt trước khi chạy matching.`

Production behavior:

- Candidate can apply only with an active owned resume to a published job.
- After successful apply, show success feedback and offer `Xem ứng tuyển` to
  open My Activity.
