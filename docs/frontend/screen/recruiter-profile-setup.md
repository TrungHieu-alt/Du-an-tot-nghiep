# Recruiter Profile Setup Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Complete recruiter profile after auth/register.
- Keep v1 as a lightweight form.
- Keep structure ready to evolve into multi-screen onboarding later.

## 2) Backend Contract Alignment

Primary endpoint:

- `PUT /api/recruiter/profile`

Current required payload fields:

- `organization_id` (required)
- `full_name` (required)

Optional payload fields:

- `title`
- `phone`

Constraint:

- `organization_id` is required by current backend contract and DB shape.

## 3) Layout

## 3.1 v1 Single-Form

- One compact setup form.
- Clear required markers for `full_name` and `organization`.
- Footer action: `Continue`

## 3.2 Future Multi-Screen

- Same field schema can render step-by-step:
  - Step 1: full_name
  - Step 2: organization
  - Step 3: title/phone (optional)
  - Step 4: continue to dedicated upload/parse page

No payload model change required between modes.

## 4) Fields

- `full_name` (required)
- `organization` selector (required, maps to `organization_id`)
- `title` (optional)
- `phone` (optional)

## 5) Organization Selection UX

- Search by organization name via `GET /api/organizations?q=...`.
- Result item UI:
  - left: logo from `logo_url` (fallback avatar if null)
  - center: organization `name`
  - optional metadata line: `slug`
- Special option in selector:
  - `Khác` (`Other`)
  - maps to pre-seeded system organization ID (Independent bucket)
  - used for freelance, agency, or independent recruiters who should still be
    able to join and publish under a neutral organization profile.

Backend/data requirement:

- The database seed/migration must create exactly one predefined Independent
  organization used by `Khác`.
- FE must read the real `organization_id` from config/bootstrap data or the
  organization search response; do not hard-code an environment-specific ID in
  screen code.
- If the predefined organization is missing, show an operational setup error
  instead of submitting an invalid `organization_id`.

## 6) Validation

- `full_name`:
  - required
  - trim leading/trailing spaces
  - reject empty value after trim
- `organization`:
  - required
  - must resolve to valid `organization_id`
- `phone`:
  - optional in MVP
  - format check can be soft warning first, strict validation later

## 7) State Model

- `idle`
- `typing`
- `searching_org`
- `submitting_profile`
- `profile_success`
- `profile_error_validation`
- `profile_error_conflict`
- `profile_error_network`

## 8) Navigation Hand-off

- On `profile_success`, route user to:
  - dedicated page: `Upload + Parse Review (JD)`
  - upload is optional at flow level, but when user uploads they must complete
    parse review confirmation before publish-ready usage.

## 9) Multi-Screen Ready Architecture Rules

- Keep a shared field registry:
  - `key`, `required`, `type`, `api_field`, `step_group`.
- Keep validation field-level, independent from page layout mode.
- Keep submission adapter shared:
  - map form state to API payload once.
- Keep step navigation stateless from payload:
  - `next`, `back`, `skip` only affect UI routing, not data model semantics.

## 10) Acceptance Checklist

- Recruiter can submit required profile with `full_name` + selected organization.
- Organization list supports search by name.
- Organization options show logo (or fallback avatar).
- Option `Khác` maps to predefined system organization ID.
- `Khác` remains available for independent recruiters and does not require a
  custom organization creation step.
- Successful profile setup routes to dedicated JD upload/parse review page.
- Same data model is reusable for future multi-screen flow.

## 11) Production Vietnamese UI Copy

- Page title: `Hoàn tất hồ sơ nhà tuyển dụng`
- Full name label: `Họ và tên`
- Organization label: `Tổ chức`
- Organization search placeholder: `Tìm tổ chức`
- Other organization option: `Khác`
- Title label: `Chức danh`
- Phone label: `Số điện thoại`
- Primary CTA: `Tiếp tục`
- Required organization error: `Vui lòng chọn tổ chức.`
- Required full name error: `Vui lòng nhập họ và tên.`
- Save success: `Đã lưu hồ sơ nhà tuyển dụng.`

Routing rule:

- If `/api/me` returns a recruiter without `recruiter_profile` or organization,
  route here before job creation, talent search, matching, or invite flows.
