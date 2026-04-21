# Quick Context

Purpose: concise system reality snapshot only. Do not duplicate policy rules from `AGENTS.md`.

## Product Snapshot
- Backend-first job matching system.
- Domain: candidates, recruiters, CVs, job posts, applications, and match results.
- Core outcome: ranked CV <-> JD matching with score and reason.

## Runtime Components
- API server: FastAPI (`backend/main.py`).
- Operational data store: MongoDB via Beanie models.
- Vector store: ChromaDB persistent client in `backend/ragmodel/vector_store`.
- AI layer:
  - Gemini for translation, parsing, and LLM scoring.
  - SentenceTransformers (MiniLM) for embeddings.

## Current Behavior Reality
- AI processing exists in ingestion and matching flows, not only one endpoint.
- Matching pipeline is multi-stage:
  1. ANN retrieval on `emb_full`.
  2. Weighted rerank across semantic fields.
  3. LLM evaluation with score and reason.
  4. Hybrid final score and persistence to `MatchResult`.
- Route-level auth/tenant enforcement is currently limited; treat as known risk in related tasks.

## Current Constraints
- No reliable full automated test suite yet.
- Interim strict gate is smoke-contract verification (startup + OpenAPI + key endpoint checks).

## Update Rule
Update this file only when system behavior reality or constraints change.
