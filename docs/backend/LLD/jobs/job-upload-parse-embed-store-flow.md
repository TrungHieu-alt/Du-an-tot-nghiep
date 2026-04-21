# LLD: Job Upload Parse Embed Store Flow

## Source Anchors
- `backend/routers/job_router.py`
- `backend/services/job_service.py`
- `backend/repositories/job_repo.py`
- `backend/ragmodel/dataPreprocess/jobPreprocess.py`
- `backend/ragmodel/dataPreprocess/jobParser.py`
- `backend/ragmodel/logics/embedder.py`
- `backend/ragmodel/db/vectorStore.py`

## Scope Boundary
This file owns ingestion pipeline behavior only.
Manual CRUD is owned by:
- `job-manual-crud-flow.md`

## Entry Endpoints
- `POST /api/jobs/upload/{recruiter_id}` (multipart file + optional override fields)
- `POST /api/jobs/upload-text/{recruiter_id}` (form text + optional override fields)

## Upload File Flow (`upload_file`)
1. Service checks filename extension.
2. PDF path:
   - write temp `.pdf`
   - call `upload_job_from_pdf`
   - cleanup temp in `finally`
3. Non-PDF path:
   - decode text
   - call `upload_job_from_text`

Error mapping:
- failures are wrapped as HTTP 400.

## Repository Ingestion Core
Common sequence:
1. Preprocess with `preprocess_jd(...)`.
2. Parse structured fields with `parse_jd(...)`.
3. Fill `full_text` from preprocessed content if parser omitted it.
4. Build embeddings via `embed_jd(...)`.
5. Insert Mongo `JobPost` first (`job_id=max+1`).
6. Compose Chroma ID `jd_{job_id}`.
7. Store vector + metadata via `vs.store_jd(...)`.

## Parsed vs Manual Override Precedence
When creating Mongo row:
- Router/service-supplied fields take precedence over parsed fields.
- Defaults used when both absent:
  - `job_type="Full-time"`
  - `experience_level="Mid-level"`

## Chroma Metadata Contract (Job)
Repository sends enriched metadata including recruiter/job IDs and profile fields.
Current vector store persists selected keys only:
- `embeddings` (JSON string)
- `full_text`, `job_description`, `job_requirement`, `skills` (JSON string), `job_title`, `location`

## Consistency Behavior
Write order is Mongo first, Chroma second.
This can leave a non-indexed Job row if Chroma write fails.

## Delete Coupling
Manual delete path attempts Chroma cleanup `jd_{job_id}` before Mongo delete.

## Related LLD
- Job manual CRUD: `job-manual-crud-flow.md`
- JD preprocess/parser internals: `../rag/job-preprocess-and-parse-details.md`
- Embedding and metadata details: `../rag/embedding-and-chromadb-metadata-contract.md`
- Cross-store risks: `../data/cross-store-consistency-and-failure-modes.md`
