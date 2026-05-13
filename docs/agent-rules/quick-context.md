# Quick Context

Purpose: concise system reality snapshot for V2 target documentation.

## Product Snapshot
- Backend-first job matching system, V2 run-only prototype direction.
- Core outcome: input one `job_id` or `cv_id`, return ranked CV <-> JD matches with score breakdown and reasoning.

## Runtime Components (V2 Target)
- API server: FastAPI (`backend/main.py`).
- Primary data store: PostgreSQL.
- Vector storage/scoring: `pgvector` in PostgreSQL.
- Matching engine (MVP): hard filters + exhaustive embedding scoring over prototype data + deterministic rerank.

## Current Behavior Target (V2)
- Prototype route namespace: `/api/v2/prototype/{matching,matching-hybrid,catalog}/*`.
- Run-only matching surface: `POST /api/v2/prototype/matching/job/{job_id}/run` and `POST /api/v2/prototype/matching/cv/{cv_id}/run`.
- Additive hybrid matching surface: `POST /api/v2/prototype/matching-hybrid/job/{job_id}/run` and `POST /api/v2/prototype/matching-hybrid/cv/{cv_id}/run`; uses the same four V2 tables, returns `0..100` scores, and preserves the original matcher contract.
- Read-only catalog helper surface (added for frontend browse/search; does not violate run-only scope): `GET /api/v2/prototype/catalog/{jobs,cvs}` and `/{jobs,cvs}/{id}` paginated browse + detail, plus `POST /api/v2/prototype/catalog/{jobs,cvs}/search` for pgvector cosine semantic search with optional `location/job_type/seniority` filters.
- Matching MVP does not require LLM stage.
- Embedding runtime uses only local `sentence-transformers/all-MiniLM-L6-v2`;
  no external AI/embedding API key is required.
- `full_text` and salary are excluded from MVP final scoring.
- Results are returned directly with `rank`, scores, and reasoning; run-only prototype does not persist match results.

## Additive Normal Job/CV Surface
- Normal Job/CV storage is PostgreSQL-backed and separate from V2 prototype
  tables.
- Normal Jobs live in `jobs`; normal CVs live in `cvs`; both use
  `created_by -> users.id` for ownership.
- Normal Job/CV APIs are under `/api/job/*` and `/api/cv/*`.
- Public normal job search is `GET /api/job/search`; compatibility aliases
  `/api/jobs`, `/api/cvs`, and `/api/candidates` route to normal tables and do
  not read V2 data.
- PDF CV upload is `POST /api/cv/upload`; it stores file metadata in
  `cvs.file` and does not parse PDFs yet.

## Current Constraints
- The original matcher keeps exact-match seniority and lowercase/trim/unique skill behavior from `docs/REQUIREMENTS.md`.
- The hybrid matcher uses rank-based seniority scoring, skill alias normalization, empty-field skipping, deterministic text fallback when local MiniLM embeddings are unavailable, and normalized valid-group weights without changing the original matcher.
- Vector index tuning (`hnsw`/`ivfflat`), benchmark, matching-result persistence,
  auth/role guards on V2 matching endpoints, and comparisons with non-V2
  pipelines are outside current matching scope.

## Update Rule
Update this file when V2 matching architecture or constraints change.
