# Backend HLD V2: Overview and Problem

## Problem

The prototype needs a small, deterministic runtime for evaluating JD <-> CV
matching over data that already exists in PostgreSQL.

## Goals

- Accept one existing `job_id` or `cv_id`.
- Return ranked matches with score breakdown and deterministic reasoning.
- Keep the runtime synchronous and easy to smoke test.
- Keep storage scope limited to the four V2 PostgreSQL tables.

## Non-Goals

- Document ingestion or parsing.
- Account, application, or business lifecycle APIs.
- Runtime LLM evaluation.
- Persisted match results.
- Benchmark conclusions from labeled quality metrics.

## High-Level Flow

```text
Frontend V2 pages
  |
  v
FastAPI /api/v2/prototype/*
  |
  v
PostgreSQL + pgvector
  |
  v
Hard filters + deterministic scoring + rerank
  |
  v
Response with ranks, score fields, reasoning, and runtime metrics
```

## Related Docs

- Product spec: `docs/REQUIREMENTS.md`
- Architecture: `docs/backend/HLD/10-architecture-overview.md`
- Matching pipeline: `docs/backend/HLD/20-matching-pipeline.md`
- Storage boundaries: `docs/backend/HLD/30-data-and-storage.md`
- API/runtime flow: `docs/backend/HLD/40-api-and-runtime-flows.md`
