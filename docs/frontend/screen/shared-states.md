# Shared State And Error Specification

Status: production-like MVP planning  
Priority: Core MVP  
Documentation language: English  
Visible UI copy: Vietnamese

## 1) Purpose

Define shared UI states that every screen must reuse so candidate, recruiter,
and admin flows behave consistently against the current `/api/*` backend.

## 2) Global Navigation Rules

- Missing or expired token (`401 missing_token`, `401 invalid_token`,
  `401 expired_token`):
  - redirect to Auth screen.
  - preserve the attempted route in client state as `return_to`.
  - after successful login, return to `return_to` when role and resource
    visibility still allow it; otherwise route to the role landing page.
- Disabled user (`403 disabled_user`):
  - show a blocked account page.
  - do not show marketplace CTAs such as activate, publish, apply, invite, or
    run matching.
- Authenticated but wrong role (`403 forbidden`):
  - show a role-permission page in the current app shell.
  - keep primary navigation visible when the session is valid.
- Resource not found or not visible (`404 not_found`):
  - show one not-found screen with copy that does not reveal whether the
    resource exists.

## 3) Vietnamese Copy Contract

Use these strings unless a screen overrides them with a more specific message.

| State | Vietnamese UI copy |
|---|---|
| Session expired | `Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.` |
| Disabled account title | `Tài khoản đã bị khóa` |
| Disabled account body | `Bạn không thể thực hiện thao tác này. Vui lòng liên hệ quản trị viên nếu cần hỗ trợ.` |
| Forbidden title | `Bạn không có quyền truy cập` |
| Forbidden body | `Tài khoản hiện tại không có quyền xem hoặc thao tác với nội dung này.` |
| Not found title | `Không tìm thấy nội dung` |
| Not found body | `Nội dung không tồn tại hoặc bạn không có quyền xem.` |
| Network error | `Không thể kết nối. Kiểm tra mạng và thử lại.` |
| Server error | `Hệ thống đang gặp sự cố. Vui lòng thử lại sau.` |
| Validation summary | `Vui lòng kiểm tra lại các trường được đánh dấu.` |
| Save success | `Đã lưu thay đổi.` |
| Duplicate application | `Bạn đã ứng tuyển công việc này bằng CV đã chọn.` |
| Duplicate invite | `Ứng viên đã có lời mời đang chờ cho công việc này.` |
| Invalid lifecycle transition | `Trạng thái hiện tại không cho phép thao tác này.` |
| Upload too large | `Tệp vượt quá dung lượng cho phép.` |
| Unsupported file type | `Định dạng tệp chưa được hỗ trợ.` |
| Parse failed | `Không thể phân tích tài liệu. Bạn có thể thử lại hoặc chỉnh thủ công.` |

## 4) Empty State Patterns

Each empty state must have one clear next action and no marketing-style copy.

| Context | Title | Body | Primary action |
|---|---|---|---|
| No candidate profile | `Hoàn tất hồ sơ cá nhân` | `Tạo hồ sơ để bắt đầu tải CV và ứng tuyển.` | `Tạo hồ sơ` |
| No resumes | `Chưa có CV` | `Tải CV hoặc tạo CV thủ công để bắt đầu tìm việc.` | `Tải CV` |
| No active resume | `Chưa có CV đang hoạt động` | `Kích hoạt một CV để nhận kết quả matching và ứng tuyển.` | `Mở danh sách CV` |
| No jobs for candidate | `Chưa có công việc phù hợp` | `Thử thay đổi từ khóa hoặc bộ lọc tìm kiếm.` | `Xóa bộ lọc` |
| No recruiter profile | `Hoàn tất hồ sơ nhà tuyển dụng` | `Chọn tổ chức để tạo và đăng tin tuyển dụng.` | `Tạo hồ sơ` |
| No jobs for recruiter | `Chưa có tin tuyển dụng` | `Tạo tin tuyển dụng thủ công hoặc tải JD để hệ thống phân tích.` | `Tạo tin tuyển dụng` |
| No applications | `Chưa có hồ sơ ứng tuyển` | `Ứng tuyển mới sẽ xuất hiện tại đây.` | `Tìm công việc` |
| No invites | `Chưa có lời mời` | `Lời mời từ nhà tuyển dụng sẽ xuất hiện tại đây.` | `Tìm công việc` |
| No notifications | `Không có thông báo` | `Các cập nhật quan trọng sẽ xuất hiện tại đây.` | none |
| Empty admin list | `Không có dữ liệu` | `Thử thay đổi bộ lọc hoặc kiểm tra lại dữ liệu hệ thống.` | `Xóa bộ lọc` |

## 5) Backend Error Mapping

- `400 invalid_anchor`: show matching/action-specific inline error and keep the
  user on the same screen.
- `409 duplicate_application`, `409 duplicate_invite`,
  `409 invalid_transition`, `409 invalid_state`: show inline or toast feedback
  near the attempted action and refresh the affected record.
- `413 file_too_large`, `415 unsupported_mime_type`: show the error in the
  upload dropzone, not as a page-level failure.
- `422 validation_error`: render field-level errors when fields are available;
  otherwise render the validation summary above the form.

## 6) Acceptance Checklist

- Every screen uses these shared states unless it defines a stricter local copy.
- Token expiry preserves `return_to`.
- Disabled users see a blocked page and no marketplace mutation CTAs.
- 403 and 404 are visually distinct enough for behavior, but 404 copy does not
  leak resource existence.
- Vietnamese text is used for visible UI strings.
