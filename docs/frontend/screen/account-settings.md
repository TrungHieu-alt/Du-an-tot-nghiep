# Account Settings Screen Specification

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide a minimal settings screen that is fully aligned with current backend.
- Expose only settings that can be persisted via existing APIs.

## 2) Backend Alignment (Current)

Read/bootstrap:

- `GET /api/me`

Update candidate profile:

- `PUT /api/candidate/profile`

Update recruiter profile:

- `PUT /api/recruiter/profile`

Notifications:

- `GET /api/notifications`
- `POST /api/notifications/{notification_id}/read`
- `POST /api/notifications/read-all`

Session:

- `POST /api/auth/logout`

## 3) Scope Split

## 3.1 Available Now (Implementable)

- Candidate:
  - `full_name`
  - `phone`
  - `current_location`
  - `total_experience_years`
  - `headline`
- Recruiter:
  - `full_name`
  - `phone`
  - `title`
  - `organization_id` (selected from organizations list flow)
- Notification quick settings:
  - in-app list/read/read-all behavior (not provider-level preferences)
- Logout action

## 3.2 Not In Current API (Do Not Implement As Saved Setting)

- Change password
- Avatar upload
- Language/timezone persistence
- Email notification frequency/preferences

These can be shown as disabled/coming-later entries if needed.

## 4) Layout

- Left nav:
  - `Profile`
  - `Notifications`
  - `Session`
- Main panel:
  - role-aware profile form
  - notification list actions
  - logout action

## 5) Validation

- Respect existing backend validation:
  - `full_name` required in both profile types
  - candidate location enum only
  - candidate `total_experience_years >= 0`
  - recruiter `organization_id` required

## 6) Navigation

- Entry from navbar user menu: `Settings`.
- Save success returns to same settings subsection with success toast.
- Optional back link to previous screen context.

## 7) States

- `loading`
- `success`
- `empty`
- `error_validation`
- `error_network`
- `error_server`
- `session_expired`

## 8) Acceptance Checklist

- Screen only exposes settings backed by current API.
- Candidate and recruiter forms map to correct PUT endpoints.
- Notification read/read-all actions map to current endpoints.
- Logout action calls current auth logout endpoint.
- Unsupported settings are not presented as persistable controls.

## 9) Production Vietnamese UI Copy

- Page title: `Cài đặt tài khoản`
- Profile nav item: `Hồ sơ`
- Notifications nav item: `Thông báo`
- Session nav item: `Phiên đăng nhập`
- Save CTA: `Lưu thay đổi`
- Logout CTA: `Đăng xuất`
- Mark read CTA: `Đánh dấu đã đọc`
- Mark all read CTA: `Đánh dấu tất cả đã đọc`
- Empty notifications title: `Không có thông báo`
- Empty notifications body: `Các cập nhật quan trọng sẽ xuất hiện tại đây.`
- Save success: `Đã lưu thay đổi.`

Production behavior:

- Notification settings are limited to in-app list/read/read-all behavior.
- Email preference controls are not shown as persistable settings in MVP.
