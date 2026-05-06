# LLD V2: Matching Core Algorithm Details

## Scope

Tài liệu này mô tả thuật toán matching MVP v2 (không LLM) cho prototype.

## Constants

- `ANN_K` default: 100
- `RERANK_K` default: 30
- `FINAL_K` default: 10

## Hard Filters

Bắt buộc kiểm tra trước scoring:
- `location`
- `job_type`
- `seniority`
- `education` (khi JD yêu cầu)
- `required_certifications` (khi JD yêu cầu)

## Field Mapping

- `title_sim`: `job.title` <-> `cv.title`
- `skills_semantic`: `job.skills` <-> `cv.skills`
- `req_exp_sim`: `job.requirement` <-> `cv.experience`
- `req_summary_sim`: `job.requirement` <-> `cv.summary`

## Skills Hybrid Score

```
skills_sim = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio
```

## Final Score

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

## Notes

- `full_text` không dùng trong điểm MVP.
- Salary không dùng trong điểm MVP.
- Kết quả luôn trả breakdown từng thành phần để audit.
