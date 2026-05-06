# Quick Context

Purpose: concise system reality snapshot for V2 target documentation.

## Product Snapshot
- Backend-first job matching system, V2 prototype direction.
- Core outcome: ranked CV <-> JD matching with explicit score breakdown.

## Runtime Components (V2 Target)
- API server: FastAPI (`backend/main.py`).
- Primary data store: PostgreSQL.
- Vector retrieval: `pgvector` in PostgreSQL.
- Matching engine (MVP): hard filters + embedding scoring + business rerank.

## Current Behavior Target (V2)
- Prototype route namespace: `/api/v2/prototype/matching/*`.
- Matching MVP does not require LLM stage.
- `full_text` and salary are excluded from MVP final scoring.
- Score breakdown fields are persisted for audit and comparison.

## Current Constraints
- Mapping quality for seniority/education/skills alias depends on normalization policy.
- Vector index tuning (`hnsw`/`ivfflat`) is benchmark-dependent.

## Update Rule
Update this file when V2 matching architecture or constraints change.
