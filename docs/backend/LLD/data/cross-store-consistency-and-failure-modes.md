# LLD: Cross-Store Consistency and Failure Modes

## Source Anchors
- `backend/repositories/cv_repo.py`
- `backend/repositories/job_repo.py`
- `backend/repositories/match_repo.py`
- `backend/ragmodel/db/vectorStore.py`

## Ownership Model
- MongoDB is source of truth for business entities and persisted matches.
- ChromaDB is retrieval infrastructure for semantic search.

## Write Paths Involving Both Stores
1. CV upload flow:
- Mongo insert CV first
- Chroma write second

2. Job upload flow:
- Mongo insert Job first
- Chroma write second

3. Match run flow:
- retrieve from Chroma
- persist selected rows in Mongo `match_results`

## Delete Paths Involving Both Stores
1. CV delete:
- attempt Chroma delete `cv_{cv_id}`
- then delete Mongo CV

2. Job delete:
- attempt Chroma delete `jd_{job_id}`
- then delete Mongo Job

3. Match cleanup/delete:
- Mongo only (`match_results`)

## Non-Transactional Boundary
No distributed transaction exists between Mongo and Chroma.

Possible divergence cases:
- Mongo success + Chroma failure on upload -> entity exists but may not be retrievable semantically.
- Chroma delete failure + Mongo delete success -> orphaned vectors.

Current strategy:
- best-effort Chroma operations with logging
- exceptions often propagated for upload paths
- safe empty-result behavior in matching retrieval paths

## Matching-Time Fallback Behavior
If LLM evaluation fails:
- use weighted similarity as LLM proxy.

If embeddings missing/invalid for candidate:
- candidate skipped or given safe low contribution.

If ANN query returns empty:
- matching returns empty result set without crashing.

## Operational Gaps
- no retry queue for cross-store reconciliation
- no background orphan sweeper
- no idempotency keys on ingestion writes

## Related LLD
- CV and Job ingestion pipelines: `../cv/cv-upload-parse-embed-store-flow.md`, `../jobs/job-upload-parse-embed-store-flow.md`
- Embedding and metadata contract: `../rag/embedding-and-chromadb-metadata-contract.md`
- Matching pipeline behavior: `../matching/matching-core-algorithm-details.md`
