# Mastodon Job Matcher Extension

Dự án gồm backend + frontend để quản lý hồ sơ ứng viên, bài đăng tuyển dụng và thực hiện matching hai chiều. Hệ thống hỗ trợ đăng nhập, quản lý CV/JD, theo dõi ứng tuyển, và trả về kết quả matching có giải thích. README này mô tả toàn bộ sản phẩm, không chỉ riêng RAG.

## Tổng quan sản phẩm
- **Ứng viên**: tạo hồ sơ, tải CV, xem gợi ý việc làm phù hợp, theo dõi đơn ứng tuyển.
- **Nhà tuyển dụng**: tạo bài đăng, xem danh sách ứng viên phù hợp, quản lý matching và phản hồi.
- **Hệ thống matching**: tự động xếp hạng phù hợp CV ↔ JD, trả về score + lý do.

## Tính năng chính
- Xác thực người dùng, phân quyền ứng viên/nhà tuyển dụng.
- Quản lý hồ sơ ứng viên (CV chính, kỹ năng, kinh nghiệm, vị trí).
- Quản lý bài đăng tuyển dụng (role, level, location, skills, mô tả).
- Upload CV/JD từ file (PDF/DOCX/ảnh) hoặc text.
- Matching hai chiều, lưu kết quả và cho phép lọc theo điểm.
- Giao diện web để thao tác và theo dõi kết quả.

## Kiến trúc hệ thống
- **Backend**: FastAPI cung cấp API CRUD và matching.
- **Database (V1 production)**: MongoDB lưu user, CV, JD, match results.
- **Vector store (V1 production)**: ChromaDB lưu embeddings phục vụ truy hồi.
- **AI/RAG (V1 production)**: Gemini parse và đánh giá, SentenceTransformer tạo embeddings.
- **V2 prototype**: PostgreSQL + pgvector (port 5433) — 4 bảng scope-locked (`job_posts_v2`, `candidate_profiles_v2`, `job_embeddings_v2`, `candidate_embeddings_v2`), embedder hash-based deterministic, không LLM ở runtime. Xem `docs/REQUIREMENTS.md` + `docs/agent-rules/codemap.md` mục 5A.
- **Frontend**: React + Vite + Tailwind + Radix UI. V2 pages tại `/v2/search`, `/v2/jobs/:id`, `/v2/cvs/:id`, `/v2/matching`; xem `frontend/README.md`.

## High-Level System Diagram
![Overview](asset/overview.png)

## RAG Matching Diagram (chi tiết)
```text
Input (CV/JD)
    |
    v
[Preprocess]
  - Read file (PDF/DOCX/Image/Text)
  - OCR nếu cần
  - Detect language + Translate EN
  - Clean + split blocks
    |
    v
[Gemini Parsing]
  CV -> {summary, experience, job_title, skills, location, full_text}
  JD -> {job_description, job_requirement, job_title, skills, location, full_text}
    |
    v
[Embedding - MiniLM]
  emb_summary / emb_experience / emb_skills / emb_full ...
    |
    v
[ChromaDB Vector Store]
  - Lưu emb_full cho ANN
  - Lưu embeddings field trong metadata
    |
    v
[Matching Pipeline]
  Stage 1: ANN Retrieval (top K)
  Stage 2: Weighted Rerank (field weights)
  Stage 3: LLM Evaluate (score + reason)
  Stage 4: Hybrid Score (ann + weighted + llm)
    |
    v
[Output]
  - Ranked list + reason
  - Lưu MatchResult vào MongoDB
```

## Luồng xử lý (tóm tắt)
1. Người dùng tải CV/JD hoặc nhập text.
2. Hệ thống preprocess, parse và lưu dữ liệu.
3. Sinh embeddings, lưu vào ChromaDB.
4. Matching: truy hồi, rerank, LLM evaluate.
5. Lưu match và hiển thị kết quả trên UI.

## Flow chart (tổng thể)
```text
Người dùng
   |
   v
Frontend UI  --->  Backend API  --->  MongoDB (CRUD)
   |                 |
   |                 v
   |             RAG Pipeline
   |                 |
   |                 v
   +------------> ChromaDB (Vector Store)
                     |
                     v
                Kết quả matching
                     |
                     v
                 Hiển thị UI
```

## Use case chính
### Ứng viên
- Đăng ký/đăng nhập.
- Tạo hồ sơ ứng viên.
- Upload CV (PDF/DOCX/ảnh) hoặc nhập text.
- Xem gợi ý việc làm phù hợp.
- Theo dõi đơn ứng tuyển đã gửi.

### Nhà tuyển dụng
- Đăng ký/đăng nhập.
- Tạo hồ sơ nhà tuyển dụng.
- Đăng bài tuyển dụng.
- Chạy matching tìm ứng viên phù hợp.
- Xem danh sách ứng viên + lý do phù hợp.
- Quản lý phản hồi và trạng thái.

## Cấu trúc UI (tóm tắt)
- **AuthPage**: Đăng nhập/đăng ký/quên mật khẩu.
  ![Auth Page](asset/authPage.png)
- **OnBoardingPage**: Chọn vai trò (Candidate/Recruiter).
- **CandidatePage**:
  ![Candidate Page](asset/candidate.png)
- **RecruiterPage**:
  ![Recruiter Page](asset/Recruiter.png)

## Cấu trúc database
![Data Schemas](asset/dataschemas.png)

- **User**: thông tin tài khoản và vai trò.
- **CV**: title, location, experience, skills, summary, full_text, pdf_url.
- **JD**: title, role, location, job_type, experience_level, skills, salary.
- **MatchResult**: cv_id, job_id, score, metadata, timestamps.

## API chính

### V1 production (Mongo + Chroma + Gemini)
- `POST /api/matching/job/{job_id}/run`
- `POST /api/matching/cv/{cv_id}/run`
- `GET /api/matching/job/{job_id}/matches`
- `GET /api/matching/cv/{cv_id}/matches`

### V2 prototype (Postgres + pgvector)
- `POST /api/v2/prototype/matching/job/{job_id}/run` — run-only sync matching
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`
- `GET /api/v2/prototype/catalog/{jobs,cvs}` — paginated browse
- `GET /api/v2/prototype/catalog/{jobs,cvs}/{id}` — single record
- `POST /api/v2/prototype/catalog/{jobs,cvs}/search` — pgvector semantic search với filter `location/job_type/seniority`

Swagger UI: `http://localhost:8000/docs`. Schema: `GET /openapi.json`. Curl examples: `frontend/apiExamples.md`.

## Công nghệ chính
- Backend: FastAPI, Uvicorn, MongoDB (Beanie/Motor).
- AI/RAG: Gemini API, SentenceTransformers (MiniLM), LlamaIndex, ChromaDB.
- OCR/Parse: PyMuPDF, pytesseract, docx2txt, langdetect.
- Frontend: React + Vite + TypeScript + Tailwind + Radix UI.

## Cấu trúc thư mục hiện tại
```text
.
├── backend/         # FastAPI backend + RAG pipeline
├── frontend/        # Frontend React + Vite
├── docker-compose.yml
├── .env.example
├── docs/            # HLD/LLD và agent rules
└── asset/           # Hình ảnh minh họa README
```

## Cấu hình môi trường
Tạo file `.env` ở root project (cùng cấp `docker-compose.yml`):

```env
DB_NAME=job_matching
GEMINI_API_KEY=your_api_key_here
OPENAI_API_KEY=
MASTODON_API_BASE_URL=
MASTODON_ACCESS_TOKEN=
VITE_API_BASE_URL=http://localhost:8000
DEV_ALLOW_ALL_ACCOUNTS=false
```

`MONGO_URI` là tùy chọn. Nếu không truyền, backend trong Docker sẽ dùng MongoDB container nội bộ: `mongodb://mongo:27017`.

`DEV_ALLOW_ALL_ACCOUNTS` (tạm thời cho môi trường dev):
- `false` (mặc định): giữ validation ứng viên/CV ownership như hiện tại.
- `true`: cho phép test chéo flow bằng một account (bỏ qua check candidate profile tồn tại và CV ownership khi tạo application).

## Setup runtime + chạy app (Docker)
Docker Compose là runtime mặc định của project.

### 1) Chuẩn bị môi trường
```bash
cp .env.example .env
# cập nhật GEMINI_API_KEY trong .env
```

### 2) Build và chạy toàn bộ app
```bash
docker compose up --build
```

### 3) Nạp dữ liệu mẫu vào MongoDB container
```bash
# copy folder dump_db từ host vào container mongo
docker compose cp ./dump_db/. mongo:/dump_db

# restore vào DB mặc định job_matching (ghi đè collections cũ)
docker compose exec mongo mongorestore --db job_matching --drop /dump_db
```

### 4) Truy cập services
- MongoDB: `mongodb://localhost:27018`
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:5173`

### 5) Các lệnh runtime Docker thường dùng
```bash
# chạy nền
docker compose up -d

# xem log
docker compose logs -f

# dừng app
docker compose down
```

### Host-local (tùy chọn, chỉ dùng khi không chạy Docker)
#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# hoặc: .venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

Backend chạy ở `http://localhost:8000`.

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend dự kiến chạy ở `http://localhost:5173`.

## Ghi chú
- ChromaDB lưu local tại `backend/ragmodel/vector_store`.
- MongoDB mặc định fallback: `mongodb://localhost:27017`, DB `job_matching`.
- Với Docker Compose, backend mặc định kết nối service `mongo` (`mongodb://mongo:27017`).
- Nếu muốn dùng MongoDB Atlas, set `MONGO_URI` trong root `.env`.
- CORS backend hiện mở cho `http://localhost:5173` và `http://127.0.0.1:5173`.
- Nếu chỉ cần chi tiết pipeline AI, xem `backend/README.md`.
