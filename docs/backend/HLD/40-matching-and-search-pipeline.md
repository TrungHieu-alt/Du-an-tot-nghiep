# Production HLD: Matching And Search Pipeline

## Goal

Rank eligible JD <-> CV pairs with explainable scoring while keeping search
intent separate from matching intent.

## Eligibility

- Job -> resume matching accepts a published `job_id` and ranks active resumes.
- Resume -> job matching accepts an active `resume_id` and ranks published jobs.
- Disabled users cannot run marketplace actions.
- Draft, archived, and closed entities are excluded.

## Hard Filters

- `job_type`: `remote | fulltime | parttime`.
- Remote jobs ignore location hard filter.
- Non-remote jobs require exact `job_type` and `location` match.
- `seniority` must match exactly.
- CV education must be greater than or equal to job required education:

```text
lop_9 < lop_12 < dai_hoc < thac_si < tien_si
```

- Job required certifications must be a subset of CV certifications.
- Missing hard-filter data fails the pair.

## Scoring

Initial MVP keeps the prototype score formula:

```text
final_score =
  0.35 * title_sim +
  0.35 * skills_sim +
  0.20 * req_exp_sim +
  0.10 * req_summary_sim +
  bonus_exact_skill - penalty_missing_required
```

```text
skills_sim = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio
```

Defaults:

- `top_k = 10`, allowed `1..50`.
- `min_score = 0.7`, allowed `0..1`.
- bonus and penalty values remain `0` until measured rules are introduced.

## Retrieval And Reranking

- Embedding retrieval produces the candidate set.
- Formula scoring remains the deterministic fallback.
- Optional cross-encoder reranking may apply to top 10-20 candidates.
- Tie-break is deterministic: `final_score DESC`, then `resume_id ASC` for
  job anchors or `job_id ASC` for resume anchors.

## Reasoning

Reasoning must be grounded in score breakdown and structured fields:

- strongest score components.
- exact skill overlap count.
- hard-filter pass notes.
- missing embedding notes.

LLM-generated reasoning is allowed only if grounded in the score breakdown and
must not invent facts.

## Search Separation

Keyword search and semantic search are separate APIs and UI intents.

- Keyword search: names, email when permitted, organization, job title, resume
  title, and exact structured lookup.
- Semantic search: description-style queries over job/resume meaning, with
  optional structured filters.
- Semantic search scores are retrieval relevance, not final matching scores.

