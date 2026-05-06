# REQUIREMENTS.md — Job Matcher V2 (Prototype Target)

## 1. Mục tiêu

Job Matcher V2 là prototype matching CV–JD hai chiều, ưu tiên tính khả thi và khả năng đo lường trước khi thay đổi hệ thống production.

Mục tiêu V2:
- Chuyển storage matching sang PostgreSQL + pgvector.
- Tách API prototype riêng dưới `/api/v2/prototype/*`.
- Dùng engine matching MVP không phụ thuộc LLM.
- Giữ logic dễ audit: hard filters + embedding score + rule rerank.

## 2. Phạm vi và vai trò

- Candidate: upload CV, chạy match CV -> jobs.
- Recruiter: upload JD, chạy match JD -> CVs.

Out of scope cho MVP V2:
- LLM reasoning trong scoring.
- Matching dựa full text end-to-end.
- Salary-based ranking.

## 3. Functional Requirements

### FR1. Ingestion và chuẩn hóa dữ liệu

Pipeline ingestion V2:
1. Parse CV/JD thành structured fields.
2. Normalize text theo dictionary/domain rules.
3. Tạo embeddings cho các field có dùng semantic match.
4. Ghi records vào PostgreSQL.
5. Ghi vector vào cột `vector` (pgvector) cùng version metadata.

Field chính V2:
- CV: `title`, `skills`, `summary`, `experience`, `location`, `job_type`, `seniority`, `education`, `certifications`, `full_text`.
- JD: `title`, `skills`, `requirement`, `location`, `job_type`, `seniority`, `education_required`, `required_certifications`, `salary_min`, `salary_max`, `full_text`.

### FR2. Matching Pipeline V2 (MVP)

Stage 1 — Hard filters:
- `location`
- `job_type`
- `seniority`
- `education` (khi JD đánh dấu bắt buộc)
- `required_certifications` (khi JD đánh dấu bắt buộc)

Stage 2 — Embedding + exact scoring:
- `title` <-> `title` (semantic)
- `skills` <-> `skills` (semantic + exact overlap)
- `requirement` <-> `summary` (semantic)
- `requirement` <-> `experience` (semantic, ưu tiên cao hơn summary khi CV ngắn)

Stage 3 — Business rerank:
- Boost theo số lượng skill exact match.
- Penalty khi thiếu skill/certification bắt buộc.

Không dùng ở MVP:
- `full_text` semantic matching.
- Salary trong final score.
- LLM evaluation.

### FR3. Công thức điểm MVP

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

Trong đó:
- `skills_sim = 0.6 * cosine(emb_skills) + 0.4 * exact_overlap_ratio`
- Tất cả điểm chuẩn hóa về `[0,1]` trước khi tổng hợp.

### FR4. Persistence

`match_results_v2` lưu:
- `cv_id`, `job_id`
- `final_score`
- `title_score`, `skills_score`, `req_exp_score`, `req_summary_score`
- `exact_skill_bonus`, `required_penalty`
- `filter_fail_reasons` (nếu cần debug/shadow)
- `feature_version`, `embedding_model_version`, `scoring_version`
- `created_at`, `updated_at`

### FR5. API Surface V2

Namespace chính:
- `POST /api/v2/prototype/matching/job/{job_id}/run`
- `POST /api/v2/prototype/matching/cv/{cv_id}/run`
- `GET /api/v2/prototype/matching/job/{job_id}/matches`
- `GET /api/v2/prototype/matching/cv/{cv_id}/matches`
- `DELETE /api/v2/prototype/matching/job/{job_id}/matches`
- `DELETE /api/v2/prototype/matching/cv/{cv_id}/matches`

Nguyên tắc:
- Route v2 chạy tách biệt với route production hiện hữu.
- Response phải trả score breakdown để audit.

## 4. Data Model Canonical V2

Bảng chính (đặt tên gợi ý):
- `candidate_profiles_v2`
- `job_posts_v2`
- `candidate_embeddings_v2`
- `job_embeddings_v2`
- `match_results_v2`

Vector/index:
- pgvector column: `embedding vector(<dim>)`
- ANN index theo lựa chọn benchmark (`hnsw` hoặc `ivfflat`)

## 5. Non-functional Requirements

- p95 latency match run theo target nội bộ của team.
- Mọi run phải reproducible theo `feature_version` và `scoring_version`.
- Có khả năng shadow run để so sánh với pipeline hiện tại.
- Không ảnh hưởng API production hiện hữu trong giai đoạn thử nghiệm.

## 6. Acceptance Criteria (Prototype V2)

Prototype V2 đạt khi:
- [ ] Chạy end-to-end CV->JD và JD->CV trên PostgreSQL + pgvector.
- [ ] Hard filters hoạt động đúng theo rule bắt buộc.
- [ ] Kết quả có đầy đủ score breakdown từng thành phần.
- [ ] Không phụ thuộc LLM để hoàn thành pipeline.
- [ ] Route `/api/v2/prototype/*` hoạt động độc lập.
- [ ] Có benchmark cơ bản so sánh chất lượng/latency với baseline.

## 7. Rủi ro và ghi chú

- Mapping seniority/education liên miền cần taxonomy thống nhất.
- Index tuning (`hnsw`/`ivfflat`) ảnh hưởng mạnh đến recall/latency.
- Exact skill matching cần normalizer (alias/synonym) để tránh miss.

## 8. Open Questions

Các quyết định chưa chốt được tập trung trong:
- `docs/backend/HLD/90-matching-v2-open-questions.md`
