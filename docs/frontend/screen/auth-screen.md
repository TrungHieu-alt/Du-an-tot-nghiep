# Auth Screen Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide one unified auth entry with two modes:
  - `Login`
  - `Sign up`
- Keep the target visual format:
  - left auth form
  - right image panel (desktop only)

## 2) Layout

## 2.1 Desktop

- Two-column container:
  - Left: auth form panel.
  - Right: image panel.
- Image panel is decorative branding support and does not contain required form interactions.
- Mode switch changes only form content inside the left panel; no full-page navigation required.

## 2.2 Mobile

- Single-column form layout.
- Hide right image panel entirely.
- Keep mode switch and all auth actions in the visible form area.

## 3) Form Modes and Fields

## 3.1 Login Mode

Fields:

- `email` (required)
- `password` (required)

Actions:

- Primary CTA: `Log in`
- Secondary link: `No account? Sign up`
- Optional helper link: `Forgot password` (UI-ready even if backend recovery is staged)

## 3.2 Sign Up Mode

Fields:

- `email` (required)
- `password` (required)
- `role` (required, quick selection control with 2 options:
  `Candidate` -> `candidate`, `Recruiter` -> `recruiter`)

Actions:

- Primary CTA: `Create account`
- Secondary link: `Already have an account? Log in`

## 4) Validation Rules (MVP)

- `email`:
  - required
  - must pass standard email format validation
- `password`:
  - required
  - minimum 8 characters
- `role`:
  - required in sign-up mode
  - value must be one of `candidate`, `recruiter`
  - input style must be explicit selection (not free-text)

## 5) UI States

Required states:

- `idle`: default form state
- `typing`: user editing
- `submitting`: request in progress, disable primary CTA, show loading indicator
- `success`: auth completed, proceed to next screen
- `field_error`: invalid field format or missing required input
- `auth_error`: invalid credentials (login)
- `conflict_error`: email already exists (sign-up)
- `role_error`: no role selected in sign-up mode
- `network_error`: network timeout/offline
- `server_error`: unexpected backend error

## 6) Interaction Rules

- Switching mode:
  - preserve shared field values where reasonable (`email`)
  - clear mode-specific errors when mode changes
- Submit behavior:
  - run client validation first
  - call backend only when form is valid
  - bind backend error codes/messages to defined UI states
- Double submit protection:
  - disable primary CTA during `submitting`

## 7) Content Rules

- Keep copy concise and operational.
- Do not include OAuth/Social login buttons in this phase.
- Keep footer/legal links optional and non-blocking for MVP flow.
- Role selection should be shown as two quick options to keep sign-up short.

## 8) Data Contract Mapping (Frontend -> Backend intent)

Auth endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout` (not part of this screen submit flow)

Login payload:

- `email`
- `password`

Sign-up payload:

- `email`
- `password`
- `role`

Notes:

- Backend contract today (from runtime code + DB + LLD):
  - `RegisterRequest`: `email`, `password(min 8)`, `role`
  - `LoginRequest`: `email`, `password`
  - user row stores `password_hash` only (not plain password)
- `full_name` must be collected in a separate post-register step:
  - full_name validation: required, trim spaces, reject empty after trim
  - candidate: `PUT /api/candidate/profile` with `full_name`
  - recruiter: `PUT /api/recruiter/profile` with `organization_id`, `full_name`

## 9) Acceptance Checklist

- Desktop shows left form + right image.
- Mobile hides right image.
- Login mode includes exactly `email`, `password`.
- Sign-up mode includes exactly `email`, `password`, `role`.
- Role control renders as 2 explicit options (`Candidate`, `Recruiter`).
- Email format validation works in both modes.
- Password min-length (8) validation works in both modes where applicable.
- Role required validation works in sign-up mode.
- All required UI states are representable and testable.

## 10) Production Vietnamese UI Copy

Documentation remains English, but visible UI copy must be Vietnamese:

- Login tab: `Đăng nhập`
- Sign-up tab: `Tạo tài khoản`
- Email label: `Email`
- Password label: `Mật khẩu`
- Role label: `Vai trò`
- Candidate role: `Ứng viên`
- Recruiter role: `Nhà tuyển dụng`
- Login CTA: `Đăng nhập`
- Sign-up CTA: `Tạo tài khoản`
- Invalid credentials: `Email hoặc mật khẩu không đúng.`
- Email conflict: `Email này đã được sử dụng.`
- Disabled account: `Tài khoản đã bị khóa`
- Session expired: `Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.`

Post-auth routing:

- candidate without `candidate_profile` -> Candidate Profile Setup.
- candidate with profile -> Job Market.
- recruiter without `recruiter_profile` or organization -> Recruiter Profile Setup.
- recruiter with profile -> Talent Market.
- admin -> Admin Monitoring.
- if the auth flow started from `return_to`, restore it only when role and
  resource visibility still allow access.
