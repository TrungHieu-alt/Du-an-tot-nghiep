# Upload + Parse Review Specification (CV/JD)

Status: production-like MVP planning
Priority: Core MVP

## 1) Purpose

- Provide a dedicated page for:
  - document upload (CV or JD)
  - parse result preview
  - mandatory user confirmation/correction of critical fields
- Ensure hard filter inputs are user-verified before downstream matching usage.
- Serve as the only upload path that may create or update draft CV/JD records
  from parser output.

## 2) Placement In Flow

- Candidate flow:
  - Auth -> Candidate Profile Setup -> Upload + Parse Review (CV)
- Recruiter flow:
  - Auth -> Recruiter Profile Setup -> Upload + Parse Review (JD)

Upload remains optional at journey level.
If user chooses to upload, parse review completion is mandatory before allowing
`active` resume or `published` job usage.

## 2.1 Required Backend Contract Delta

Current document upload/status endpoints are enough for file persistence and
parse lifecycle display, but not enough for production review UI.

Before FE implementation, the API must expose:

- parsed normalized fields for the target entity:
  - CV: `title`, `summary`, `experience`, `skills`, `location`, `job_type`,
    `seniority`, `education`, `certifications`
  - JD: `title`, `requirement`, `skills`, `location`, `job_type`,
    `seniority`, `education`, `required_certifications`
- raw/extracted text or an extracted text URL.
- parser metadata: `parser_version`, extraction timestamp, confidence or
  warnings when available.
- embedding metadata: target groups and `embedding_version_requested`.
- target entity linkage: `resume_id` or `job_id` after parse creates/updates the
  draft record.
- a save path for reviewed data:
  - CV: `PATCH /api/candidate/resumes/{resume_id}`
  - JD: `PATCH /api/jobs/{job_id}`

Do not implement this screen with mock parsed fields. If the parsed-field API is
not available, keep the page behind a feature flag and route users to manual
CV/JD creation instead.

## 3) Page Modes

- `CV mode`
- `JD mode`

Both modes use the same page shell and state machine, with different field sets.

## 4) Required Layout And Sections

## 4.0 Two-Tab Layout (Core)

- Tab A: `Review Form`
- Tab B: `Original File`

Rule:

- Both CV and JD modes must use this two-tab structure.
- User can switch tabs freely without losing unsaved review edits.
- The hard-filter confirmation gate remains enforced regardless of active tab.

## 4.1 Upload Section

- file input/dropzone
- accepted file type hints
- file metadata preview (filename, size, type)
- upload progress and retry

## 4.2 Parse Status Section

- parsing progress (`queued`, `processing`)
- parse success/failure summary
- parser version and extraction timestamp (if available)

## 4.3 Extracted Fields Review Section

Rule:

- Show all extracted fields returned by parser/normalizer.
- Do not hide extracted fields even if low confidence or empty.
- Each field must be user-editable unless field is system-managed metadata.
- If the API returns warnings/confidence, display them inline at field level
  without blocking edits.

Field grouping:

- Hard filter fields (must confirm)
- Ranking/context fields
- Raw extraction and metadata fields
- Embedding-related fields

Placement:

- This section lives under Tab A (`Review Form`).

## 4.4 Hard Filter Confirmation Section (Mandatory)

Before continue, user must explicitly confirm or edit:

- `location`
- `job_type`
- `seniority`
- `education`
- certifications field (`certifications` or `required_certifications`) when present

Block continue until required confirmations pass validation.

## 4.5 Embedding Fields Section (Read/Review)

Show embedding-related values/metadata generated or prepared by pipeline, such as:

- source text chunks used per embedding target
- embedding target groups:
  - CV: title/skills/summary/experience targets
  - JD: title/skills/requirement targets
- embedding version/status metadata

Notes:

- If numeric vectors are not exposed by API, display available embedding metadata
  and source-text basis instead of raw vector arrays.
- If vectors are exposed later, page should support read-only rendering for audit.

## 4.6 Original File Viewer Section

Placement:

- This section lives under Tab B (`Original File`).

Behavior:

- PDF files:
  - render inline preview from backend download/signed URL.
- DOC/DOCX files:
  - show fallback message that inline preview is unavailable in MVP,
  - provide `Download original file` action,
  - provide extracted text preview link/section in Tab A when available.

Storage note:

- Viewer depends on backend-provided accessible document URL.
- URL can come from local storage adapter now and S3-compatible signed URLs later
  without changing the FE tab structure.

## 5) Validation Rules

- Enumerated fields must match backend enums.
- User edits must pass schema checks before confirmation.
- Hard filter confirmation is mandatory when upload path is used.

## 6) State Model

- `idle`
- `uploading`
- `upload_error`
- `parse_queued`
- `parse_processing`
- `parse_failed`
- `parse_succeeded_review_required`
- `review_validation_error`
- `review_confirming`
- `review_confirmed`
- `save_error`

## 7) Actions

- `Upload file`
- `Retry upload`
- `Retry parse`
- `Edit extracted field`
- `Confirm hard filters`
- `Save reviewed data`
- `Continue to next screen`
- `Skip upload` (available only before upload starts)

## 8) Multi-Screen Ready Architecture Rules

- Keep parsed data in a normalized draft object:
  - `raw_extracted`
  - `normalized_fields`
  - `hard_filter_fields`
  - `embedding_fields`
  - `user_overrides`
- Keep review completion criteria declarative:
  - list of required confirmed keys
- Keep per-field confidence and audit trail:
  - original value
  - user-edited value
  - final committed value

## 8.1 Reuse With Detail Screens (Scoped)

Reuse with `job-detail` and `resume-detail` should be limited to shared data
presentation/editing building blocks:

- field section renderer
- hard-filter section renderer
- field-row editor/view model

Do not force action/navigation parity:

- Preview uses review-confirm-save actions.
- Detail uses lifecycle/matching/record actions.

## 9) Acceptance Checklist

- Upload is on a dedicated page, not embedded in profile setup form.
- Page supports both CV and JD mode.
- Page uses two tabs: `Review Form` and `Original File`.
- All parser-extracted fields are visible in review UI.
- Hard filter fields require explicit user confirmation/edit before continue.
- Embedding-related fields/metadata are visible in dedicated section.
- PDF original file can be previewed inline via backend URL.
- DOC/DOCX mode provides fallback (download + extracted-content guidance).
- User can skip upload only before starting upload.

## 10) Production Vietnamese UI Copy

- CV page title: `Tải và kiểm tra CV`
- JD page title: `Tải và kiểm tra JD`
- Review tab: `Biểu mẫu kiểm tra`
- Original file tab: `Tệp gốc`
- Upload CTA: `Tải tệp lên`
- Retry upload CTA: `Tải lại`
- Retry parse CTA: `Phân tích lại`
- Confirm hard filters CTA: `Xác nhận thông tin bắt buộc`
- Save reviewed data CTA: `Lưu thông tin đã kiểm tra`
- Continue CTA: `Tiếp tục`
- Skip upload CTA: `Bỏ qua tải tệp`
- Queued status: `Đang chờ phân tích`
- Processing status: `Đang phân tích`
- Succeeded status: `Phân tích xong, cần kiểm tra`
- Failed status: `Phân tích thất bại`
- Upload too large: `Tệp vượt quá dung lượng cho phép.`
- Unsupported file type: `Định dạng tệp chưa được hỗ trợ.`
- Parse failed: `Không thể phân tích tài liệu. Bạn có thể thử lại hoặc chỉnh thủ công.`

Production routing:

- CV parse success routes to Resume Detail after required hard-filter review.
- JD parse success routes to Job Detail after required hard-filter review.
- Parse retry history is visible through document detail `parse_jobs`.
- Reviewed data is saved through the target entity PATCH endpoint before
  navigation. Activation/publishing remains an explicit action on detail pages.
