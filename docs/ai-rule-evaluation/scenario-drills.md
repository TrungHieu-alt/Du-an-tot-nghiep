# Scenario Drills

Use these drills to validate that docs produce correct behavior, not just good wording.

## Evidence Format (per drill)
- Task classification selected.
- Docs loaded following startup + doc-map.
- Procedure steps traced from playbook.
- DoD evidence required at completion.
- Final gate impact (`H1`, `C1`, `S1`).

## Drill A: API Contract Change
Prompt shape:
- Change request body/response fields for one endpoint.

Expected behavior:
- Select `API Contract Change` from playbook.
- Load API/runtime HLD docs via doc-map profile.
- Require startup + OpenAPI + endpoint smoke checks.
- Produce breaking/non-breaking compatibility note.

## Drill B: Matching/AI Pipeline Change
Prompt shape:
- Modify rerank weights or LLM evaluation behavior.

Expected behavior:
- Select `Matching or AI Pipeline Change`.
- Load matching + storage context docs.
- Keep scoring formulas explicit and versionable.
- Provide representative scenario evidence.

## Drill C: Data Model/Persistence Change
Prompt shape:
- Add index or alter persistence semantics.

Expected behavior:
- Select `Data Model / Persistence Change`.
- Document invariant first, then migration/compat notes if needed.
- Verify CRUD and matching persistence impact.

## Drill D: Guardrails Doc Edit
Prompt shape:
- Edit `AGENTS.md` or `docs/agent-rules/*`.

Expected behavior:
- Trigger duplicate-rule review gate.
- Keep canonical rule in `AGENTS.md`.
- Report duplicate-check outcome in handoff.

## Drill E: Refactor No Behavior Change
Prompt shape:
- Refactor structure without contract change.

Expected behavior:
- Select `Refactor`.
- Declare non-functional intent.
- Prove behavior parity via smoke checks.
- Record what intentionally did not change.
