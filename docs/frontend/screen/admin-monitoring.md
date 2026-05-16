# Admin Monitoring Specification

Status: production-like MVP planning  
Priority: Core MVP  
Documentation language: English  
Visible UI copy: Vietnamese

## 1) Purpose

Provide a read-only admin area for operational monitoring of users, uploaded
content, parse jobs, applications, invites, notifications, and audit logs.
Admin MVP has no destructive moderation actions.

## 2) Backend Alignment

Primary endpoints:

- `GET /api/admin/users?role=&status=&q=`
- `GET /api/admin/users/{user_id}`
- `GET /api/admin/documents?document_type=&parse_status=&owner_user_id=`
- `GET /api/admin/parse-jobs?status=&document_type=`
- `GET /api/admin/applications?status=&job_id=&resume_id=`
- `GET /api/admin/invites?status=&job_id=&resume_id=`
- `GET /api/admin/notifications?status=&user_id=`
- `GET /api/admin/audit-logs?actor_user_id=&target_type=&target_id=&event_type=`

## 3) Information Architecture

- Landing route: Admin Monitoring dashboard.
- Primary tabs:
  - Users
  - Documents
  - Parse Jobs
  - Applications
  - Invites
  - Notifications
  - Audit Logs
- User detail route:
  - user summary
  - candidate/recruiter profile block when available
  - organization block for recruiters
  - operational summary counts

## 4) Vietnamese UI Copy

| UI element | Copy |
|---|---|
| Dashboard title | `Giám sát hệ thống` |
| Users tab | `Người dùng` |
| Documents tab | `Tài liệu` |
| Parse jobs tab | `Tác vụ phân tích` |
| Applications tab | `Ứng tuyển` |
| Invites tab | `Lời mời` |
| Notifications tab | `Thông báo` |
| Audit logs tab | `Nhật ký hệ thống` |
| User detail title | `Chi tiết người dùng` |
| Ops summary title | `Tổng quan vận hành` |
| Empty title | `Không có dữ liệu` |
| Empty body | `Thử thay đổi bộ lọc hoặc kiểm tra lại dữ liệu hệ thống.` |
| Read-only hint | `Chế độ chỉ xem` |

## 5) List Requirements

- Users:
  - filters: role, status, email query.
  - columns: email, role, status, created date.
- Documents:
  - filters: document type, parse status, owner user ID.
  - columns: filename, owner, type, size, linked resume/job, created date.
- Parse Jobs:
  - filters: status, document type.
  - columns: parse job ID, document ID, target type, status, error code,
    updated date.
- Applications:
  - filters: status, job ID, resume ID.
  - columns: application ID, job ID, resume ID, candidate user ID, status.
- Invites:
  - filters: status, job ID, resume ID.
  - columns: invite ID, job ID, resume ID, candidate user ID, recruiter user ID,
    status.
- Notifications:
  - filters: status, user ID.
  - columns: notification ID, recipient, type, status, entity.
- Audit Logs:
  - filters: actor user ID, target type, target ID, event type.
  - columns: audit log ID, actor, event type, target, created date.

## 6) States

- `loading`
- `success`
- `empty`
- `filter_empty`
- `session_expired`
- `forbidden`
- `not_found`
- `error_network`
- `error_server`

## 7) Acceptance Checklist

- Admin landing gives access to all seven monitoring lists.
- Every list has the filters backed by current API query parameters.
- User detail includes profile/organization blocks when available and ops
  summary counts.
- No destructive action is shown.
- Vietnamese copy is used for all visible UI strings.
