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
- Prototype route namespace: `/api/v2/prototype/matching/*`.
- Prototype API surface is run-only: `POST /job/{job_id}/run` and `POST /cv/{cv_id}/run`.
- Matching MVP does not require LLM stage.
- `full_text` and salary are excluded from MVP final scoring.
- Results are returned directly with `rank`, scores, and reasoning; run-only prototype does not persist match results.

## Current Constraints
- Seniority uses exact-match prototype taxonomy from `docs/REQUIREMENTS.md`.
- Skills normalization is lowercase + trim + unique; no synonym dictionary in run-only prototype.
- Vector index tuning (`hnsw`/`ivfflat`), benchmark, persistence, auth changes, and old-vs-v2 comparison are outside current scope.

## Update Rule
Update this file when V2 matching architecture or constraints change.
