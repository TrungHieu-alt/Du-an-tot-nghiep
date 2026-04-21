# Playbook (Task-to-Procedure Matrix)

Purpose: task router and required procedures by task type. Intake/output format is canonical in `AGENTS.md`.

## How to Use
1. Select one primary task type below.
2. Run all listed procedure steps for that type.
3. Satisfy Definition of Done gates in `definition-of-done.md`.

## A) Bugfix (No Contract Change)
- Use when fixing incorrect behavior without endpoint contract changes.
- Procedure:
  1. Reproduce issue from code path or request flow.
  2. Apply minimal fix in service/repository/logic layer.
  3. Run smoke-contract checks for impacted endpoints.
  4. Record root cause and verification evidence.

## B) API Contract Change
- Use when changing route path, params, body, response, status semantics, or error contract.
- Procedure:
  1. Define contract delta first.
  2. Implement route/schema/service changes.
  3. Update OpenAPI-facing schemas/docs references.
  4. Run startup + OpenAPI + endpoint smoke checks.
  5. Add compatibility note (breaking/non-breaking and migration guidance).

## C) Data Model / Persistence Change
- Use when changing Beanie models, repository logic, IDs, indexes, or storage semantics.
- Procedure:
  1. Document data invariant before editing.
  2. Implement model/repository changes consistently.
  3. Verify impacted CRUD and matching persistence flows.
  4. Document migration/compat fallback if needed.

## D) Matching or AI Pipeline Change
- Use for parse logic, embedding logic, retrieval, rerank weights, LLM evaluation, or hybrid scoring changes.
- Procedure:
  1. Specify changed stage(s) and expected ranking impact.
  2. Keep scoring formulas explicit and versionable in notes.
  3. Run smoke checks for ingest and matching endpoints.
  4. Provide representative scenario evidence (input -> top results trend).

## E) Frontend Wiring Support
- Use when preparing backend for new frontend integration.
- Procedure:
  1. Confirm route contracts are explicit and stable.
  2. Eliminate ambiguous request/response fields.
  3. Provide endpoint usage examples for critical flows.
  4. Validate CORS and auth assumptions.

## F) Refactor (No Intended Behavior Change)
- Use when restructuring code for maintainability/performance without product behavior changes.
- Procedure:
  1. Declare non-functional intent.
  2. Keep interfaces stable.
  3. Run smoke checks to prove behavior parity.
  4. Record what was intentionally not changed.
