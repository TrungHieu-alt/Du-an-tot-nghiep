# Cấu trúc Collections (DB Schema)

Tập hợp các bảng dưới đây mô tả cấu trúc của các collection hiện có trong project.

## users

| Trường | Kiểu | Bắt buộc / Giá trị mặc định | Ghi chú |
|---|---:|---|---|
| email | EmailStr | Bắt buộc | Địa chỉ email (unique nên thiết lập ở DB) |
| password_hash | str | Bắt buộc | Hash mật khẩu |
| role | str | Bắt buộc | Giá trị: `candidate` \| `recruiter` \| `admin` |
| name | str | Bắt buộc | Tên hiển thị |
| avatar | Optional[str] | Không bắt buộc (None) | URL hoặc path ảnh đại diện |
| location | Optional[str] | Không bắt buộc (None) | Vị trí người dùng |
| (collection name) | — | — | `users` |

---

## jobs

| Trường | Kiểu | Bắt buộc / Giá trị mặc định | Ghi chú |
|---|---:|---|---|
| recruiter_id | str | Bắt buộc | ID của tuyển dụng (tham chiếu User) |
| title | str | Bắt buộc | Tiêu đề công việc |
| company | str | Bắt buộc | Tên công ty |
| location | Optional[str] | Không bắt buộc | Địa điểm làm việc |
| salary | Optional[str] | Không bắt buộc | Khoảng lương (chuỗi) |
| description | Optional[str] | Không bắt buộc | Mô tả chi tiết |
| requirements | List[str] | Mặc định `[]` | Danh sách yêu cầu/kỹ năng |
| logo | Optional[str] | Không bắt buộc | URL hoặc path logo công ty |
| status | str | Mặc định `"open"` | Trạng thái: `open`/`closed`/... |
| (collection name) | — | — | `jobs` |

---

## candidates

| Trường | Kiểu | Bắt buộc / Giá trị mặc định | Ghi chú |
|---|---:|---|---|
| user_id | str | Bắt buộc | ID user ứng viên (tham chiếu User) |
| title | str | Bắt buộc | Chức danh/ngắn gọn |
| skills | List[str] | Mặc định `[]` | Danh sách kỹ năng |
| summary | Optional[str] | Không bắt buộc | Tóm tắt profile |
| experience | Optional[str] | Không bắt buộc | Kinh nghiệm làm việc |
| location | Optional[str] | Không bắt buộc | Vị trí ứng viên |
| availability | Optional[str] | Không bắt buộc | Tình trạng sẵn sàng |
| (collection name) | — | — | `candidates` |

---

## cv_documents

| Trường | Kiểu | Bắt buộc / Giá trị mặc định | Ghi chú |
|---|---:|---|---|
| candidate_id | str | Bắt buộc | ID ứng viên (tham chiếu Candidate/User) |
| template | str | Bắt buộc | Tên/ID mẫu CV |
| data | Dict | Bắt buộc | Dữ liệu điền vào template (key/value) |
| thumbnail | Optional[str] | Không bắt buộc | URL/path ảnh thu nhỏ |
| (collection name) | — | — | `cv_documents` |

---

## matching

| Trường | Kiểu | Bắt buộc / Giá trị mặc định | Ghi chú |
|---|---:|---|---|
| job_id | str | Bắt buộc | ID công việc (tham chiếu Job) |
| candidate_id | str | Bắt buộc | ID ứng viên (tham chiếu Candidate/User) |
| score | Optional[int] | Không bắt buộc | Điểm match (ví dụ 0-100) |
| status | Optional[str] | Không bắt buộc | Trạng thái matching (ví dụ `pending`, `accepted`) |
| updated_at | datetime | Mặc định thời điểm tạo (UTC) | Thời điểm cập nhật; mặc định: datetime.now(timezone.utc) |
| (collection name) | — | — | `matching` |

---
