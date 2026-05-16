# Requirements Acceptance Matrix

This matrix connects product requirements to implementation slices and required
acceptance evidence.

Use it to prevent a slice from being marked complete while the product
requirement is still untested or only partially implemented.

## Status Values

- `not_started`: no implementation or evidence exists yet.
- `partial`: some implementation exists, but evidence or behavior is incomplete.
- `implemented`: code exists and local slice verification passed.
- `accepted`: implementation is verified by the required acceptance evidence.
- `deferred`: intentionally moved out of the current MVP scope with rationale.

## Acceptance Rules

- Every user-visible requirement must map to at least one slice.
- Every code slice must update this matrix when it implements or changes a
  requirement.
- A requirement can be `implemented` without being `accepted`, but not `done` for
  MVP release.
- `accepted` requires evidence: unit tests, integration tests, smoke-contract
  output, or documented frontend smoke results.
- If requirements and runtime behavior conflict, `docs/REQUIREMENTS.md` wins and
  the conflict must be recorded in the slice handoff.

## Product Requirement Coverage

| Requirement area | Source | Primary slices | Required acceptance evidence | Status | Notes |
|---|---|---|---|---|---|
| Email/password auth and JWT sessions | `docs/REQUIREMENTS.md` sections 2, 4, 9 | 1, 12, 16 | Unit tests for token expiry/invalid token; login/register smoke; `/api/me` smoke | partial | Runtime exists but expiry/bootstrap drift remains. |
| Roles: candidate, recruiter, admin | `docs/REQUIREMENTS.md` sections 1, 3, 6 | 1, 2, 11, 12 | Role authorization unit tests; endpoint forbidden smoke; admin/non-admin integration checks | partial | Needs tightened ownership and admin read-only checks. |
| Candidate profile and resume lifecycle | `docs/REQUIREMENTS.md` sections 4.1, 6.1, 6.2 | 2, 3, 5, 12, 15, 16 | Candidate flow integration test; activate/archive smoke; visibility tests | partial | Manual resume CRUD exists; parse-to-resume flow incomplete. |
| Recruiter profile, organization, and job lifecycle | `docs/REQUIREMENTS.md` sections 4.2, 6.1, 6.3 | 2, 3, 5, 12, 15, 16 | Recruiter flow integration test; publish/close smoke; organization ownership tests | partial | Runtime exists but ownership/PATCH/filter drift remains. |
| Upload original CV/JD files | `docs/REQUIREMENTS.md` sections 5, 6.4, 9 | 4, 5, 12, 15, 16 | Multipart upload success; MIME/size failures; document metadata read; download-url smoke | not_started | Current runtime is metadata-only. |
| Text extraction and preprocessing | `docs/REQUIREMENTS.md` section 5.2 | 5, 6, 12, 16 | Unit tests for Unicode/control/whitespace cleanup; parse fixture smoke | not_started | Needs worker implementation. |
| Skill normalization | `docs/REQUIREMENTS.md` section 5.3 | 5, 6, 7, 8 | Unit tests for alias mapping/dedup; matching/search fixture evidence | not_started | Needs 50-100 high-impact aliases. |
| LLM structured extraction | `docs/REQUIREMENTS.md` section 5.4 | 6, 12, 16 | Parser fixture tests in Vietnamese, English, mixed text; invalid enum failure test | not_started | Must use adapter and fallback strategy. |
| Embedding generation and versioning | `docs/REQUIREMENTS.md` section 6.5 | 5, 7, 8, 12 | Embedding version tests; missing embedding tests; semantic search smoke | partial | Slice 7 provider boundary is active; local hash remains default fallback. Parse-job metadata now records active embedding provider version. Backfill/re-embedding operations remain future work. |
| Keyword search separation | `docs/REQUIREMENTS.md` section 8.1 | 3, 12, 15 | Job/resume search endpoint smoke; frontend exact search mode smoke | partial | Search exists but target fields/filter coverage incomplete. |
| Semantic search separation | `docs/REQUIREMENTS.md` section 8.2 | 7, 12, 15 | Semantic endpoint smoke; relevance score shape check; frontend semantic mode smoke | partial | Backend semantic endpoints now use intended description fields: resume summary/experience and job requirement. Frontend semantic mode remains future work. |
| Two-way matching | `docs/REQUIREMENTS.md` section 7 | 7, 8, 12, 15, 16 | Unit tests for hard filters/scoring; job->resume and resume->job integration tests | partial | Matching exists but ownership/provider gaps remain. |
| Explainable ranking | `docs/REQUIREMENTS.md` sections 7.3, 7.5, 9 | 8, 12, 15 | Response schema check; reasoning notes tests; UI result card smoke | partial | Current response has fields; content needs hardening. |
| Candidate apply flow | `docs/REQUIREMENTS.md` section 4.3, 6.6 | 9, 10, 12, 15, 16 | Candidate apply integration test; duplicate application test; notification/audit check | partial | Runtime exists, transition graph needs hardening. |
| Recruiter invite flow | `docs/REQUIREMENTS.md` section 4.3, 6.7 | 9, 10, 12, 15, 16 | Invite create/accept/reject integration tests; duplicate accept behavior test | partial | Runtime exists; duplicate pending guard/status checks needed. |
| Application lifecycle | `docs/REQUIREMENTS.md` sections 4.3, 6.6 | 9, 10, 12, 15, 16 | Status transition unit tests; event history verification; terminal lock smoke | partial | Runtime status checks are incomplete. |
| Notifications and email | `docs/REQUIREMENTS.md` sections 4.4, 6.8 | 10, 12, 15, 16 | Notification row checks; email failure non-rollback test; frontend notification smoke | partial | In-app rows exist; email provider not implemented. |
| Audit logs | `docs/REQUIREMENTS.md` sections 6.9, 60 HLD | 10, 11, 12, 16 | Audit row checks for required events; admin audit filter smoke | partial | Some audit exists; consistency incomplete. |
| Admin read-only monitoring | `docs/REQUIREMENTS.md` sections 1, 2, 6.9 | 11, 12, 15, 16 | Admin monitoring integration test; non-admin forbidden smoke | partial | Runtime exists but filters/details incomplete. |
| OpenAPI production namespaces | `docs/REQUIREMENTS.md` section 9 | 0, 1, 3, 4, 8, 9, 12, 16 | `/openapi.json`; schema checks for changed endpoints; no prototype route check | partial | Current surface exists; contract drift remains. |
| Frontend core workflows | `docs/frontend/*` reference plus product/backend docs | 13, 14, 15, 16 | Screen-to-API map; browser smoke for candidate, recruiter, admin | not_started | Frontend runtime is not active. |

## Release Acceptance Rule

Before MVP release or demo readiness is claimed:

- No in-scope requirement above may remain `not_started`.
- Any `partial` requirement must have a named follow-up or an explicit MVP
  deferral decision.
- Core flows must be `accepted`: auth, candidate CV/apply, recruiter
  JD/invite/application, matching, parse success/failure, notifications/audit,
  and admin monitoring.
