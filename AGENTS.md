# Agent Entry Rules

This file is the mandatory entrypoint for all coding agents and contributors in this repository.

## Rule Priority (Canonical)
1. System and developer instructions from the active runtime.
2. This `AGENTS.md`.
3. Documents under `docs/agent-rules/`.
4. Existing inline code comments and historical docs.

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
- Exact documentation files expected to be synced, or `none` with reason
- Explicit out-of-scope areas
- Affected runtime workflows from `codemap.md`

### 3) Plan
- Ordered implementation steps
- Ordered verification steps
- Expected API/OpenAPI impact: `none`, `non-breaking`, or `breaking`

## REQUIREMENTS.md — Product Spec Gate (Canonical)
`docs/REQUIREMENTS.md` is the high-level source of truth for what the system builds, why, domain model, scoring formulas, and acceptance criteria.

**Always read `docs/REQUIREMENTS.md` when:**
- Starting a new feature
- Changing behavior visible to users
- Modifying domain/business logic (matching pipeline, data models, scoring)
- Resolving ambiguity between code and spec
- Writing tests for product behavior
- Reviewing PRs for correctness against spec

**Do NOT need to read it for:**
- Pure formatting changes
- Renaming variables without behavior change
- Small local bug fixes already described clearly in the task
- Dependency/config updates unrelated to behavior

If code contradicts `docs/REQUIREMENTS.md`, treat the spec as authoritative and escalate before proceeding.

## Context Budget and Read Order
- First pass (always): this file + all docs under `docs/agent-rules/` in startup order.
- Second pass (targeted): load `docs/REQUIREMENTS.md` per the gate above, then only files in impacted workflows from `codemap.md`.
- Avoid broad repo scanning when the task scope is already clear.

## Notion MCP Trigger Rule (Canonical)
- If the user prompt contains the word `notion` (case-insensitive), the agent must use Notion MCP tools for retrieval/update workflows when relevant to the request.
- Prefer Notion MCP as the primary execution path over ad-hoc alternatives for Notion workspace operations.
- If the prompt includes `notion` but the requested action is clearly outside Notion scope, state that constraint explicitly in the handoff.

## Playwright MCP Trigger Rule (Canonical)
- Only use Playwright MCP tools when the user prompt contains the word `playwright` (case-insensitive).
- If the prompt does not contain `playwright`, do not use Playwright MCP tools.

## Context7 Usage Rule (Canonical)
- Default to reading and reasoning from local source code first.
- Use Context7 only when at least one condition is true:
  1. The task depends on external library/framework APIs, configuration, or best practices.
  2. Relevant behavior is not clear from source code.
  3. There is risk that built-in knowledge may be outdated.
  4. Version-specific usage must be verified.
- Do not use Context7 for:
  1. Pure business logic already implemented in the repo.
  2. Simple refactors, renames, formatting, or type fixes.
  3. Explaining code that is fully understandable from source.
  4. Searching files, symbols, or project-local behavior.
- When using Context7:
  - Query narrowly for the specific library/topic.
  - Avoid broad documentation dumps.
  - Stop after one query unless result is insufficient.
  - Briefly state that Context7 was used and why.

## MCP and Action Tool Approval Gate (Canonical)
- Before using any MCP tool, the agent must ask for user confirmation and state exactly which tool will be used and why.
- Do not call MCP tools until user confirmation is explicitly received in the current conversation.
- User approval scope must be explicit (single tool call or a clearly listed tool set). No implicit blanket approval.
- If approval is not granted, stop at read/reasoning only and ask again; do not execute MCP calls.
- Never use write/action tools without explicit approval. This includes, at minimum, Notion create/update/move tools and Playwright interaction tools such as click/type/fill/select/drag/drop.
- This approval gate also applies to Context7 tools (`resolve_library_id`, `query_docs`).
- If another rule requires a specific MCP path (for example, the Notion MCP trigger rule), that requirement is still gated by this approval rule.

## Conflict and Escalation Protocol
- If two sources disagree, apply Rule Priority and document the conflict in handoff.
- If requirement ambiguity can change API/security/data behavior, stop and escalate.
- If encountering unexpected same-file edits from others, stop and escalate before proceeding.

## Hard Stops (Non-Negotiable)
- Do not ship behavior changes without verification evidence.
- When a bug/regression or uncovered case is identified, add or update an automated test that reproduces and guards that case before closing the task.
- Do not change API behavior without OpenAPI contract sync notes.
- Do not skip docs updates when behavior, flow, assumptions, slice status, verification evidence, or Go/No-Go readiness changes.
- Do not make silent assumptions on security, auth, or tenant boundaries.
- Do not merge AI guardrails doc edits without a duplicate-rule check across `AGENTS.md` and `docs/agent-rules/*`.

## Documentation Synchronization Gate (Canonical)
Before final handoff or staging, run a documentation impact check for every
task that changes behavior, API/OpenAPI semantics, data flow, provider behavior,
verification status, roadmap/slice readiness, operational assumptions, or
Go/No-Go decisions.

Required behavior:
1. Identify docs from `docs/agent-rules/doc-map.md` plus roadmap/status docs
   when progress or readiness changes.
2. Update every affected source-of-truth doc in the same task, or explicitly
   record `docs: none` with the reason in the handoff.
3. For slice/risk-sweep work, always check these roadmap files:
   - `docs/mvp-roadmap/progress.md`
   - `docs/mvp-roadmap/slices.md`
   - `docs/mvp-roadmap/requirements-acceptance-matrix.md`
4. For API/behavior changes, also check current implementation/API docs:
   - `docs/backend/LLD/50-current-api-implementation-matrix.md`
   - `docs/backend/HLD/*` files loaded for the task
   - `docs/backend/LLD/40-api-contract.md` when request/response/status
     semantics change
5. Stage or report code and doc changes together. Never stage code-only work
   after a behavior/risk-sweep change unless the documentation impact check
   found no required doc updates and the handoff says why.

## Runtime Execution Rule (Canonical)
- For any task that requires runtime execution (for example: running tests, starting app services, smoke checks, or commands that depend on live backend/frontend processes), use Docker Compose runtime instead of host-local runtimes.
- Default execution path is `docker compose` with repository-defined services.
- Host-local runtime commands are allowed only when Docker-based execution is unavailable or explicitly requested by the user, and this exception must be documented in the handoff note.
- LaTeX report workflows are an explicit local-runtime exception: for tasks under `report/` (for example `latexmk`, `xelatex`, `pdflatex`, `biber`, `bibtex`, `makeindex`), run on host-local environment and do not use Docker/container execution unless the user explicitly requests containerized LaTeX.

## LaTeX Knowledge Pack Rule (Canonical)
Applies to report-authoring tasks that use files under `report/`.

Required behavior:
1. Treat `report/knowledge/01-structure-blueprint.md` as the structure source-of-truth.
2. Treat `report/knowledge/02-writing-style-guide.md` as the writing/citation source-of-truth.
3. Use `report/knowledge/03-legacy-content-map.md` only as idea/mapping input; do not copy long verbatim passages from legacy report content.
4. Do not reopen large DOCX sources by default once Knowledge Pack exists. Reopen DOCX only when:
   - a required section/rule is missing in Knowledge Pack, or
   - visual/layout fidelity must be verified, or
   - exact quotation verification is explicitly required.
5. If source DOCX files in `report/` change, regenerate Knowledge Pack before further writing using:
   - `python3 report/tools/extract_docx_knowledge.py --layout report/Bo-cuc-khoa-luan.docx --legacy "report/Dự án khoa học.docx" --out report/knowledge`
6. For report writing handoffs, include a short note confirming which Knowledge Pack files were used and whether DOCX reopen was required.

## AI Guardrails Doc Change Gate
Applies when editing `AGENTS.md` or any file under `docs/agent-rules/`.

Required verification before completion:
1. Run a duplicate-rule review against all AI guardrails docs.
2. Resolve duplicates by keeping the canonical rule in `AGENTS.md` and leaving references elsewhere.
3. Record duplicate check outcome in the handoff note, including what was removed or confirmed unique.

## Current Repository Baseline
- Backend is the active implemented system (`backend/`).
- Frontend runtime code is not active yet; future screens will be redesigned
  later from product/backend/OpenAPI sources.
- API contract discipline is mandatory now.
- Automated tests are currently limited; strict smoke-contract verification is required until full tests exist.

## Mandatory Output Template For Completed Tasks
Use this exact section structure in every completion handoff.

1. What changed
2. Why it changed
3. Verification steps executed and outcomes
4. API/OpenAPI impact
5. Risks, gaps, and follow-up actions

## Backend Surface (current state)

* **Backend source**: `backend/src/jobconnect/` with app, core, common,
  integrations, and feature module boundaries. `backend/main.py` is a
  compatibility wrapper.
* **Runtime API**: `/api/*` namespaces plus `/api/health` and `/`.
  Legacy `/api/v2/prototype/*` code is removed from runtime.
* **Database**: Postgres + pgvector at host port 5433. Schema lives
  in `backend/db/migrations/001_production_mvp.sql`.
* **Matching helpers**: deterministic hard filters, scoring, reasoning, and
  local hash embedding helpers live under
  `backend/src/jobconnect/modules/matching/`.
* **Frontend**: frontend runtime code is not present yet. `docs/frontend/`
  contains experimental prototype-adjacent notes only; do not treat them as the
  source of truth for the next frontend design.
* **Data is NOT auto-loaded** by `docker compose up`. Apply migrations with
  `docker compose exec backend python db/apply_migrations.py`.
  Volume `postgres_data` persists rows across `docker compose down/up`; only
  `down -v` wipes.
