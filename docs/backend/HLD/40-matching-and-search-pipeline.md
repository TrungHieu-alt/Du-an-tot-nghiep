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
- Local cross-encoder reranking is attempted on top 10 candidates after
  deterministic pre-ranking.
- If reranker is unavailable, runtime falls back to deterministic scoring and
  exposes fallback warnings in matching runtime metadata.
- Tie-break is deterministic: `final_score DESC`, then `resume_id ASC` for
  job anchors or `job_id ASC` for resume anchors.

Runtime metrics include `total_ms`, `retrieval_ms`, `filter_ms`, `scoring_ms`,
`rerank_ms`, candidate counts before/after hard filters, rerank-applied flag,
and warning notes.

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
  optional structured filters. Job search ranks against JD requirement
  embeddings. Resume search ranks against CV summary and experience embeddings,
  not title embeddings.
- Semantic search scores are retrieval relevance, not final matching scores.

## Embedding Provider Boundary (Slice 7)

Implementations live under `backend/src/jobconnect/integrations/embedding/`:

- `base.py` defines the `EmbeddingProvider` Protocol (`embed`, `dim`,
  `embedding_version`) and the `EmbeddingError` exception. `EMBEDDING_DIM = 384`
  is fixed by the DB schema (`VECTOR(384)`).
- `local.py` exposes `LocalHashEmbeddingProvider` wrapping the Slice 0
  SHA-256-seeded bag-of-words embedder. `embedding_version = "hash-v1"`.
- `openai.py` exposes `OpenAIEmbeddingProvider` calling `/v1/embeddings` with
  `dimensions=384` (supported by `text-embedding-3-*`). Vectors with the wrong
  length raise `EmbeddingError` rather than being silently padded.
  `embedding_version = "openai-{model}-v1"`.

Selection happens in `get_embedding_provider()` based on env:

| Var | Default | Notes |
|---|---|---|
| `EMBEDDING_PROVIDER` | `local` | `local` or `openai`. Unknown values fall back to local. |
| `OPENAI_EMBEDDING_API_KEY` | _(unset)_ | Falls back to `OPENAI_API_KEY` if unset. Required for `openai` provider; missing → factory falls back to local. |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedded in `embedding_version`. |
| `OPENAI_EMBEDDING_BASE_URL` | `https://api.openai.com/v1` | For compatible endpoints / proxies. |
| `OPENAI_EMBEDDING_TIMEOUT_SECONDS` | `30` | httpx request timeout. |

Failure handling:

- Network / HTTP / decode / dimension-mismatch errors raise `EmbeddingError`.
- Worker pipeline catches `EmbeddingError` → marks parse job `failed` with
  `error_code = embedding_failed`; the uploaded file is preserved.
- Direct call sites (router CRUD upserts, semantic-search query embed) currently
  let the exception bubble; production hardening (Slice 8) will wrap them in a
  user-visible 503 envelope.

Re-embedding / backfill: when `embedding_version` advances, operators run a
backfill script that re-embeds existing rows. The version column on each
embedding row makes the impacted set discoverable with a single
`WHERE embedding_version <> '<new>'` query.
