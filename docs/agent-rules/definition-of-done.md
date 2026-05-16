# Definition of Done (Strict Gate)

Purpose: measurable completion criteria only. Canonical workflow, runtime,
documentation-sync, AI-guardrail, and handoff rules live in `AGENTS.md`.

A task is done only if every required item below is satisfied.

## 1) Implementation Completeness
- Requested behavior is fully implemented.
- Impacted flows are identified (API, service, repository, AI pipeline, persistence).
- No known unresolved blocker remains hidden.

## 2) Verification Evidence (Mandatory)
- For runtime/API changes, verify startup, OpenAPI availability, and impacted
  endpoint smoke paths using the runtime execution policy in `AGENTS.md`.
- Minimum for API work: one success case and one validation/error case.
- Minimum for matching work: one seeded/read path and one match run path.
- Capture exact commands and outcomes in handoff notes.
- For response-only tasks, use the canonical exception in `AGENTS.md` and
  provide read-only evidence instead of runtime smoke checks.

## 3) Contract Discipline
- If API behavior changed:
  - Schemas/contracts are updated.
  - Change is classified as breaking or non-breaking.
  - Compatibility/migration notes are included.

## 4) Documentation Sync
- Follow the canonical Documentation Synchronization Gate in `AGENTS.md`.
- For AI guardrail edits, follow the canonical AI Guardrails Doc Change Gate in
  `AGENTS.md`.
- Completion evidence must state which docs changed, or `docs: none` with the
  reason.

## 5) Failure Condition
- If any required item is missing, task status is `not done`.
- Partial completion must be explicitly labeled `partial` with remaining gaps.

## 6) Interim Testing Policy
- For runtime/API work, smoke-contract evidence remains mandatory until a full
  automated suite exists.
- "No tests available" is not accepted as completion evidence.
