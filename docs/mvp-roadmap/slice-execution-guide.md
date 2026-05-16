# Slice Execution Guide

Purpose: slice-specific execution checklist. Canonical agent workflow, handoff,
runtime, verification, documentation-sync, and conflict rules live in
`AGENTS.md` and `docs/agent-rules/*`.

Use this guide only after choosing a slice from `docs/mvp-roadmap/slices.md`.

## Source Of Truth Links

- Slice scope and DoD: `docs/mvp-roadmap/slices.md`
- Current status: `docs/mvp-roadmap/progress.md`
- Product acceptance tracking:
  `docs/mvp-roadmap/requirements-acceptance-matrix.md`
- Test policy: `docs/mvp-roadmap/testing-strategy.md`
- Dirty worktree policy: `docs/mvp-roadmap/worktree-readiness.md`
- Targeted doc routing: `docs/agent-rules/doc-map.md`
- Runtime ownership map: `docs/agent-rules/codemap.md`
- Frontend slices only: `docs/mvp-roadmap/frontend-readiness.md`
- Provider-backed slices only: `docs/mvp-roadmap/provider-strategy.md`

## Start Checklist

Before implementation:

1. Confirm the slice and dependencies in `slices.md`.
2. Check and update status in `progress.md`.
3. Record worktree state according to `worktree-readiness.md`.
4. Load targeted docs through `doc-map.md` and `codemap.md`.
5. Identify expected touched files, tests, acceptance evidence, and
   API/OpenAPI impact.
6. Provide the pre-execution summary required by `AGENTS.md`.

If scope, dependency, security, auth, API, or ownership assumptions are unclear,
record the blocker in `progress.md` before editing code.

## Progress Update Shape

Use compact entries in `progress.md`:

```text
Status: <in_progress | blocked | review | done>
Owner: <name>
Current branch/PR: <branch or PR>
Last updated: YYYY-MM-DD
Blocker: <none or specific blocker>
Current next action: <specific next action>
Verification evidence: <none yet or command/evidence summary>
Notes: <API/OpenAPI impact, risks, or follow-ups>
```

## Assignment Prompt

```text
Implement Slice <ID>: <slice name> from docs/mvp-roadmap/slices.md.

Use AGENTS.md and docs/agent-rules/* for canonical workflow.
Use docs/mvp-roadmap/testing-strategy.md for tests.
Use docs/mvp-roadmap/worktree-readiness.md before editing.
Update docs/mvp-roadmap/progress.md and requirements acceptance evidence when required.
Load only targeted product/backend docs through docs/agent-rules/doc-map.md.
Stay inside the slice scope and report API/OpenAPI impact.
```

## Completion Checklist

A slice is complete only when:

- Slice DoD in `slices.md` is satisfied.
- Required verification from `testing-strategy.md` is executed or explicitly
  replaced with valid docs-only evidence.
- `progress.md` records actual evidence and remaining risks.
- `requirements-acceptance-matrix.md` is updated when product behavior changes.
- API/OpenAPI impact is recorded.
- Final handoff uses the mandatory structure in `AGENTS.md`.
