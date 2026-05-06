# Backend HLD V2: Matching Pipeline

## Goal

Pipeline V2 tối ưu cho prototype tách biệt: dễ đo lường, dễ debug, không phụ thuộc LLM.

## Pipeline Stages

1. Hard Filter
- location
- job_type
- seniority
- education (nếu bắt buộc)
- required_certifications (nếu bắt buộc)

2. Semantic + Exact Scoring
- title <-> title (embedding cosine)
- skills <-> skills (embedding + exact overlap)
- requirement <-> experience (embedding cosine)
- requirement <-> summary (embedding cosine)

3. Rule Rerank
- boost exact skill overlap
- penalty thiếu required skills/certifications

4. Persist
- lưu kết quả top-k và score breakdown vào `match_results_v2`

## Scoring Formula

```
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

`skills_sim = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio`

## Exclusions in MVP

- No LLM stage.
- No full_text semantic scoring in final score.
- No salary scoring.

## Directional Modes

- JD -> CV: query candidates theo job anchor.
- CV -> JD: query jobs theo cv anchor.

Cả hai dùng chung trọng số và rule.
