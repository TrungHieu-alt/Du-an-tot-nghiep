# LLD: Embedding and ChromaDB Metadata Contract

## Source Anchors
- `backend/ragmodel/logics/embedder.py`
- `backend/ragmodel/db/vectorStore.py`
- `backend/repositories/cv_repo.py`
- `backend/repositories/job_repo.py`

## Scope Boundary
This file is authoritative for:
- Embedding field schema
- Chroma collection names
- Metadata serialization/deserialization behavior

## Embedding Model Contract
Model:
- `sentence-transformers/all-MiniLM-L6-v2`

Helper:
- `emb(text)` returns normalized vector or `None` for empty input.

Implications:
- similarity uses dot product as cosine proxy.
- missing field embeddings are explicit `None`, not zero vectors.

## CV Embedding Schema (`embed_cv`)
Produced keys:
- `emb_summary`
- `emb_experience`
- `emb_job_title`
- `emb_skills`
- `emb_location`
- `emb_full`

Input mapping:
- skills list is joined into one text string before embedding.

## JD Embedding Schema (`embed_jd`)
Produced keys:
- `emb_job_description`
- `emb_job_requirement`
- `emb_job_title`
- `emb_skills`
- `emb_location`
- `emb_full`

## Vector Store Collections
Persistent client path:
- `backend/ragmodel/vector_store`

Collections:
- `cv_full`
- `jd_full`

## Chroma Record ID Contract
- CV: `cv_{cv_id}`
- JD: `jd_{job_id}`

Used consistently for add/get/delete across repositories and matching logic.

## Metadata Serialization Rules
Because Chroma metadata supports primitives only:
- full embedding dict stored as JSON string in `metadata["embeddings"]`
- `skills` stored as JSON string
- text fields stored as strings

## Deserialization Contract
Matching logic expects:
- `metadata["embeddings"]` JSON string -> dict -> numpy arrays

If decode fails:
- candidate skipped or score falls back to safe defaults.

## Drift Notes
1. `skills` is serialized JSON string in Chroma metadata, but consumer paths often read it as list-like data without explicit `json.loads`.
2. Repositories provide extra metadata (for example `user_id`, `recruiter_id`) that `vectorStore.store_cv/store_jd` currently do not persist.

## Related LLD
- Matching algorithm consumers: `../matching/matching-core-algorithm-details.md`
- CV/JD ingestion orchestrators: `../cv/cv-upload-parse-embed-store-flow.md`, `../jobs/job-upload-parse-embed-store-flow.md`
- Cross-store risks: `../data/cross-store-consistency-and-failure-modes.md`
