# MVP Roadmap

This folder is the working map for implementing the real JobConnect MVP.

The goal is to make the backend production-like and complete against the
product/backend docs, while bringing up a simple frontend that follows the
intended screen flows and shows real data correctly first. Visual polish can
come after the core data and workflow behavior is trusted.

## Current State

- Backend runtime exists under `backend/src/jobconnect` and exposes the
  production `/api/*` route surface.
- PostgreSQL and pgvector schema exists at
  `backend/db/migrations/001_production_mvp.sql`.
- Matching helpers exist under `backend/src/jobconnect/modules/matching/`.
- The current API is broad but not complete. Known gaps include upload/parsing
  execution, provider integrations, email delivery, auth expiry, ownership
  hardening, PATCH semantics, lifecycle transitions, and some response/filter
  drift from the target contract.
- Frontend runtime is not active. Files under `docs/frontend/` are archived
  reference only and must not be treated as the source of truth for the next
  frontend implementation.

## How To Use This Roadmap

1. Start with `slices.md` to choose the next implementation slice.
2. Check `path-map.md` for the exact files and workflows affected by that
   slice.
3. Update `progress.md` when a slice starts, blocks, enters review, or finishes.
4. Use the Definition of Done in each slice before marking it `done`.
5. Record verification commands and outcomes in the slice handoff.
6. Update the requirements acceptance matrix when a slice implements or changes
   product behavior.

## Delivery Strategy

The team can work in parallel tracks, but backend API contract stabilization
must happen early. Frontend work should consume a stable OpenAPI surface or
explicit temporary mocks; otherwise UI implementation will churn while backend
contracts are still being corrected.

Recommended order:

1. Backend contract, auth, authorization, and API drift cleanup.
2. Upload, parse, provider adapters, embeddings, matching, and lifecycle flows.
3. Frontend design direction and app shell in parallel once contracts are clear.
4. Frontend core workflows against real backend data.
5. End-to-end hardening and release readiness.

## Roadmap Documents

- `docs/mvp-roadmap/slices.md`: detailed implementation slices and DoD.
- `docs/mvp-roadmap/progress.md`: team-maintained progress tracker.
- `docs/mvp-roadmap/path-map.md`: full path map by workflow.
- `docs/mvp-roadmap/slice-execution-guide.md`: rules and prompt template for
  starting and completing each slice.
- `docs/mvp-roadmap/testing-strategy.md`: minimum unit, integration, and
  smoke-contract expectations for implementation slices.
- `docs/mvp-roadmap/requirements-acceptance-matrix.md`: requirement-to-slice
  traceability and acceptance evidence tracker.
- `docs/mvp-roadmap/frontend-readiness.md`: frontend source-of-truth and design
  readiness gate.
- `docs/mvp-roadmap/provider-strategy.md`: adapter/fallback strategy for object
  storage, parsing, embeddings, reranking, and email.
- `docs/mvp-roadmap/worktree-readiness.md`: branch/checkpoint and dirty
  worktree rules before implementation.

## Source Documents

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/00-overview-and-problem.md`
- `docs/backend/HLD/10-architecture-overview.md`
- `docs/backend/HLD/20-ingestion-and-normalization.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/40-matching-and-search-pipeline.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`
- `docs/backend/HLD/60-security-notifications-audit.md`
- `docs/backend/LLD/30-database-schema.md`
- `docs/backend/LLD/40-api-contract.md`
- `docs/backend/LLD/50-current-api-implementation-matrix.md`
