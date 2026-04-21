# Working Contract

Purpose: operational behavior contract. Canonical rule priority, hard stops, intake artifacts, and handoff template live in `AGENTS.md`.

## 1) Execution Principles
- Be explicit: no hidden assumptions.
- Be reproducible: verification is command-backed.
- Be contract-safe: backend API changes are controlled and documented.
- Be incremental: prefer small, verifiable deltas.

## 2) Decision Logging
For non-trivial decisions, record:
- Options considered.
- Chosen option.
- Reason.
- Risk tradeoff.

## 3) API and OpenAPI Contract
- OpenAPI is source of truth for frontend-backend wiring.
- No endpoint contract drift without explicit update notes.
- For breaking changes, include:
  - What breaks.
  - Who is affected.
  - Migration path.

## 4) Code and Data Safety
- Do not weaken auth/security behavior silently.
- Do not perform destructive data operations without explicit approval.
- Keep Chroma/Mongo consistency visible in matching-related changes.

## 5) Verification Responsibility
- Definition of Done gates in `definition-of-done.md` are mandatory.
- Every completed task includes command log summary and pass/fail outcomes.
- Missing evidence means incomplete task.

## 6) Escalation Triggers
Escalate immediately when:
- Requirements conflict.
- Repo state contains unexpected same-file changes affecting your task.
- Critical assumptions cannot be validated safely.
