# REQUIREMENTS.md — Matching Prototype V2 (Simple Run-Only)

## 1. Mục tiêu

Prototype V2 dùng để kiểm tra nhanh matching method trên dữ liệu đã có trong PostgreSQL:
- Input một `job_id` hoặc `cv_id`.
- Chạy matching hai chiều JD -> CV hoặc CV -> JD.
- Trả danh sách match có `rank`, điểm số, score breakdown và reasoning.

Prototype này không xử lý ingestion/parse/extract dữ liệu. Dữ liệu test được insert trực tiếp vào PostgreSQL để đánh giá matching logic.

## 2. Phạm vi

In scope:
- Chạy matching từ input ID có sẵn trong DB (`job_id` hoặc `cv_id`).
- Trả top 10 kết quả tốt nhất.
- Trả `rank`, score breakdown và reasoning deterministic.
- Trả runtime cơ bản để biết prototype có chạy ổn không.

Out of scope:
- Thu thập/bóc tách/chuẩn hóa dữ liệu đầu vào
- Mọi flow extract/upload/parse tài liệu.
- LLM scoring/reasoning.
- Salary và full_text trong scoring MVP.
- Persist/query/delete match result.
- Benchmark kết luận quality bằng Precision/Recall/NDCG.
- Auth/role guard riêng cho route prototype.
- So sánh với các pipeline ngoài V2.

## 3. Functional Requirements

### FR1. Input/Output runtime

Input:
- `job_id` cho mode JD -> CV.
- `cv_id` cho mode CV -> JD.

Output mỗi run:
- top 10 matches.
- rank của từng match.
- score breakdown từng thành phần.
- reasoning dạng rule-based.
- runtime cơ bản.

### FR2. Matching pipeline MVP

Stage 1: Load data
- Đọc anchor và candidate pool từ PostgreSQL.
- Prototype run-only dùng exhaustive candidate scoring trên dataset test để dễ kiểm chứng.
- pgvector được dùng để lưu vector và tính similarity khi có embedding, nhưng chưa cần ANN index tuning.

Stage 2: Hard filter
- Hard filter áp dụng hai chiều trên trường chung giữa JD và CV.
- `job_type` chỉ nhận: `remote | fulltime | parttime` (cả JD và CV đều phải có).
- Rule `job_type`:
  - Nếu JD `job_type = remote` thì bỏ qua hard filter `location`.
  - Nếu JD `job_type != remote` thì `job_type` và `location` phải match chính xác giữa JD và CV.
- `seniority`: cả JD và CV đều phải có và phải khớp.
- `education` là hard filter theo thứ bậc taxonomy: `lop_9` < `lop_12` < `dai_hoc` < `thac_si` < `tien_si` (cả JD và CV đều phải có).
- Rule pass: education của CV phải >= education yêu cầu của JD.
- `required_certifications`: nếu JD đánh dấu bắt buộc thì CV phải có đầy đủ.

Stage 3: Scoring
- `title` <-> `title` semantic.
- `skills` <-> `skills` semantic + exact overlap.
- `requirement` <-> `experience` semantic.
- `requirement` <-> `summary` semantic.

Stage 4: Rerank + Return
- apply bonus/penalty rules.
- sort final score, lấy top 10.
- trả response trực tiếp, không persist kết quả.

### FR3. Công thức điểm

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

```
skills_sim = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio
```

### FR4. Reasoning

Reasoning là deterministic template, sinh từ:
- field scores cao nhất.
- số lượng skill exact match.
- penalty nếu thiếu required conditions.

Không dùng LLM.

### FR5. API Surface V2

Namespace: `/api/v2/prototype/matching`
- `POST /job/{job_id}/run`
- `POST /cv/{cv_id}/run`

Không implement GET/DELETE persisted matches trong prototype run-only.

## 4. Data Model (Run-Only Evaluation)

Prototype run-only cần dữ liệu JD/CV và embeddings trong PostgreSQL. Không cần bảng persisted result để kiểm tra matching method.

`match_results_v2` là later-phase table nếu cần lưu kết quả so sánh phương pháp; không tạo hoặc dùng trong prototype run-only.

## 5. Canonical Data Types (Locked)

### 5.1 PostgreSQL - Candidate fields dùng cho matching
- `cv_id`: `BIGINT` (PK/unique business id)
- `title`: `TEXT NOT NULL`
- `skills`: `TEXT[] NOT NULL DEFAULT '{}'`
- `summary`: `TEXT NOT NULL DEFAULT ''`
- `experience`: `TEXT NOT NULL DEFAULT ''`
- `location`: `TEXT NOT NULL` (chỉ nhận `ha_noi|tp_hcm|da_nang`)
- `job_type`: `TEXT NOT NULL` (chỉ nhận `remote|fulltime|parttime`)
- `seniority`: `TEXT NOT NULL`
- `education`: `TEXT NOT NULL` (chỉ nhận `lop_9|lop_12|dai_hoc|thac_si|tien_si`)
- `certifications`: `TEXT[] NOT NULL DEFAULT '{}'`

### 5.2 PostgreSQL - Job fields dùng cho matching
- `job_id`: `BIGINT` (PK/unique business id)
- `title`: `TEXT NOT NULL`
- `skills`: `TEXT[] NOT NULL DEFAULT '{}'`
- `requirement`: `TEXT NOT NULL DEFAULT ''`
- `location`: `TEXT NOT NULL` (chỉ nhận `ha_noi|tp_hcm|da_nang`)
- `job_type`: `TEXT NOT NULL` (chỉ nhận `remote|fulltime|parttime`)
- `seniority`: `TEXT NOT NULL`
- `education`: `TEXT NOT NULL` (chỉ nhận `lop_9|lop_12|dai_hoc|thac_si|tien_si`)
- `required_certifications`: `TEXT[] NOT NULL DEFAULT '{}'`

### 5.3 PostgreSQL - Embedding fields
- Semantic vectors dùng `VECTOR(384)` (pgvector) cho:
  - `emb_title`, `emb_skills`, `emb_requirement`, `emb_summary`, `emb_experience`

### 5.4 PostgreSQL - persisted results
- Không có persisted result table trong prototype run-only.
- Nếu later phase cần persistence, schema phải được chốt lại trước khi tạo `match_results_v2`.

### 5.5 API types (matching v2)
- Path params:
  - `job_id`: `int64`
  - `cv_id`: `int64`
- `RunMatchingV2Request`:
  - `top_k`: `int32` (`1..10`, default `10`)
  - `min_score`: `float64` (`0..1`, default `0.7`)
- `RunMatchingV2Response.matches[*]`:
  - `rank`: `int32`
  - ids: `int64`
  - score fields: `float64`
  - `reasoning`: `string`

## 6. Prototype Validation

- Sanity check: endpoint chạy được với `job_id` và `cv_id` có trong seed.
- Determinism check: cùng input trả cùng rank/order khi dữ liệu không đổi.
- Rule check: hard filters và score formula đúng expected cases.
- Benchmark `Precision`, `Recall`, `NDCG` chỉ làm ở later phase khi có labeled set riêng.

## 7. Test Data Policy

- Cho phép drop/reset toàn bộ database prototype.
- Team có thể seed/insert dữ liệu trực tiếp vào PostgreSQL.
- Không yêu cầu tương thích dữ liệu ngoài 4 bảng PostgreSQL V2.
- Seed data chỉ dùng demo/sanity, không dùng để kết luận quality.

## 8. Acceptance Criteria

- [ ] Chạy được cả JD -> CV và CV -> JD từ ID có sẵn.
- [ ] Mỗi run trả tối đa top 10 + `rank` + breakdown + reasoning.
- [ ] Nếu JD `job_type=remote` thì không áp dụng hard filter `location`.
- [ ] Nếu JD `job_type!=remote` thì `location` filter strict đúng theo text tỉnh/thành.
- [ ] `education` hard filter đúng theo 5 mức taxonomy đã chốt.
- [ ] Không có dependency ingestion/LLM.
- [ ] Không persist kết quả trong prototype run-only.

## 9. Default Decisions (AI-proposed)

- `top_k` default: `10`
- `min_score` default: `0.7`
- Seniority taxonomy prototype: `intern|fresher|junior|mid|senior|lead`; hard filter exact match, không infer alias.
- Skills normalization mặc định: lowercase + trim + unique theo token, chưa áp dụng synonym dictionary ở prototype.
- Bonus/penalty MVP: set `bonus_exact_skill = 0` và `penalty_missing_required = 0` để score formula đơn giản, dễ kiểm chứng.
- Runtime metrics: API run response trả `runtime_ms_total`, `runtime_ms_filter`, `runtime_ms_scoring`, `runtime_ms_sort`.
- Nếu thiếu embedding của một field semantic thì score field đó = `0` (không fail toàn run). Reasoning phải ghi rõ missing embedding cho field tương ứng.
- Nếu thiếu dữ liệu cho hard filter ở JD hoặc CV thì coi như fail hard filter cho cặp đó.
- Tie-break deterministic: sort theo `final_score desc`, sau đó theo deterministic ID asc (`cv_id asc` cho JD -> CV, `job_id asc` cho CV -> JD).
- pgvector/index prototype: không tạo `hnsw`/`ivfflat` index bắt buộc; dùng exhaustive scoring trên seed/test dataset. Chỉ benchmark/index tuning ở later phase.
- Data lifecycle prototype: không persist run result, không TTL, không shadow-run table, không backfill policy.
- API compatibility prototype: repository hiện chỉ giữ namespace V2; không duy trì endpoint ngoài `/api/v2/prototype/*` cho matching/catalog.
- Schema drift: không thêm persisted result fields/tables nếu `docs/REQUIREMENTS.md` chưa đổi scope.

## 10. Open Questions

Prototype run-only không còn open question blocking implementation. Later-phase questions nếu cần sẽ mở lại trong file:
- `docs/backend/HLD/90-matching-v2-open-questions.md`

---

## Addendum A — Catalog Helper Surface (post-spec extension)

Phạm vi spec gốc (mục 1–9) **không đổi**. Phần này ghi lại một bổ sung **read-only** đã được thêm sau khi spec gốc đóng băng, mục đích để frontend có thể duyệt và tìm kiếm dataset V2 trước khi gọi `run`. Bổ sung này **không vi phạm** các invariant của spec gốc (run-only, no persistence, no LLM, 4-table scope-lock).

### Endpoints thêm vào
- `GET /api/v2/prototype/catalog/jobs`, `GET /api/v2/prototype/catalog/cvs` — paginated browse (`limit`, `offset`), order by id ASC.
- `GET /api/v2/prototype/catalog/jobs/{job_id}`, `GET /api/v2/prototype/catalog/cvs/{cv_id}` — single record, 404 khi không tồn tại.
- `POST /api/v2/prototype/catalog/jobs/search`, `POST /api/v2/prototype/catalog/cvs/search` — pgvector cosine semantic search; body `{q, top_k≤50, blend_skills∈[0,1], location?, job_type?, seniority?}`.

### Tại sao không vi phạm scope gốc
- Không có endpoint nào ghi vào DB.
- Không tạo thêm bảng (vẫn 4 bảng: `job_posts_v2`, `candidate_profiles_v2`, `job_embeddings_v2`, `candidate_embeddings_v2`).
- Không gọi LLM runtime; embedder hash-based deterministic dùng cho query là chính module đã sinh ra embeddings lưu trữ (`backend/v2_search/embedder.py` → `db_v2/scenario/embedder.py`). Cosine giữa query vector và stored vector valid về mặt toán học.
- Search blend formula: `score = (1 - blend_skills) * cos(emb_title, q_vec) + blend_skills * cos(emb_skills, q_vec)`, clamp `[0, 1]`. Không phải `final_score` của FR3 và không persist.

### Filter contract
Filter `location/job_type/seniority` áp dụng trong SQL CTE WHERE trước khi scoring, dùng cùng enum cứng đã định nghĩa ở mục 3 (`ha_noi/tp_hcm/da_nang`, `remote/fulltime/parttime`, `intern/fresher/junior/mid/senior/lead`). Pydantic Literal reject 422 nếu sai enum.

### Out-of-scope addendum
- KHÔNG có ingestion / parse / upload (giống spec gốc).
- KHÔNG persist search results.
- KHÔNG có "save anchor to catalog" — anchor chỉ qua `POST /run` với ID có sẵn.
- KHÔNG thay đổi formula `final_score` của matching (mục FR3).
