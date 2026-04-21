# Rubric: AI Rule Docs Quality Gates

## Gate H1: Hallucination Control Strictness
Objective: ensure docs force source-grounded, low-assumption execution.

Mandatory checks:
- H1.1 Canonical priority exists and conflict resolution is explicit.
- H1.2 Startup routine enforces mandatory context loading.
- H1.3 Rules include escalation triggers for ambiguity/conflict/high-risk assumptions.
- H1.4 Hard stops block silent security/auth/API behavior assumptions.
- H1.5 Completion requires verifiable evidence, not claim-only completion.

Strongly recommended checks:
- H1.R1 Explicit citation requirement for major technical claims in handoff.
- H1.R2 Explicit anti-hallucination fallback when repository evidence is missing.

Pass criteria:
- All mandatory checks pass.
- No missing hard-stop or escalation clause for high-risk ambiguity.

## Gate C1: Task Context Sufficiency
Objective: ensure an agent can reliably find enough context for most tasks.

Mandatory checks:
- C1.1 Startup read order is deterministic and complete.
- C1.2 Codemap covers main workflow ownership paths.
- C1.3 Doc-map routes tasks to targeted docs with fallback behavior.
- C1.4 Playbook provides task-type procedure mapping.
- C1.5 Context-budget rule discourages unnecessary broad scanning.

Strongly recommended checks:
- C1.R1 Coverage map for all playbook task types to concrete docs.
- C1.R2 Explicit handling for unknown/new workflow areas.

Pass criteria:
- All mandatory checks pass.
- No uncovered critical workflow that would block task execution.

## Gate S1: Skill/Process and DoD Reliability
Objective: ensure process support is sufficient and DoD is strict/reproducible.

Mandatory checks:
- S1.1 Playbook procedures include verification expectations per task type.
- S1.2 DoD has explicit mandatory evidence gates.
- S1.3 DoD defines failure condition when evidence is missing.
- S1.4 Working contract enforces reproducibility and decision logging.
- S1.5 API/contract-discipline expectations are explicit.

Strongly recommended checks:
- S1.R1 Skill-capability matrix: which tasks require which competencies/tools.
- S1.R2 Reliability checks for repeated execution consistency.

Pass criteria:
- All mandatory checks pass.
- DoD evidence path is executable and auditable for each major task class.

## Scoring Rule
For each gate:
- `PASS`: mandatory checks all pass, no material reliability gap.
- `PARTIAL`: mandatory checks pass, but recommended gaps create practical risk.
- `FAIL`: any mandatory check fails.
