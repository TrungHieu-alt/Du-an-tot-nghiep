# AI Rule Docs Quality Evaluation

This folder contains a repeatable method to evaluate in-repo AI guardrail docs quality.

## Evaluation Boundary
In scope:
- `AGENTS.md`
- `docs/agent-rules/*`

Out of scope:
- runtime system/developer prompts
- source code quality itself
- HLD/LLD design quality (unless explicitly added later)

## Evaluation Goals
The evaluation must answer:
1. Are docs strict enough to reduce hallucination as much as possible?
2. Does an agent have enough context to execute tasks correctly?
3. Does the agent have enough skill/process support, and is DoD strict/reliable?

## Method
1. Run static rubric checks in `rubric.md`.
2. Run scenario drills in `scenario-drills.md`.
3. Produce a gate-based report (`PASS`, `PARTIAL`, `FAIL`) with evidence and remediation.

## Gate Semantics
- `PASS`: all mandatory checks satisfied, no high-risk gap.
- `PARTIAL`: core checks pass but one or more medium/high-risk gaps remain.
- `FAIL`: any hard gate violated or evidence missing.

## Outputs
- One dated report file per run (example: `report-YYYY-MM-DD.md`).
