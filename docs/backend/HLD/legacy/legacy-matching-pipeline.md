# Backend HLD V2: Matching Run-Only Pipeline

> Legacy prototype HLD. This file preserves the deterministic matching formula
> and run-only prototype pipeline used by current tests. Use
> `docs/backend/HLD/40-matching-and-search-pipeline.md` for target
> MVP matching/search architecture.

## Goal

Kiểm tra nhanh matching method trên dữ liệu đã có trong PostgreSQL bằng cách nhập `job_id` hoặc `cv_id` và nhận ranked matches có điểm + reasoning.

## Pipeline Stages

1. Load anchor + candidate pool
- Input là `job_id` hoặc `cv_id`.
- Đọc record + embeddings hiện có trong PostgreSQL.
- Prototype dùng exhaustive candidate scoring trên dataset test; chưa cần ANN/index tuning.

2. Hard filters
- Hard filter áp dụng hai chiều trên trường chung giữa JD và CV.
- `job_type` chỉ nhận `remote|fulltime|parttime`.
- Nếu JD `job_type=remote` thì bỏ qua hard filter `location`.
- Nếu JD `job_type!=remote` thì `job_type` và `location` phải khớp exact giữa JD và CV.
- `seniority`: cả JD và CV đều phải có và phải khớp.
- `education` hard filter theo thứ bậc taxonomy: `lop_9` < `lop_12` < `dai_hoc` < `thac_si` < `tien_si` (cả JD và CV đều phải có).
- Rule pass: education CV >= education JD.
- `required_certifications`: nếu JD flagged required thì CV phải có đầy đủ.

3. Scoring
- `title_sim`, `skills_sim`, `req_exp_sim`, `req_summary_sim`.
- `skills_sim = 0.6 * semantic + 0.4 * exact_overlap`.

4. Rerank and return
- apply bonus/penalty.
- sort theo final score, lấy top 10.
- trả response trực tiếp, không persist kết quả.

## Final Score

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

## Output Contract

Mỗi run trả:
- top 10 matches.
- `rank` cho từng match.
- score breakdown.
- rule-based reasoning.
- `runtime_ms_total` và runtime theo stage.

## Out of Scope For Run-Only Prototype

- Persist/query/delete match results.
- Benchmark quality bằng labeled set.
- Auth/role guard riêng cho route prototype.
- Compare with pipelines outside the V2 prototype.
