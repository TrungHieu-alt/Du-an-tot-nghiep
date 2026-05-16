# Talent Market Screen Specification (Recruiter)

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide a recruiter-facing candidate discovery screen.
- Keep search behavior explicit with two distinct modes:
  - `Exact`
  - `Semantic`
- Keep results actionable for invite and matching flows.
- Serve as the recruiter-side matching result surface.

## 2) Backend/DB Alignment

Primary endpoints:

- `GET /api/candidate/resumes/search` (exact/keyword mode)
- `POST /api/candidate/resumes/semantic-search` (embedding mode)
- `POST /api/matching/jobs/{job_id}/run` (recruiter match mode)
- `POST /api/invites`

Current runtime behavior detail:

- Exact search `q` currently matches resume title and skills.
- Candidate avatar is not part of current DB/API contract and is intentionally
  not used in this screen.

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
  - candidate resume result list
- Optional right-side panel (later phase):
  - shortlisting/compare actions

No heavy coaching modules in MVP.

## 4) Search Modes

## 4.1 Exact Mode

- Endpoint: `GET /api/candidate/resumes/search`
- Input: `q`, `location`, `job_type`, `seniority`, `limit`, `offset`.
- UX:
  - one-line search input
  - pagination or load-more behavior

## 4.2 Semantic Mode

- Endpoint: `POST /api/candidate/resumes/semantic-search`
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

- direct `matching_score` filter on this page (use matching run flow for score
  threshold control via `min_score`).

## 6) Resume Card Content

Required:

- resume title
- candidate display name if available from permitted API surface
- `location`
- `job_type`
- `seniority`
- `education`
- skills preview (compact)

No avatar/photo rendering in MVP.

## 7) Recruiter Actions

Primary actions per card:

- `Open Resume Detail`
- `Invite Candidate` (where flow permissions allow)

Page-level action:

- `Run Matching from Job`

Rule:

- actions must honor ownership and visibility constraints from backend.

## 8) JD Improvement Hook (Design-Ready)

Future enhancement hook:

- action: `Improve JD Quality`
- output categories:
  - hard-filter strictness/conflict warnings
  - skill requirement clarity
  - requirement measurability suggestions

## 9) States

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
- `selecting_job`
- `matching_running`
- `matching_results_ready`
- `matching_no_results_above_threshold`
- `matching_error`

## 10) Interaction Rules

- Mode switch preserves current typed query when possible.
- Filter changes trigger refetch for active mode.
- Clearing filters resets to default list for active mode.
- Result click navigates to dedicated Resume Detail page route.
- Clicking `Run Matching from Job` opens a published JD/job selector, then keeps
  user on Talent Market and renders ranked matching results in-page.

## 10.1 In-Screen Matching Flow

- Anchor: selected published recruiter-owned job.
- API: `POST /api/matching/jobs/{job_id}/run` with `top_k`, `min_score`.
- Entry points:
  - user clicks page-level `Run Matching from Job` and chooses one published JD.
  - another screen redirects here with `match_job_id`; validate that the job is
    published and recruiter-owned before running.
- Output mode:
  - switch local view from `search_results` to `matching_results` without route
    change.
- Matching results show rank, final score, compact score breakdown, reasoning,
  open resume action, and invite action.

## 10.2 Route Connectivity

- `Talent Market` -> `Resume Detail` (on row click / view action)
- `Talent Market` -> `Job Detail` (from context actions when recruiter inspects
  anchor job)
- `Job Detail` -> `Talent Market` with `match_job_id` when recruiter runs
  matching from a published job.
- Returning from detail pages restores:
  - active mode (`Exact`/`Semantic`)
  - query/filter state
  - matching sub-view state when present

## 11) Acceptance Checklist

- Screen has explicit `Exact` and `Semantic` search modes.
- MVP filters are limited to location/job_type/seniority.
- Resume cards render core fields consistently.
- No candidate avatar/face logic appears in this screen.
- State coverage includes loading/empty/error/session-expired.
- Matching always uses a selected published recruiter-owned JD/job as the
  backend anchor.

## 12) Production Vietnamese UI Copy

- Page title: `Kho ứng viên`
- Exact mode: `Tìm chính xác`
- Semantic mode: `Tìm theo ngữ nghĩa`
- Search placeholder: `Tìm theo chức danh, kỹ năng hoặc kinh nghiệm`
- Active-only label: `Chỉ hiển thị CV đang hoạt động`
- Open resume CTA: `Mở CV`
- Run matching CTA: `Chạy matching từ tin tuyển dụng`
- Invite CTA: `Mời ứng tuyển`
- Empty title: `Chưa có ứng viên phù hợp`
- Empty body: `Thử thay đổi từ khóa hoặc bộ lọc tìm kiếm.`
- Duplicate invite: `Ứng viên đã có lời mời đang chờ cho công việc này.`
- Invite success: `Đã gửi lời mời ứng tuyển.`

Production behavior:

- Recruiters see only active resumes from public search/matching APIs.
- Contact fields remain hidden unless a later application/invite visibility
  policy explicitly exposes them.
