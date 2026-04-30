# REQUIREMENTS.md — Nguồn Sự Thật Cấp Cao

> **Khi nào cần đọc file này:**
> - Bắt đầu một feature mới
> - Thay đổi hành vi hiển thị với người dùng
> - Sửa domain/business logic
> - Giải quyết mâu thuẫn giữa code và spec
> - Viết test cho product behavior
> - Refactor code có thể ảnh hưởng đến requirements
> - Review PR về tính đúng đắn nghiệp vụ
>
> **Không cần đọc khi:**
> - Chỉ format code / đổi tên biến không ảnh hưởng hành vi
> - Bugfix nhỏ đã mô tả rõ trong task
> - Cập nhật dependency/config không liên quan đến behavior

---

## 1. Tổng quan dự án

**Tên:** Job Matcher — Hệ thống matching CV–JD sử dụng kiến trúc RAG

**Một câu:** Hệ thống matching CV–JD hai chiều kết hợp vector search, weighted reranking và LLM evaluation để tìm việc/ứng viên theo ngữ nghĩa, trả về điểm số và reasoning rõ ràng cho từng kết quả.

**Mục tiêu sản phẩm:**
- Ứng viên (Candidate) upload CV → tìm được các công việc phù hợp nhất kèm lý do.
- Nhà tuyển dụng (Recruiter) upload JD → tìm được các ứng viên phù hợp nhất kèm lý do.
- Mọi kết quả matching đều có điểm số, breakdown theo từng chiều, và reasoning sinh bởi LLM.

**Vấn đề cốt lõi được giải quyết:**
- CV/JD là văn bản dài, phi cấu trúc, đa ngôn ngữ — keyword search bỏ sót nhiều trường hợp tương đồng về ý nghĩa.
- LLM dùng trực tiếp không có context thực tế dễ hallucinate.
- Đánh giá thủ công tốn thời gian và thiếu nhất quán.
- Hệ thống hiện tại khó giải thích lý do xếp hạng.

---

## 2. Người dùng và vai trò

| Role | Mô tả | Quyền chính |
|---|---|---|
| `candidate` | Ứng viên tìm việc | Upload CV, tìm jobs, xem match results, nộp đơn |
| `recruiter` | Nhà tuyển dụng | Upload JD, tìm candidates, xem match results, quản lý đơn |

**Lưu ý thực tế:** Hệ thống hiện tại chưa enforce tenant boundary nghiêm ngặt ở route level — đây là known risk cần ghi nhận trong mọi task liên quan đến auth/access control.

---

## 3. Use Cases chính

### UC1: Candidate tìm việc
1. Candidate đăng ký / đăng nhập.
2. Upload CV (PDF, DOCX, TXT) hoặc nhập text.
3. Hệ thống extract text → dịch sang tiếng Anh nếu cần → parse thành JSON → tạo embeddings → lưu MongoDB + ChromaDB.
4. Candidate bấm "Find Jobs".
5. Hệ thống chạy matching pipeline (CV → JD): ANN retrieval → weighted rerank → LLM evaluate → hybrid score.
6. Trả về Top-5 jobs kèm final score, breakdown, và reasoning.
7. Candidate xem match detail, có thể nộp đơn (Application).

### UC2: Recruiter tìm ứng viên
1. Recruiter đăng ký / đăng nhập.
2. Upload JD (PDF, DOCX, TXT) hoặc nhập text.
3. Hệ thống xử lý tương tự phía JD.
4. Recruiter bấm "Find Candidates".
5. Hệ thống chạy matching pipeline (JD → CV): ANN retrieval → weighted rerank → LLM evaluate → hybrid score.
6. Trả về Top-5 candidates kèm final score, breakdown, và reasoning.
7. Recruiter xem match detail, quản lý trạng thái đơn ứng tuyển.

### UC3: Quản lý đơn ứng tuyển (Application Tracking)
- Candidate nộp đơn cho một job với CV và cover letter.
- Recruiter xem danh sách đơn, cập nhật trạng thái: `pending → viewed → interviewing → rejected | hired`.
- Candidate xem lịch sử các đơn đã nộp.

---

## 4. Functional Requirements

### FR1. Xác thực người dùng

- Đăng ký với email + password (hash bằng Argon2).
- Đăng nhập trả về JWT access token (60 phút) + refresh token (7 ngày).
- Role được gán khi tạo profile: `candidate` hoặc `recruiter`.
- **Constraint:** SECRET_KEY hiện hardcoded trong `auth.py` — phải chuyển sang env var trước production.

### FR2. Upload và ingestion tài liệu

**Supported formats:** PDF, DOCX, TXT (image OCR với Tesseract).

**Pipeline ingestion (bất biến — không được phá vỡ thứ tự):**
```
File upload
  → Extract raw text (fitz/docx2txt/Tesseract)
  → Language detect (langdetect)
  → Translate to English if needed (Gemini, bypass if AI_MODE=mock)
  → Clean + segment blocks (regex first, LLM fallback)
  → Parse to structured JSON (Gemini, mock regex fallback)
  → Generate field embeddings (SentenceTransformer all-MiniLM-L6-v2)
  → Store business record → MongoDB
  → Store vector + metadata → ChromaDB
```

**CV parsed JSON schema (canonical):**
```json
{
  "summary": "string",
  "experience": "string",
  "job_title": "string",
  "skills": ["string"],
  "full_text": "string",
  "location": "string"
}
```

**JD parsed JSON schema (canonical):**
```json
{
  "job_description": "string",
  "job_requirement": "string",
  "job_title": "string",
  "skills": ["string"],
  "full_text": "string",
  "location": "string"
}
```

**Invariants:**
- Output phải là JSON hợp lệ. Nếu LLM trả invalid JSON → raise exception, không được swallow lỗi.
- `skills` phải là `List[str]`, không phải string.
- Không được hallucinate thông tin ngoài văn bản gốc.
- Xóa CV/JD phải xóa cả vector trong ChromaDB (cross-store consistency).

### FR3. Matching Pipeline (4 stages — thứ tự bất biến)

**Stage 1 — ANN Retrieval:**
- Query bằng `emb_full` embedding của anchor (CV hoặc JD).
- Lấy Top-N candidates từ ChromaDB (default `ANN_K = 50`).
- Output: danh sách candidate IDs + metadata.

**Stage 2 — Weighted Field Reranking:**
- Tính cosine similarity cho từng field embedding pair.
- Embeddings đã normalize → dot product = cosine similarity.
- Lấy Top-K để đưa vào LLM (default `RERANK_K = 10`).

**Field weights (canonical — thay đổi phải cập nhật spec này):**

| Field | Weight | CV embedding key | JD embedding key |
|---|---|---|---|
| skills | 0.30 | `emb_skills` | `emb_skills` |
| experience_requirement | 0.25 | `emb_experience` | `emb_job_requirement` |
| summary_description | 0.20 | `emb_summary` | `emb_job_description` |
| job_title | 0.15 | `emb_job_title` | `emb_job_title` |
| full | 0.05 | `emb_full` | `emb_full` |
| location | 0.05 | `emb_location` | `emb_location` |

**Stage 3 — LLM Evaluation (batched):**
- Gửi một prompt duy nhất cho Top-K candidates.
- LLM (Gemini 2.5 Flash Lite) trả về `score` (0–100) và `reason` cho từng candidate.
- Nếu LLM fail → fallback: `llm_score = weighted_sim * 100`, reason = fallback message.
- Nếu `AI_MODE=mock` → bypass LLM hoàn toàn, dùng fallback ngay.

**Stage 4 — Hybrid Final Scoring:**

```
final_score = 0.2 × cosine_ann + 0.5 × weighted_sim + 0.3 × (llm_score / 100)
```

Tất cả thành phần chuẩn hóa về `[0, 1]`. Trả về Top-K cuối (default `FINAL_K = 5`).

**Invariants:**
- Candidate thiếu embedding → bị skip (không crash).
- ANN query empty → trả `[]` an toàn.
- LLM failure không được làm crash toàn bộ pipeline.

### FR4. Kết quả matching và persistence

**MatchResult** được lưu vào MongoDB với unique constraint `(cv_id, job_id)`.

**Schema:**
```json
{
  "match_id": "int",
  "cv_id": "int",
  "job_id": "int",
  "score": "float [0,1]",
  "metadata": {
    "cosine_ann": "float",
    "weighted_sim": "float",
    "llm_score": "float (0-100)",
    "reason": "string"
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Persistence policy:**
- Upsert mỗi qualifying pair (score ≥ `min_score`).
- Delete records ngoài Top-K cho anchor entity sau mỗi run.
- Read API enriches on-the-fly từ MongoDB CV/Job records — không lưu enriched payload vào `match_results`.

### FR5. Asynchronous Matching

Hệ thống hỗ trợ hai execution mode:

| Mode | Endpoint | Behavior |
|---|---|---|
| Sync | `POST /matching/job/{id}/run` | Blocking, trả kết quả trực tiếp |
| Async | `POST /matching/job/{id}/run/async` | Queued background task, poll bằng `GET /matching/jobs/{tracking_id}` |

**Job status lifecycle:** `queued → running → succeeded | failed`

### FR6. Application Tracking

- Candidate nộp đơn: `POST /applications/` với `job_id`, `candidate_id`, `cv_id`, `cover_letter`.
- Application status: `pending → viewed → interviewing → rejected | hired`.
- Recruiter cập nhật status qua `PATCH /applications/{app_id}/status`.
- Cover letter tối đa 5000 ký tự.

### FR7. Frontend

**Routes hiện tại:**
- `/` — Home/landing page
- `/login`, `/register` — Auth pages
- `/jobs`, `/jobs/:id` — Job listing và detail
- `/candidates`, `/candidates/:id` — Candidate listing và detail
- `/profile` — User profile
- `/create-profile` — Tạo profile lần đầu

**Tính năng UI bắt buộc:**
- Upload CV/JD.
- CV/JD Selector Modal để chọn tài liệu khi tìm kiếm.
- Hiển thị match results với: final score, reasoning, field score breakdown.
- Chatbot AI tích hợp toàn cục.
- Filter/sort kết quả theo nhiều tiêu chí.

---

## 5. Non-functional Requirements

### Performance
- ANN retrieval + weighted rerank phải hoàn thành trong vài giây.
- LLM evaluation là bottleneck chính — phải batched, không gọi per-candidate.
- Matching sync có thể blocking cho prototype; production nên async.

### Reliability & Fallback
- LLM unavailable → fallback score từ weighted_sim, không crash.
- JSON parse failure từ LLM → raise rõ ràng, không swallow.
- Cross-store operations không transactional — temporary divergence có thể xảy ra; cần graceful retry.

### AI Mode Control
- `AI_MODE=live` (default): Gemini được gọi cho translation, parsing, LLM evaluation.
- `AI_MODE=mock`: Toàn bộ Gemini calls bị bypass. Parsing dùng regex fallback. LLM score = weighted_sim * 100. Dùng cho dev/test offline.

### Cost Control
- LLM chỉ được gọi cho Top-K (≤ 10) candidates, không gọi cho toàn bộ ANN results.
- Gemini queue có bounded size (256), workers (2), timeout (45s), retries (2).
- Cache parsed JSON và embeddings nếu document không thay đổi.

### Explainability (bắt buộc cho mọi match result)
Mỗi kết quả phải có đủ:
- `final_score` — điểm tổng hợp
- `cosine_ann` — ANN retrieval score
- `weighted_sim` — weighted field similarity score
- `llm_score` — LLM evaluation score (0–100)
- `reason` — reasoning text từ LLM (hoặc fallback message)

### Security (known gaps)
- JWT secret key hiện hardcoded → phải env var trước production.
- Route-level auth/tenant enforcement chưa đầy đủ → known risk, không silently assume protected.

---

## 6. Data Model (Canonical)

### User
```python
user_id: int
email: str
password_hash: str  # Argon2
role: "candidate" | "recruiter" | None
created_at, updated_at: datetime
```

### CandidateProfile
```python
user_id: int
full_name, location, summary: Optional[str]
experience_years: Optional[int]
skills: List[str]
```

### RecruiterProfile
```python
user_id: int
company_name, recruiter_title, company_logo, about_company: Optional[str]
hiring_fields: List[str]
```

### CandidateResume (cv_id là business key)
```python
cv_id: int
user_id: int
title: str
location, experience, summary, full_text: Optional[str]
skills: List[str]
embedding: Optional[str]  # JSON serialized field embeddings
pdf_url: Optional[str]
is_main: bool
```

### JobPost (job_id là business key)
```python
job_id: int
recruiter_id: int
title, role, location, job_type, experience_level: str
skills: List[str]
salary_min, salary_max: Optional[int]
full_text, embedding: Optional[str]
pdf_url: Optional[str]
```

### MatchResult
```python
match_id: int
cv_id: int         # FK → CandidateResume
job_id: int        # FK → JobPost
score: float       # [0, 1] final hybrid score
metadata: Dict     # cosine_ann, weighted_sim, llm_score, reason
# Unique index: (cv_id, job_id)
# Sort indexes: (cv_id, score DESC), (job_id, score DESC)
```

### Application
```python
app_id: int
job_id: int
candidate_id: int
cv_id: int
match_id: Optional[int]
cover_letter: str  # max 5000 chars
status: "pending" | "viewed" | "interviewing" | "rejected" | "hired"
```

---

## 7. Kiến trúc hệ thống

### Stack

| Thành phần | Công nghệ |
|---|---|
| Backend | FastAPI + Uvicorn |
| Business DB | MongoDB (Beanie ODM) |
| Vector Store | ChromaDB (persistent local) |
| Embedding | SentenceTransformers `all-MiniLM-L6-v2` |
| LLM | Gemini 2.5 Flash Lite |
| Frontend | React + TypeScript + Tailwind CSS (Vite) |
| Container | Docker Compose (mongo + backend + frontend) |

### Data ownership boundaries (bất biến)
- **MongoDB** = source of truth cho business entities và match records.
- **ChromaDB** = retrieval infrastructure only (semantic index).
- AI outputs = advisory ranking signals; quyết định cuối cùng persist trong MongoDB.

### ChromaDB collections
- `cv_full` — CV embeddings + metadata (serialized field embeddings JSON)
- `jd_full` — JD embeddings + metadata (serialized field embeddings JSON)

### API surface (prefix `/api`)

| Router | Path prefix | Chức năng |
|---|---|---|
| user_router | `/users` | Auth, register, login |
| candidate_router | `/candidates` | Candidate profile |
| recruiter_router | `/recruiters` | Recruiter profile |
| cv_router | `/cv` | CV CRUD, upload, match |
| job_router | `/jobs` | JD CRUD, upload, match |
| match_router | `/matching` | Run matching, query results |
| application_router | `/applications` | Application lifecycle |
| system_router | `/health` | Health check |

---

## 8. Acceptance Criteria (Prototype)

Prototype được coi là đạt khi:

- [ ] Candidate upload CV → hệ thống parse thành JSON có đủ 6 fields.
- [ ] Recruiter upload JD → hệ thống parse thành JSON có đủ 6 fields.
- [ ] Embeddings được tạo và lưu thành công vào ChromaDB.
- [ ] Candidate tìm được Top-5 jobs phù hợp với đầy đủ score + reasoning.
- [ ] Recruiter tìm được Top-5 candidates phù hợp với đầy đủ score + reasoning.
- [ ] Mỗi kết quả có `final_score`, `cosine_ann`, `weighted_sim`, `llm_score`, `reason`.
- [ ] Match results được persist trong MongoDB với unique `(cv_id, job_id)`.
- [ ] Nếu LLM fail → fallback score hoạt động, pipeline không crash.
- [ ] Xóa CV/JD → vectors tương ứng bị xóa khỏi ChromaDB.
- [ ] `AI_MODE=mock` → pipeline chạy end-to-end không cần Gemini API key.
- [ ] Docker Compose `docker compose up` → toàn bộ stack khởi động thành công.

---

## 9. Rủi ro và hạn chế hiện tại

| Nhóm | Hạn chế | Mức độ |
|---|---|---|
| Security | JWT secret hardcoded; route auth chưa đầy đủ | Cao |
| Matching quality | Chưa có Knowledge Graph, chưa fine-tune embedding | Trung bình |
| Scalability | ChromaDB local không phù hợp dữ liệu lớn | Trung bình |
| Reliability | Cross-store ops không transactional | Trung bình |
| Config | Field weights hardcoded, không tunable qua API | Thấp |
| Testing | Chưa có automated test suite đầy đủ | Cao |
| LLM | Reasoning có thể suy diễn nếu prompt chưa ràng buộc chặt | Trung bình |

---

## 10. Roadmap

### Phase 1 — Hoàn thiện prototype (hiện tại)
- Chuẩn hóa API contracts.
- Hoàn thiện frontend candidate/recruiter dashboard.
- Thêm validation output từ LLM.
- Thêm fallback rõ ràng cho mọi AI stage.
- Chuyển JWT secret sang env var.

### Phase 2 — Cải thiện matching quality
- Skills Knowledge Graph.
- Job Title Hierarchy.
- Set-based skill matching theo từng kỹ năng riêng lẻ.
- Fine-tune embedding bằng contrastive learning trên cặp CV–JD.
- Tối ưu field weights bằng validation set.

### Phase 3 — Nâng độ tin cậy
- Multi-agent system (Supervisor, Preprocess, Retrieval, Rerank, Generate agents).
- Evidence-only reasoning constraint cho LLM.
- Confidence score cho mỗi kết quả.
- Retry/fallback per-agent.

### Phase 4 — Production readiness
- Matching chạy background jobs (queue-based).
- Managed MongoDB Atlas.
- Vector DB chuyên dụng (Pinecone / Weaviate / Milvus).
- Monitoring, logging, cost tracking.
- Feedback loop từ recruiter/candidate để cải thiện ranking.

---

## 11. Evaluation baseline

| Method | Recall@5 (tập test nhỏ) |
|---|---|
| Pure embedding full_text | 0.61 |
| RAG pipeline (4-stage) | 0.73 |

RAG pipeline cải thiện ~+14% trên tập 20 CV / 10 JD. Kết quả này chỉ là đánh giá sơ bộ — chưa có benchmark chuẩn hoặc dataset lớn.

---

*Cập nhật file này khi: thay đổi domain model, thay đổi scoring formula, thêm/xóa user-facing behavior, hoặc thay đổi acceptance criteria.*
