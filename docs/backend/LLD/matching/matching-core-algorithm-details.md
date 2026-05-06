# LLD V2: Matching Core Algorithm (Run-Only)

## Scope

Thuật toán matching MVP v2 chạy trên dữ liệu đã có trong PostgreSQL/pgvector và trả kết quả trực tiếp, không persist.

## Inputs

- Mode 1: `job_id` (`BIGINT`) -> top CVs.
- Mode 2: `cv_id` (`BIGINT`) -> top Jobs.

## Defaults

- `FINAL_K = 10`
- Candidate pool: exhaustive scan over prototype seed/test data.
- ANN/index tuning is outside run-only prototype scope.

## Hard filters

- Hard filter áp dụng hai chiều trên trường chung giữa JD và CV.
- `job_type`: chỉ nhận `remote|fulltime|parttime`.
- Nếu JD `job_type=remote` thì bỏ qua hard filter `location`.
- Nếu JD `job_type!=remote` thì `job_type` và `location` phải khớp exact giữa JD và CV.
- `seniority`: cả JD và CV đều phải có và phải khớp.
- `education` hard filter theo thứ bậc taxonomy: `lop_9` < `lop_12` < `dai_hoc` < `thac_si` < `tien_si` (cả JD và CV đều phải có).
- Rule pass: education CV >= education JD.
- `required_certifications`: nếu JD đánh dấu required thì CV phải có đầy đủ.

## Component scores

- `title_sim`: semantic(title, title)
- `skills_sim`: `0.6 * semantic(skills) + 0.4 * exact_overlap(skills)`
- `req_exp_sim`: semantic(requirement, experience)
- `req_summary_sim`: semantic(requirement, summary)

## Final score

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

## Reasoning

Reasoning được sinh theo template rule-based:
- Nêu 2-3 tín hiệu mạnh nhất theo component scores.
- Nêu penalty nếu thiếu required skills/certifications.

## Data type notes

- Score fields in API response: `float64`.
- `reasoning`: `TEXT`.
- `education`: taxonomy `lop_9|lop_12|dai_hoc|thac_si|tien_si` and compared by rank order.
- Each returned match includes deterministic `rank`.
