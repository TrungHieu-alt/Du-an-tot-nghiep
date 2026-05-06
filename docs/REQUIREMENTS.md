# REQUIREMENTS.md — Matching Prototype V2 (Evaluation-Only)

## 1. Mục tiêu

Prototype V2 dùng để đánh giá thiết kế matching method trên dữ liệu đã có trong PostgreSQL:
- Logic matching chạy như thế nào.
- Thời gian chạy theo từng stage.
- Độ chính xác trên tập benchmark gán nhãn.

Prototype này không xử lý ingestion/parse/extract dữ liệu. Dữ liệu test được insert trực tiếp vào PostgreSQL để đánh giá matching logic.

## 2. Phạm vi

In scope:
- Chạy matching từ input ID có sẵn trong DB (`job_id` hoặc `cv_id`).
- Trả top 10 kết quả tốt nhất.
- Trả score breakdown, reasoning, runtime metrics.
- Persist kết quả phục vụ so sánh phương pháp.

Out of scope:
- Thu thập/bóc tách/chuẩn hóa dữ liệu đầu vào
- Mọi flow extract/upload/parse tài liệu.
- LLM scoring/reasoning.
- Salary và full_text trong scoring MVP.

## 3. Functional Requirements

### FR1. Input/Output runtime

Input:
- `job_id` cho mode JD -> CV.
- `cv_id` cho mode CV -> JD.

Output mỗi run:
- top 10 matches.
- score breakdown từng thành phần.
- reasoning dạng rule-based.

### FR2. Matching pipeline MVP

Stage 1: Load data
- Đọc anchor và candidate pool từ PostgreSQL/pgvector.

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

Stage 4: Rerank + Persist
- apply bonus/penalty rules.
- sort final score, lấy top 10.
- persist vào `match_results_v2`.

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
- `GET /job/{job_id}/matches`
- `GET /cv/{cv_id}/matches`
- `DELETE /job/{job_id}/matches`
- `DELETE /cv/{cv_id}/matches`

## 4. Data Model (Evaluation)

`match_results_v2` lưu:
- `cv_id`, `job_id`, `final_score`
- `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`
- `reasoning`

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

### 5.4 PostgreSQL - match_results_v2
- `cv_id`: `BIGINT NOT NULL`
- `job_id`: `BIGINT NOT NULL`
- `final_score`: `DOUBLE PRECISION NOT NULL`
- `title_score`: `DOUBLE PRECISION NOT NULL`
- `skills_score`: `DOUBLE PRECISION NOT NULL`
- `req_exp_score`: `DOUBLE PRECISION NOT NULL`
- `req_summary_score`: `DOUBLE PRECISION NOT NULL`
- `reasoning`: `TEXT NOT NULL`
- Unique key: `(cv_id, job_id)`

### 5.5 API types (matching v2)
- Path params:
  - `job_id`: `int64`
  - `cv_id`: `int64`
- `RunMatchingV2Request`:
  - `top_k`: `int32` (`1..10`, default `10`)
  - `min_score`: `float64` (`0..1`, default `0.7`)
- `RunMatchingV2Response.matches[*]`:
  - ids: `int64`
  - score fields: `float64`
  - `reasoning`: `string`

## 6. Metrics đánh giá prototype

Accuracy:
- `Precision`
- `Recall`
- `NDCG`

## 7. Test Data Policy

- Cho phép drop/reset toàn bộ database prototype.
- Team có thể seed/insert dữ liệu trực tiếp vào PostgreSQL.
- Không yêu cầu tương thích dữ liệu legacy production.

## 8. Acceptance Criteria

- [ ] Chạy được cả JD -> CV và CV -> JD từ ID có sẵn.
- [ ] Mỗi run trả tối đa top 10 + breakdown + reasoning.
- [ ] Nếu JD `job_type=remote` thì không áp dụng hard filter `location`.
- [ ] Nếu JD `job_type!=remote` thì `location` filter strict đúng theo text tỉnh/thành.
- [ ] `education` hard filter đúng theo 5 mức taxonomy đã chốt.
- [ ] Không có dependency ingestion/LLM.
- [ ] Có báo cáo benchmark accuracy + latency từ labeled set.

## 9. Default Decisions (AI-proposed)

- `top_k` default: `10`
- `min_score` default: `0.7`
- Skills normalization mặc định: lowercase + trim + unique theo token, chưa áp dụng synonym dictionary ở MVP.
- Nếu thiếu embedding của một field semantic thì score field đó = `0` (không fail toàn run).
- Nếu thiếu dữ liệu cho hard filter ở JD hoặc CV thì coi như fail hard filter cho cặp đó.

## 10. Open Questions

Xem file:
- `docs/backend/HLD/90-matching-v2-open-questions.md`
