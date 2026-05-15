# Backend HLD V2: Overview and Problem

> Legacy prototype HLD. This file documents the current V2 run-only prototype
> and is not the active production architecture. Use
> `docs/backend/HLD/00-overview-and-problem.md` for target MVP work.

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
- Matching pipeline: `docs/backend/HLD/legacy/legacy-matching-pipeline.md`
- Storage boundaries: `docs/backend/HLD/legacy/legacy-data-and-storage.md`
- API/runtime flow: `docs/backend/HLD/legacy/legacy-api-and-runtime-flows.md`
