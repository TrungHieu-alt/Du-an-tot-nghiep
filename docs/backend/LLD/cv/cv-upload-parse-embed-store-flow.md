# LLD: CV Upload Parse Embed Store Flow

## Source Anchors
- `backend/routers/cv_router.py`
- `backend/services/cv_service.py`
- `backend/repositories/cv_repo.py`
- `backend/ragmodel/dataPreprocess/resumePreprocess.py`
- `backend/ragmodel/dataPreprocess/resumeParser.py`
- `backend/ragmodel/logics/embedder.py`
- `backend/ragmodel/db/vectorStore.py`

## Scope Boundary
This file owns ingestion pipeline behavior only.
Manual CRUD semantics are owned by:
- `cv-manual-crud-and-main-cv-flow.md`

## Entry Endpoints
- `POST /api/cv/upload/{user_id}` with multipart file
- `POST /api/cv/upload-text/{user_id}` with form text

## Upload File Flow (`upload_file`)
1. Service inspects uploaded filename extension.
2. For PDF:
   - writes temporary `.pdf` file
   - delegates to `upload_cv_from_pdf`
   - removes temp file in `finally`
3. For non-PDF:
   - decodes bytes as UTF-8 text
   - delegates to `upload_cv_from_text`

Failure surface:
- Any exception maps to HTTP 400 in service.

## PDF/Text Ingestion Core
Common sequence in repository:
1. Preprocess source text via `preprocess_resume(...)`.
2. Parse structured CV fields via `parse_resume(...)`.
3. If parser output misses `full_text`, fill with preprocessed text.
4. Create embeddings via `embed_cv(...)`.
5. Insert Mongo CV row first to allocate numeric `cv_id`.
6. Compose Chroma ID `cv_{cv_id}`.
7. Upsert embeddings + metadata to Chroma with `vs.store_cv(...)`.

## Mongo vs Chroma Write Ordering
Current order:
- Mongo insert first
- Chroma write second

Implication:
- If Chroma fails after Mongo success, a CV exists without vector index.

## Metadata Fields Sent to Chroma
Repository sends `cv_data_with_user` including:
- parser data
- `user_id`
- `cv_id`

Current `vectorStore.store_cv` persists only selected keys:
- `embeddings` (JSON string)
- `full_text`, `summary`, `experience`, `skills` (JSON string), `job_title`, `location`

## Parser/Embed Contracts (Referenced)
Detailed contracts are owned by:
- `../rag/resume-preprocess-and-parse-details.md`
- `../rag/embedding-and-chromadb-metadata-contract.md`

## Delete Coupling
CV delete path in CRUD repository also deletes `cv_{cv_id}` in Chroma.
This ensures best-effort cross-store cleanup.

## Related LLD
- CV manual CRUD: `cv-manual-crud-and-main-cv-flow.md`
- Resume preprocess/parser internals: `../rag/resume-preprocess-and-parse-details.md`
- Embedding/metadata contract: `../rag/embedding-and-chromadb-metadata-contract.md`
- Cross-store consistency risks: `../data/cross-store-consistency-and-failure-modes.md`
