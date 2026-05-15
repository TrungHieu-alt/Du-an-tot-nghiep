# Provider Strategy

This document defines how to implement complex providers without blocking the
two-week MVP timeline.

Provider areas:

- object storage,
- text extraction,
- LLM structured parsing,
- embedding generation,
- optional reranking,
- email delivery.

## Provider Implementation Rule

Every provider-backed capability must have:

- a narrow interface owned by the backend module or `integrations/`,
- a local/dev implementation that can run in Docker without external services
  where practical,
- a production/provider implementation behind configuration,
- explicit version or provider metadata when output affects persisted data,
- failure behavior that does not corrupt business state,
- tests for success and failure paths.

Do not call a real provider directly from route handlers.

## Recommended Two-Week Strategy

Start with adapter-first implementation:

1. Define interface.
2. Add local/dev fallback.
3. Wire business flow and tests.
4. Add real provider implementation only when the flow is stable.
5. Record provider env vars and failure modes in handoff.

This lets the MVP validate business flows while still keeping a production-like
boundary for later provider replacement.

## Provider Matrix

| Provider area | First MVP mode | Later production mode | Required fallback | Required evidence |
|---|---|---|---|---|
| Object storage | local filesystem adapter | S3-compatible storage | local file storage | upload/download smoke, file retained on parse failure |
| Text extraction | tested local PDF extraction | same or managed extraction service | failure result with preserved original file | PDF success, bad file failure |
| LLM parser | deterministic parser or fixture parser behind interface | configured LLM provider | deterministic parser for tests/dev | parser fixtures, invalid enum failure |
| Embeddings | deterministic local hash embedding | configured embedding provider | local hash embedding | version stored, missing embedding behavior |
| Reranker | disabled | optional cross-encoder/provider | deterministic formula scoring | matching still works with reranker unavailable |
| Email | local/log sender | SMTP or email API provider | log sender | email failure non-rollback test |

## Failure Rules

- Object storage failure returns a clear upload error and creates no partial
  business entity unless explicitly documented.
- Parse failure preserves the original uploaded file.
- LLM parser failure marks parse job `failed`; unsupported enum values are not
  persisted as canonical labels.
- Embedding failure does not activate/publish silently with missing required
  indexing unless the slice explicitly records fallback behavior.
- Email failure never rolls back the business transaction.
- Provider exceptions must not leak secrets or raw file contents into logs.

## Configuration Rules

Each provider slice must document:

- environment variables,
- default local mode,
- production mode,
- how to run tests without external credentials,
- what happens when credentials are missing,
- what metadata is persisted for versioning or diagnosis.

## Slice Mapping

- Slice 4: object storage adapter.
- Slice 5: text extraction and local parse worker.
- Slice 6: LLM parser adapter.
- Slice 7: embedding provider adapter.
- Slice 8: optional reranker remains disabled unless explicitly added.
- Slice 10: email sender adapter.
