# Agent Entry Rules

This file is the mandatory entrypoint for all coding agents and contributors in this repository.

## Rule Priority (Canonical)
1. System and developer instructions from the active runtime.
2. This `AGENTS.md`.
3. Documents under `docs/agent-rules/`.
4. Existing inline code comments and legacy docs.

If rules conflict, follow the higher-priority source and record the conflict in the handoff note.

## Required Startup Routine
1. Read this file completely.
2. Read, in order:
   - `docs/agent-rules/quick-context.md`
   - `docs/agent-rules/codemap.md`
   - `docs/agent-rules/doc-map.md`
   - `docs/agent-rules/playbook.md`
   - `docs/agent-rules/definition-of-done.md`
   - `docs/agent-rules/working-contract.md`
3. Classify the task using the playbook matrix.
4. Follow `docs/agent-rules/doc-map.md` loading walkthrough to load only required docs for the classified task.
5. Produce the AI working artifacts below before implementation.
6. Execute only the procedure and checks required by that playbook row.
7. Produce handoff evidence that satisfies Definition of Done.

## AI Working Flow (Mandatory)

For any request that qualifies as a task, the AI may first:
- read required files
- read mandatory context documents
- inspect relevant code or docs
- perform internal reasoning and solution design

Before taking any external action beyond reading and reasoning, the AI MUST provide a pre-execution response with these sections:

1) Task Summary
2) Scope
3) Plan

External actions include:
- editing files
- writing code
- generating patches
- creating or modifying documents
- running implementation commands
- producing final deliverables or user-facing output artifacts

This pre-execution response is mandatory for implementation, analysis, planning, and debugging tasks, or any user request that can be executed as a task.

This requirement applies only to the pre-execution checkpoint.
It does NOT require the final answer, deliverable, or completion handoff to use the same structure unless explicitly requested by the user.

### Response-Only Task Rule (Canonical)
Use this rule when the user explicitly requests chat output only (for example: "overview as a response, not a new file") and no repository change is required.
- Recognition signal: user intent is informational/summary/reporting output in chat, with explicit or implicit "no file/code changes."
- Required behavior:
  1. Do not edit repository files.
  2. Do not run implementation commands that mutate code/data.
  3. Produce the requested deliverable directly in the response.
  4. Still provide pre-execution `Task Summary`, `Scope`, and `Plan` before final output.
  5. In handoff, mark touched files as `none` and record read-only verification evidence.

### 1) Task Summary
- Intent
- Success criteria
- Constraints and assumptions
- Task type from `playbook.md`

### 2) Scope (Touch Files)
- Exact file list expected to be edited
- Explicit out-of-scope areas
- Affected runtime workflows from `codemap.md`

### 3) Plan
- Ordered implementation steps
- Ordered verification steps
- Expected API/OpenAPI impact: `none`, `non-breaking`, or `breaking`

## Context Budget and Read Order
- First pass (always): this file + all docs under `docs/agent-rules/` in startup order.
- Second pass (targeted): only files in impacted workflows from `codemap.md`.
- Avoid broad repo scanning when the task scope is already clear.

## Conflict and Escalation Protocol
- If two sources disagree, apply Rule Priority and document the conflict in handoff.
- If requirement ambiguity can change API/security/data behavior, stop and escalate.
- If encountering unexpected same-file edits from others, stop and escalate before proceeding.

## Hard Stops (Non-Negotiable)
- Do not ship behavior changes without verification evidence.
- Do not change API behavior without OpenAPI contract sync notes.
- Do not skip docs updates when behavior, flow, or assumptions change.
- Do not make silent assumptions on security, auth, or tenant boundaries.
- Do not merge AI guardrails doc edits without a duplicate-rule check across `AGENTS.md` and `docs/agent-rules/*`.

## AI Guardrails Doc Change Gate
Applies when editing `AGENTS.md` or any file under `docs/agent-rules/`.

Required verification before completion:
1. Run a duplicate-rule review against all AI guardrails docs.
2. Resolve duplicates by keeping the canonical rule in `AGENTS.md` and leaving references elsewhere.
3. Record duplicate check outcome in the handoff note, including what was removed or confirmed unique.

## Current Repository Baseline
- Backend is the active implemented system (`backend/`).
- Frontend integration is expected next; API contract discipline is mandatory now.
- Automated tests are currently limited; strict smoke-contract verification is required until full tests exist.

## Mandatory Output Template For Completed Tasks
Use this exact section structure in every completion handoff.

1. What changed
2. Why it changed
3. Verification steps executed and outcomes
4. API/OpenAPI impact
5. Risks, gaps, and follow-up actions
