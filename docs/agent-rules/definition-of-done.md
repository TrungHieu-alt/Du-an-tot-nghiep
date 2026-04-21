# Definition of Done (Strict Gate)

Purpose: measurable completion criteria only. Handoff section format is canonical in `AGENTS.md`.

A task is done only if every required item below is satisfied.

## 1) Implementation Completeness
- Requested behavior is fully implemented.
- Impacted flows are identified (API, service, repository, AI pipeline, persistence).
- No known unresolved blocker remains hidden.

## 2) Verification Evidence (Mandatory)
- Run backend startup verification.
  - Example: `uvicorn main:app --reload` from `backend/`.
- Validate OpenAPI contract availability.
  - Example: verify `/docs` and `/openapi.json` respond successfully.
- Run key endpoint smoke calls for impacted flows.
  - Minimum for API work: one success case + one validation/error case.
  - Minimum for matching work: one ingest path + one match retrieval path.
- Capture exact commands and outcomes in handoff notes.

Response-only exception (see canonical rule in `AGENTS.md`):
- If task type is `Response-Only Task (No Repository Changes)`, replace runtime smoke checks with read-only verification evidence:
  - source files/docs inspected,
  - key statements cross-checked,
  - confirmation that touched files are `none`.

## 3) Contract Discipline
- If API behavior changed:
  - Schemas/contracts are updated.
  - Change is classified as breaking or non-breaking.
  - Compatibility/migration notes are included.

## 4) Documentation Sync
- Update relevant docs when behavior, assumptions, or flow changes:
  - `docs/agent-rules/quick-context.md` for system reality changes.
  - `docs/agent-rules/codemap.md` for flow ownership/path changes.
  - `docs/agent-rules/playbook.md` if execution procedure standards changed.
- If task edits AI guardrails docs (`AGENTS.md` or `docs/agent-rules/*`):
  - Run a duplicate-rule check across all AI guardrails docs.
  - Keep canonical rules in `AGENTS.md`; other files should reference rather than duplicate.
  - Include duplicate-check result in handoff evidence.

## 5) Failure Condition
- If any required item is missing, task status is `not done`.
- Partial completion must be explicitly labeled `partial` with remaining gaps.

## 6) Interim Testing Policy
- Until a full automated suite exists, smoke-contract gate is mandatory.
- "No tests available" is not accepted as completion evidence.
