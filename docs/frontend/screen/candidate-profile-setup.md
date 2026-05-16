# Candidate Profile Setup Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Complete candidate profile after auth/register.
- Keep v1 lightweight, with only one required field.
- Keep structure ready for future multi-screen onboarding.

## 2) Backend Contract Alignment

Primary endpoint:

- `PUT /api/candidate/profile`

Current required payload field:

- `full_name` (required)

Optional payload fields:

- `phone`
- `current_location` (`ha_noi` | `tp_hcm` | `da_nang`)
- `total_experience_years` (>= 0)
- `headline`

## 3) Layout

## 3.1 v1 Single-Form

- Compact setup form with required field first.
- Optional fields grouped in secondary section.
- Footer action: `Continue`

## 3.2 Future Multi-Screen

- Same field schema can render step-by-step:
  - Step 1: full_name
  - Step 2: location (optional)
  - Step 3: total experience (optional)
  - Step 4: headline/phone (optional)
  - Step 5: continue to dedicated upload/parse page

No payload model change required between modes.

## 4) Fields

- `full_name` (required)
- `current_location` (optional enum)
- `total_experience_years` (optional number)
- `headline` (optional)
- `phone` (optional)

## 5) Validation

- `full_name`:
  - required
  - trim leading/trailing spaces
  - reject empty value after trim
- `current_location`:
  - if provided, must be one of allowed enum values
- `total_experience_years`:
  - if provided, must be number >= 0
- `phone`:
  - optional in MVP
  - format check can be soft warning first

## 6) State Model

- `idle`
- `typing`
- `submitting_profile`
- `profile_success`
- `profile_error_validation`
- `profile_error_conflict`
- `profile_error_network`

## 7) Navigation Hand-off

- On `profile_success`, route user to:
  - dedicated page: `Upload + Parse Review (CV)`
  - upload is optional at flow level, but when user uploads they must complete
    parse review confirmation before active-ready usage.

## 8) Multi-Screen Ready Architecture Rules

- Keep a shared field registry:
  - `key`, `required`, `type`, `api_field`, `step_group`.
- Keep validation field-level, independent from page layout mode.
- Keep submission adapter shared:
  - map form state to API payload once.
- Keep step navigation stateless from payload:
  - `next`, `back`, `skip` only affect UI routing, not data model semantics.

## 9) Acceptance Checklist

- Candidate can submit required profile with `full_name`.
- Optional fields can be skipped without blocking.
- Successful profile setup routes to dedicated CV upload/parse review page.
- Same data model is reusable for future multi-screen flow.

## 10) Production Vietnamese UI Copy

- Page title: `Hoàn tất hồ sơ cá nhân`
- Full name label: `Họ và tên`
- Location label: `Địa điểm hiện tại`
- Experience label: `Số năm kinh nghiệm`
- Headline label: `Tiêu đề hồ sơ`
- Phone label: `Số điện thoại`
- Primary CTA: `Tiếp tục`
- Save success: `Đã lưu hồ sơ cá nhân.`
- Required full name error: `Vui lòng nhập họ và tên.`
- Invalid location error: `Địa điểm không hợp lệ.`

Routing rule:

- If `/api/me` returns a candidate without `candidate_profile`, route here
  before upload, matching, apply, or invite response flows.
