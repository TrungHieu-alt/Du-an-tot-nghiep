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
| Email/password auth and JWT sessions | `docs/REQUIREMENTS.md` sections 2, 4, 9 | 1, 12, 16 | Unit tests for token expiry/invalid token; login/register smoke; `/api/me` smoke | accepted | Slice 1 is done: `expires_in`, JWT `exp`, expired/missing-exp rejection, disabled-user guard, and role bootstrap are verified. End-to-end release smoke remains in Slice 12/16. |
| Roles: candidate, recruiter, admin | `docs/REQUIREMENTS.md` sections 1, 3, 6 | 1, 2, 11, 12 | Role authorization unit tests; endpoint forbidden smoke; admin/non-admin integration checks | partial | Needs tightened ownership and admin read-only checks. |
| Candidate profile and resume lifecycle | `docs/REQUIREMENTS.md` sections 4.1, 6.1, 6.2 | 2, 3, 5, 12, 15, 16 | Candidate flow integration test; activate/archive smoke; visibility tests | partial | Resume CRUD, lifecycle guards, upload-to-draft parse path, and ownership visibility have backend coverage; full candidate E2E and frontend workflow evidence remain in Slice 12/15/16. |
| Recruiter profile, organization, and job lifecycle | `docs/REQUIREMENTS.md` sections 4.2, 6.1, 6.3 | 2, 3, 5, 12, 15, 16 | Recruiter flow integration test; publish/close smoke; organization ownership tests | partial | Organization/job ownership, partial PATCH, publish/close guards, and upload-to-draft JD parse path have backend coverage. Independent organization seed/bootstrap and full recruiter E2E remain follow-up. |
| Upload original CV/JD files | `docs/REQUIREMENTS.md` sections 5, 6.4, 9 | 4, 5, 12, 15, 16 | Multipart upload success; MIME/size failures; document metadata read; download-url smoke | accepted | Slice 4 is done: multipart upload, MIME/size errors, storage adapter, document detail parse jobs, retry, and download-url contract are verified. Frontend upload UX remains Slice 15. |
| Text extraction and preprocessing | `docs/REQUIREMENTS.md` section 5.2 | 5, 6, 12, 16 | Unit tests for Unicode/control/whitespace cleanup; parse fixture smoke | accepted | Slice 5/6 parser pipeline is done for local deterministic extraction/preprocessing and parser fallback. DOCX extraction limitation remains documented. |
| Skill normalization | `docs/REQUIREMENTS.md` section 5.3 | 5, 6, 7, 8 | Unit tests for alias mapping/dedup; matching/search fixture evidence | partial | Parser fixtures cover canonical skill/enum mapping, but broader 50-100 high-impact alias coverage and matching/search scenario evidence remain in Slice 8/12. |
| LLM structured extraction | `docs/REQUIREMENTS.md` section 5.4 | 6, 12, 16 | Parser fixture tests in Vietnamese, English, mixed text; invalid enum failure test | accepted | Slice 6 is done: adapter boundary, local fallback, OpenAI provider error handling, EN/VN/mixed fixtures, and invalid enum sanitization are verified. |
| Embedding generation and versioning | `docs/REQUIREMENTS.md` section 6.5 | 5, 7, 8, 12 | Embedding version tests; missing embedding tests; semantic search smoke | accepted | Slice 7 is done: provider-backed embeddings, active embedding version metadata, missing-embedding behavior, and semantic search paths are verified. Backfill/re-embedding operations remain future work. |
| Keyword search separation | `docs/REQUIREMENTS.md` section 8.1 | 3, 12, 15 | Job/resume search endpoint smoke; frontend exact search mode smoke | partial | Backend search/filter cleanup exists, including jobs `q` over organization name, but full target field coverage and frontend exact-search smoke remain in Slice 12/15. |
| Semantic search separation | `docs/REQUIREMENTS.md` section 8.2 | 7, 8, 12, 15 | Semantic endpoint smoke; relevance score shape check; semantic provider-failure 503 contract check; frontend semantic mode smoke | partial | Backend semantic endpoints use intended fields and now return deterministic `503 embedding_unavailable` envelope when embedding provider fails. Frontend semantic mode remains future work. |
| Two-way matching | `docs/REQUIREMENTS.md` section 7 | 7, 8, 12, 15, 16 | Unit tests for hard filters/scoring; job->resume and resume->job integration tests | partial | Slice 8 closes rerank execution gap with local multilingual reranker + deterministic fallback; end-to-end UI flow and larger seeded ranking evidence remain in later slices. |
| Explainable ranking | `docs/REQUIREMENTS.md` sections 7.3, 7.5, 9 | 8, 12, 15 | Response schema check; reasoning notes tests; runtime metric field checks; UI result card smoke | partial | Matching response now includes additive breakdown/runtime metadata (`bonus/penalty`, phase timings, candidate counters, rerank status/warnings). Frontend rendering validation remains pending. |
| Candidate apply flow | `docs/REQUIREMENTS.md` section 4.3, 6.6 | 9, 10, 12, 15, 16 | Candidate apply integration test; duplicate application test; notification/audit check | partial | Runtime exists, transition graph needs hardening. |
| Recruiter invite flow | `docs/REQUIREMENTS.md` section 4.3, 6.7 | 9, 10, 12, 15, 16 | Invite create/accept/reject integration tests; duplicate accept behavior test | partial | Runtime exists; duplicate pending guard/status checks needed. |
| Application lifecycle | `docs/REQUIREMENTS.md` sections 4.3, 6.6 | 9, 10, 12, 15, 16 | Status transition unit tests; event history verification; terminal lock smoke | partial | Runtime status checks are incomplete. |
| Notifications and email | `docs/REQUIREMENTS.md` sections 4.4, 6.8 | 10, 12, 15, 16 | Notification row checks; email failure non-rollback test; frontend notification smoke | partial | In-app rows exist; email provider not implemented. |
| Audit logs | `docs/REQUIREMENTS.md` sections 6.9, 60 HLD | 10, 11, 12, 16 | Audit row checks for required events; admin audit filter smoke | partial | Some audit exists; consistency incomplete. |
| Admin read-only monitoring | `docs/REQUIREMENTS.md` sections 1, 2, 6.9 | 11, 12, 15, 16 | Admin monitoring integration test; non-admin forbidden smoke | partial | Runtime exists but filters/details incomplete. |
| OpenAPI production namespaces | `docs/REQUIREMENTS.md` section 9 | 0, 1, 3, 4, 8, 9, 12, 16 | `/openapi.json`; schema checks for changed endpoints; no prototype route check | partial | Current surface exists; legacy monolith runtime fallback has been removed and `/api/*` is now served by domain modules. Contract drift remains. |
| Frontend core workflows | `docs/frontend/*` reference plus product/backend docs | 13, 14, 15, 16 | Screen-to-API map; browser smoke for candidate, recruiter, admin | partial | Slice 13 is in review with active screen specs and a screen-to-API/state matrix. Frontend runtime, browser smoke, and real workflow implementation remain Slice 14/15/16. |

## Release Acceptance Rule

Before MVP release or demo readiness is claimed:

- No in-scope requirement above may remain `not_started`.
- Any `partial` requirement must have a named follow-up or an explicit MVP
  deferral decision.
- Core flows must be `accepted`: auth, candidate CV/apply, recruiter
  JD/invite/application, matching, parse success/failure, notifications/audit,
  and admin monitoring.
