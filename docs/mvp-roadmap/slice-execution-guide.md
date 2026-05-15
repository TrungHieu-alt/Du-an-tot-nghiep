# Slice Execution Guide

Use this guide whenever a team member or coding agent starts a new MVP roadmap
slice.

The purpose is to keep slice work small, verifiable, and aligned with
`docs/REQUIREMENTS.md`, the backend HLD/LLD docs, and the current roadmap.

## Required Reading Before Starting A Slice

Read these files before implementation:

1. `AGENTS.md`
2. `docs/agent-rules/quick-context.md`
3. `docs/agent-rules/codemap.md`
4. `docs/agent-rules/doc-map.md`
5. `docs/agent-rules/playbook.md`
6. `docs/agent-rules/definition-of-done.md`
7. `docs/agent-rules/working-contract.md`
8. `docs/mvp-roadmap/README.md`
9. `docs/mvp-roadmap/slices.md`
10. `docs/mvp-roadmap/progress.md`
11. `docs/mvp-roadmap/path-map.md`
12. `docs/mvp-roadmap/testing-strategy.md`
13. `docs/mvp-roadmap/requirements-acceptance-matrix.md`
14. `docs/mvp-roadmap/worktree-readiness.md`

For frontend slices, also read:

- `docs/mvp-roadmap/frontend-readiness.md`

For provider-backed slices, also read:

- `docs/mvp-roadmap/provider-strategy.md`

Also read targeted product/backend docs listed by the slice and by
`docs/agent-rules/doc-map.md`.

## Definition Of Ready

A slice is ready to implement only when these fields are clear:

- Slice ID and title.
- Owner.
- Current branch or PR target.
- Dependencies and whether they are done, accepted as partial, or explicitly
  bypassed.
- Expected touched paths.
- Expected API/OpenAPI impact: `none`, `non-breaking`, or `breaking`.
- Required tests and smoke checks.
- Required unit test and integration test expectations from
  `docs/mvp-roadmap/testing-strategy.md`.
- Required acceptance evidence from
  `docs/mvp-roadmap/requirements-acceptance-matrix.md`.
- Worktree/branch checkpoint status from
  `docs/mvp-roadmap/worktree-readiness.md`.
- Known blockers or open decisions.

If any item is unclear, update `docs/mvp-roadmap/progress.md` before coding or
record the blocker there.

## Start-Of-Slice Rules

Before editing code or docs for a slice:

1. Confirm the slice status in `docs/mvp-roadmap/progress.md`.
2. Change the slice status to `in_progress`.
3. Fill owner, branch/PR, started date, last updated date, and current next
   action.
4. Run `git status --short` and record whether unrelated dirty files exist.
5. Write a pre-execution summary with:
   - Task Summary
   - Scope / touch files
   - Plan
   - Expected API/OpenAPI impact
6. Keep work inside the slice scope unless a blocker proves the scope is wrong.

## Scope Control Rules

- Do not fix unrelated drift while implementing a slice.
- Do not clean up unrelated dirty worktree changes.
- Do not silently change security, auth, tenant, role, or visibility behavior.
- Do not change API behavior without OpenAPI impact notes.
- Do not mark a slice done without verification evidence.
- Do not mark a code slice done without at least the minimum tests required by
  `docs/mvp-roadmap/testing-strategy.md`.
- Do not mark a user-visible behavior slice done without updating
  `docs/mvp-roadmap/requirements-acceptance-matrix.md`.
- Do not begin frontend implementation before the frontend readiness gate is
  satisfied or explicitly recorded as accepted partial.
- Do not call provider services directly from route handlers; use provider
  interfaces and fallback behavior from `docs/mvp-roadmap/provider-strategy.md`.
- If a new bug or missing dependency appears, either:
  - fix it only if it is required for the current slice DoD, or
  - record it as a blocker or follow-up in `docs/mvp-roadmap/progress.md`.

## Implementation Prompt Template

Use this prompt when assigning a slice to an agent:

```text
Implement Slice <ID>: <slice name> from docs/mvp-roadmap/slices.md.

Rules:
- Read AGENTS.md and the required agent-rule docs first.
- Read docs/mvp-roadmap/README.md, slices.md, progress.md, path-map.md, and slice-execution-guide.md.
- Read docs/mvp-roadmap/testing-strategy.md and add/update the required tests for this slice.
- Read docs/mvp-roadmap/requirements-acceptance-matrix.md and update acceptance evidence for changed requirements.
- Run git status --short before editing and follow docs/mvp-roadmap/worktree-readiness.md.
- For frontend work, read docs/mvp-roadmap/frontend-readiness.md before implementation.
- For provider-backed work, read docs/mvp-roadmap/provider-strategy.md before implementation.
- Read targeted product/backend docs required by the slice.
- Only implement this slice scope.
- Before editing, summarize:
  1. Task Summary
  2. Scope / touch files
  3. Plan
  4. Expected API/OpenAPI impact
- Update docs/mvp-roadmap/progress.md when starting and after completion.
- Do not modify unrelated code or cleanup unrelated dirty worktree changes.
- Use Docker Compose for runtime verification unless explicitly documented otherwise.
- Run the verification required by the slice DoD.
- For code slices, add/update minimum unit tests and add integration tests when a large flow is completed.
- Final handoff must include:
  1. What changed
  2. Why it changed
  3. Verification steps executed and outcomes
  4. API/OpenAPI impact
  5. Risks, gaps, and follow-up actions
```

## Progress Update Template

When a slice starts:

```text
Status: in_progress
Owner: <name>
Current branch/PR: <branch or PR>
Started date: YYYY-MM-DD
Last updated: YYYY-MM-DD
Blocker: none
Current next action: <specific next action>
Verification evidence: none yet
Notes: <scope or assumptions>
```

When a slice is blocked:

```text
Status: blocked
Blocker: <specific blocker>
Current next action: <who needs to decide or what needs to happen>
Notes: <impact on scope, API, or schedule>
```

When a slice is done:

```text
Status: done
Last updated: YYYY-MM-DD
Blocker: none
Current next action: <next recommended slice or follow-up>
Verification evidence:
- <command>: <outcome>
- <smoke check>: <outcome>
Notes:
- API/OpenAPI impact: <none | non-breaking | breaking>
- Risks/follow-ups: <specific remaining items>
```

## Verification Expectations

For backend slices, use the slice DoD plus the standard smoke-contract gate:

```bash
docker compose up -d postgres backend
docker compose exec backend python db/apply_migrations.py
docker compose exec backend python -m unittest discover -s tests
curl http://localhost:8000/api/health
curl http://localhost:8000/openapi.json
```

For frontend slices, record the actual commands introduced by the frontend
runtime. Until the frontend runtime exists, frontend implementation slices must
state the chosen stack, startup command, and smoke checklist.

For docs-only slices, runtime checks can be replaced with read-only evidence:

- files inspected,
- files changed,
- links/path references checked,
- confirmation that API/OpenAPI impact is `none`.

## Completion Gate

A slice is complete only when:

- Its DoD in `docs/mvp-roadmap/slices.md` is satisfied.
- Required verification evidence is recorded.
- `docs/mvp-roadmap/progress.md` is updated.
- API/OpenAPI impact is recorded.
- Risks and follow-up actions are visible.
- The final handoff uses the mandatory five-section structure from `AGENTS.md`.
