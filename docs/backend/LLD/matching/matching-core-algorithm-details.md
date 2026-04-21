# LLD: Matching Core Algorithm Details

## Source Anchors
- `backend/ragmodel/logics/matchingLogic.py`
- `backend/ragmodel/logics/llmEvaluate.py`
- `backend/ragmodel/db/vectorStore.py`

## Scope Boundary
This file owns algorithm and scoring internals only.
Service orchestration/persistence is owned by:
- `matching-orchestration-and-topk-sync.md`

## Config Constants
`MatchingConfig` defaults:
- `ANN_K = 50`
- `RERANK_K = 10`
- `FINAL_K = 5`

Field weights:
- skills: `0.30`
- experience_requirement: `0.25`
- summary_description: `0.20`
- job_title: `0.15`
- full: `0.05`
- location: `0.05`

Hybrid weights:
- ANN: `0.2`
- weighted similarity: `0.5`
- LLM: `0.3`

## Field Mapping Contract
`CV_JD_FIELD_MAP`:
- summary_description: (`emb_summary`, `emb_job_description`)
- experience_requirement: (`emb_experience`, `emb_job_requirement`)
- job_title: (`emb_job_title`, `emb_job_title`)
- skills: (`emb_skills`, `emb_skills`)
- location: (`emb_location`, `emb_location`)
- full: (`emb_full`, `emb_full`)

## Shared Helpers
- `deserialize_embeddings`: JSON string -> numpy vectors
- `cosine`: safe similarity; returns `0.0` for missing/shape mismatch
- `calc_weighted_vector_sim`: field-by-field weighted sum
- `normalize_llm_score`: clamp score to `[0,100]`

## Direction: JD -> CV (`get_top_k_cvs_for_jd`)
Stages:
1. Build JD embeddings.
2. ANN query on `cv_full` using `emb_full`.
3. Weighted rerank using field mapping.
4. Run LLM evaluation on reranked candidates.
5. Compute hybrid final score and return top-k.

## Direction: CV -> JD (`get_top_k_jds_for_cv`)
Symmetric stages:
1. Build CV embeddings.
2. ANN query on `jd_full`.
3. Weighted rerank.
4. LLM evaluation.
5. Hybrid final scoring.

## Final Score Formula
`final = 0.2*cosine_ann + 0.5*weighted_sim + 0.3*(llm_score/100)`

## LLM Evaluation Contract
Function:
- `evaluate_match(jd_text, cv_text)`

Expected return:
- `score` (0-100)
- `reason` (string)

LLM fallback in matching logic:
- if LLM call fails:
  - `llm_score = weighted_sim * 100`
  - reason set to fallback message.

## Pairwise Direct Match
Function:
- `match_jd_to_cv(jd_id, cv_id)`

Returns:
- field-level scores
- weighted final score

Used by per-pair endpoints in CV/Job repositories.

## Related LLD
- Service persistence orchestration: `matching-orchestration-and-topk-sync.md`
- Query enrichment and cleanup semantics: `match-query-enrichment-and-cleanup-flows.md`
- Embedding/vector contracts: `../rag/embedding-and-chromadb-metadata-contract.md`
