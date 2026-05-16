# MVP Implementation Slices

Status values: `not_started | in_progress | blocked | review | done`.

Each slice should be completed with command-backed verification before it is
marked `done`. Backend runtime checks must use Docker Compose unless the team
explicitly records why Docker is unavailable.

## API Split Migration Note (2026-05-16)

- The runtime API behavior is served by domain modules under
  `backend/src/jobconnect/modules/*/{router.py,schemas.py,service.py}`.
- `backend/src/jobconnect/modules/api/_legacy_api_impl.py` has been removed.
- `backend/src/jobconnect/modules/api/router.py` is now an aggregator with
  compatibility re-exports used by app wiring and tests.
- Slices that touch API behavior should continue aligning endpoint behavior with:
  - `docs/backend/LLD/40-api-contract.md`
  - `docs/backend/LLD/50-current-api-implementation-matrix.md`
  - `docs/REQUIREMENTS.md`

## Slice 0: Baseline Contract Audit

Status: `done`

Goal: create the exact implementation backlog from the current backend against
the product and API contract docs.

Why now: this prevents the team from implementing frontend or providers against
runtime behavior that is already known to drift from the target contract.

In scope:

- Compare current OpenAPI, runtime routes, migration, and docs.
- Update the gap list as `Aligned`, `Partial`, `Drift`, or `Missing`.
- Classify each needed API change as `none`, `non-breaking`, or `breaking`.

Out of scope:

- Runtime behavior changes.
- Frontend implementation.

Impacted paths:

- `docs/REQUIREMENTS.md`
- `docs/backend/LLD/40-api-contract.md`
- `docs/backend/LLD/50-current-api-implementation-matrix.md`
- `backend/src/jobconnect/modules/api/router.py`
- `backend/db/migrations/001_production_mvp.sql`

Dependencies: none.

API/OpenAPI impact: `none` for audit only.

DoD:

- Current implementation matrix reflects the latest runtime surface.
- Every high-risk drift has an owner-ready follow-up slice.
- Contract and behavior gaps are not mixed with frontend styling tasks.

Verification evidence required:

- Docker startup result.
- Migration result.
- `/api/health` result.
- `/openapi.json` result.
- Backend unittest result.

Handoff checklist:

- List updated docs.
- List unresolved blockers.
- List next slice recommendation.

## Slice 1: Auth, Session, And `/api/me`

Status: `done`

Goal: make auth and current-user bootstrap stable enough for frontend and
protected backend workflows.

Why now: nearly every later slice depends on authenticated role-aware behavior.

In scope:

- Add explicit JWT expiry behavior and return `expires_in` from register/login.
- Reject expired or invalid tokens.
- Return user plus role-specific bootstrap data from `/api/me`.
- Keep logout stateless unless token revocation is explicitly added later.

Out of scope:

- OAuth/social login.
- Refresh tokens unless separately required.
- Admin user invitation flows.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/core/security.py`
- `backend/tests/`
- `docs/backend/LLD/40-api-contract.md`

Dependencies: Slice 0 recommended.

API/OpenAPI impact: `non-breaking` if additive except `/api/me`; `/api/me`
response shape is `breaking` relative to the current runtime.

DoD:

- Register/login responses include `expires_in`.
- Expired tokens fail.
- Disabled users remain blocked from protected active actions.
- `/api/me` exposes candidate/recruiter bootstrap fields as documented.

Verification evidence required:

- Success and failure auth smoke calls.
- Test for expired token.
- Test for `/api/me` candidate, recruiter, and admin shapes.
- OpenAPI schema check.

Handoff checklist:

- Record token expiry duration and rationale.
- Record compatibility note for `/api/me`.

## Slice 2: Ownership And Authorization

Status: `done`

Goal: close role and ownership gaps before marketplace actions are trusted.

Why now: upload, matching, applications, and frontend workflows depend on clear
resource visibility and permission rules.

In scope:

- Recruiters can update only their own organization-linked profile/jobs.
- Matching anchors require owner visibility, except admin.
- Candidates see only their own private records plus published jobs.
- Recruiters see public active resumes and their own jobs.
- Admin remains read-only for MVP.

Out of scope:

- Company tenant isolation.
- Fine-grained team permissions.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/tests/`
- `docs/backend/HLD/60-security-notifications-audit.md`
- `docs/backend/LLD/40-api-contract.md`

Dependencies: Slice 1 recommended.

API/OpenAPI impact: `non-breaking` behavior hardening; some clients may start
receiving correct `403` or `404` responses.

DoD:

- Ownership checks are explicit for organization, job, resume, matching,
  application, invite, document, and notification actions.
- Disabled users cannot publish, activate, apply, invite, or run matching.
- Admin write behavior is not silently expanded.

Verification evidence required:

- Success and forbidden cases for org update, job update, resume match, job
  match, document access, and notification access.
- OpenAPI protected route security check.

Handoff checklist:

- List all tightened endpoints.
- Record any behavior now intentionally denied.

## Slice 3: API Contract Drift Cleanup

Status: `done`

Goal: align existing CRUD, list, and detail endpoints with the target contract
before frontend depends on them.

Why now: frontend should not be built around response shapes and filters that
are already known to be temporary.

In scope:

- Convert resume, job, and organization PATCH endpoints to partial updates.
- Add missing filters for jobs, organizations, admin resources, and audit logs.
- Fix response drift such as notifications `updated_count`.
- Replace generic dict responses with explicit Pydantic response models where
  required.
- Ensure canonical enums appear in OpenAPI.

Out of scope:

- Multipart upload.
- Provider integrations.
- Visual frontend work.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/tests/`
- `docs/backend/LLD/40-api-contract.md`
- `docs/backend/LLD/50-current-api-implementation-matrix.md`

Dependencies: Slices 0-2 recommended.

API/OpenAPI impact: mix of `non-breaking` additions and targeted `breaking`
cleanup for current drift.

DoD:

- PATCH endpoints accept partial bodies.
- List/search filters match the API LLD where implemented.
- Response models are explicit for touched endpoints.
- OpenAPI reflects the corrected contract.

Verification evidence required:

- Endpoint smoke calls for one success and one validation/error case per touched
  workflow.
- OpenAPI diff summary.
- Backend unittest result.

Handoff checklist:

- Record each contract delta.
- Mark breaking changes clearly.

## Slice 4: Document Upload Foundation

Status: `done`

Goal: implement the real upload contract and file persistence boundary.

Why now: candidate CV and recruiter JD flows start with original document upload.

In scope:

- `POST /api/documents` accepts `multipart/form-data`.
- Enforce PDF MIME and configured file size limit.
- Store files through a storage adapter.
- First implementation may use local filesystem storage if the adapter is
  compatible with future S3-compatible storage.
- Create `uploaded_documents` and queued `parse_jobs`.
- Return `{ document, parse_job }`.

Out of scope:

- Full parse execution.
- LLM extraction.
- Real cloud storage if local adapter is chosen for the first pass.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/integrations/`
- `backend/db/migrations/001_production_mvp.sql`
- `backend/tests/`
- `docs/backend/HLD/20-ingestion-and-normalization.md`
- `docs/backend/LLD/40-api-contract.md`

Dependencies: Slices 1-3.

API/OpenAPI impact: `breaking` from current JSON metadata endpoint to target
multipart upload contract.

DoD:

- Valid PDF upload creates document and queued parse job.
- Unsupported MIME returns `415`.
- Oversized file returns `413`.
- Unauthorized upload returns `401` or `403`.
- Original file remains available through the storage adapter.

Verification evidence required:

- Multipart upload success smoke.
- MIME failure smoke.
- Size failure smoke.
- Parse job read smoke.
- OpenAPI upload schema check.

Handoff checklist:

- Record storage adapter mode and configured limits.
- Record future S3 swap requirements if local storage is used.

## Slice 5: Parse Worker V1

Status: `done`

Goal: make upload-to-draft-entity run end to end with deterministic local
behavior.

Why now: users need parsed draft CV/JD data before activation or publishing.

In scope:

- Process queued parse jobs through `processing`, `succeeded`, or `failed`.
- Extract text from supported files.
- Preprocess text with Unicode NFC normalization and whitespace/control cleanup.
- Normalize high-impact skill aliases.
- Create or update draft resume/job records.
- Link document and parse job to the created entity.
- Generate embeddings after structured data is available.
- On failure, preserve file, store error, create notification, and write audit.

Out of scope:

- High-quality LLM extraction.
- Cross-encoder reranking.
- Production queue infrastructure unless explicitly chosen.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/modules/documents/`
- `backend/src/jobconnect/modules/resumes/`
- `backend/src/jobconnect/modules/jobs/`
- `backend/src/jobconnect/modules/matching/`
- `backend/tests/`

Dependencies: Slice 4.

API/OpenAPI impact: `non-breaking` if parse status contract remains stable.

DoD:

- One CV fixture parses to a draft resume.
- One JD fixture parses to a draft job.
- One bad file produces failed parse state, notification, and audit event.
- Retry creates a new parse job when allowed.

Verification evidence required:

- Parse success smoke for CV and JD.
- Parse failure smoke.
- Notification/audit row verification.
- Embedding row verification.

Handoff checklist:

- Record parser version.
- Record extraction limitations.

## Slice 6: LLM Parser Adapter

Status: `done`

Goal: add production-style structured parsing behind an adapter while keeping
local development runnable.

Why now: MVP quality depends on mapping mixed Vietnamese/English CV/JD text into
canonical fields without inventing enum values.

In scope:

- Parser interface with constrained JSON schema.
- Configured LLM provider adapter.
- Deterministic fallback for dev/test when provider env vars are absent.
- Canonical enum validation and safe failure handling.
- Parser version stored on parse jobs.

Out of scope:

- Model quality benchmarking claims.
- Translation of full documents.

Impacted paths:

- `backend/src/jobconnect/integrations/`
- `backend/src/jobconnect/modules/documents/`
- `backend/src/jobconnect/modules/resumes/`
- `backend/src/jobconnect/modules/jobs/`
- `backend/tests/`
- `docs/backend/HLD/20-ingestion-and-normalization.md`

Dependencies: Slice 5.

API/OpenAPI impact: `none` unless parse error response fields change.

DoD:

- Vietnamese, English, and mixed-language fixtures map into canonical enums.
- Unsupported or invalid LLM output fails safely.
- Raw unsupported enum values are not persisted as canonical labels.
- Parser version and error details are visible in parse job state.

Verification evidence required:

- Parser fixture tests.
- Failed provider/fallback test.
- Parse job status smoke.

Handoff checklist:

- Record provider env vars.
- Record fallback behavior.

## Slice 7: Embedding And Semantic Search

Status: `done`

Goal: make semantic search and matching embeddings versioned, useful, and
replaceable.

Why now: matching/search quality should improve without coupling business logic
to one provider.

In scope:

- Embedding provider interface.
- Local hash embedding remains dev fallback.
- Configurable production embedding provider.
- Store and check embedding version.
- Semantic job/resume search uses intended text fields.
- Missing embeddings score `0` and appear in reasoning notes.

Out of scope:

- BM25 hybrid retrieval.
- Labeled quality benchmarking.

Impacted paths:

- `backend/src/jobconnect/modules/matching/`
- `backend/src/jobconnect/integrations/`
- `backend/src/jobconnect/modules/api/router.py`
- `backend/db/migrations/001_production_mvp.sql`
- `backend/tests/`

Dependencies: Slices 3 and 5.

API/OpenAPI impact: `non-breaking` if response shape remains stable.

DoD:

- Embedding rows contain version.
- Semantic search applies filters and returns relevance scores.
- Missing embedding behavior is graceful.
- Ordering is deterministic for equal scores.

Verification evidence required:

- Semantic search smoke for jobs and resumes.
- Missing embedding test.
- Version persistence check.

Handoff checklist:

- Record provider and embedding version.
- Record re-embedding/backfill implications.

Risk sweep update (2026-05-16):

- Semantic resume search now ranks against CV summary/experience embeddings,
  not title embeddings.
- Semantic job search now ranks against JD requirement embeddings, not title
  embeddings.
- Parse-job creation/retry and worker success metadata persist the active
  embedding provider version instead of hard-coded `hash-v1`.
- Go for Slice 8. Application lifecycle transition graph and terminal-state
  lock moved to Slice 9 tracking and are no longer Slice 7 backlog.

## Slice 8: Matching Production Hardening

Status: `done`

Goal: complete explainable two-way matching behavior from requirements.

Why now: matching is the core product outcome and must be reliable before UI
polish.

In scope:

- Enforce published job and active resume anchor eligibility.
- Apply all hard filters exactly.
- Preserve deterministic formula and tie-breaks.
- Include full breakdown, overlap, hard-filter notes, missing embedding notes,
  reasoning, and runtime metrics.
- Keep matching as recommendation-only with no application/invite side effects.

Out of scope:

- AI-only automatic decisions.
- Cross-encoder reranking unless separately enabled.

Impacted paths:

- `backend/src/jobconnect/modules/matching/`
- `backend/src/jobconnect/modules/api/router.py`
- `backend/tests/`
- `docs/matching-v2-scenario-test-cases.md`

Dependencies: Slices 2, 3, and 7.

API/OpenAPI impact: `non-breaking` if response fields are additive/aligned;
otherwise record exact contract delta.

DoD:

- Job anchor ranks active resumes only.
- Resume anchor ranks published jobs only.
- Hard filter failures do not enter ranked results.
- Tie-breaks are deterministic.
- Reasoning is grounded in score breakdown and structured fields.

Verification evidence required:

- Seeded job-to-resume match smoke.
- Seeded resume-to-job match smoke.
- No-match-above-threshold case.
- Missing embedding case.

Handoff checklist:

- Record representative input and top result trend.
- Record any ranking changes.

## Slice 9: Applications And Invites

Status: `done`

Goal: make ATS-lite application and invite lifecycle complete and safe.

Why now: matching must connect to real business actions without creating
applications automatically.

In scope:

- Candidate apply to published job with active owned resume.
- Recruiter invite active resume to published owned job.
- Accepted invite creates or returns existing application.
- Rejected invite creates no application.
- Enforce application transition graph.
- Closed jobs reject new applications and invites.
- Application detail includes event history.

Out of scope:

- Configurable stages.
- Interview scheduling.
- Offer approvals.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/modules/applications/`
- `backend/src/jobconnect/modules/invites/`
- `backend/tests/`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/LLD/40-api-contract.md`

Dependencies: Slices 2 and 3.

API/OpenAPI impact: `non-breaking` behavior hardening unless response models
change for application event history. Slice 9 adds typed application/invite
list response models and linked summary/timestamp fields, which is additive for
existing clients.

DoD:

- Duplicate `(job_id, resume_id)` application is rejected with `409`.
- Duplicate accepted invite returns existing application as documented.
- Terminal application states cannot move further.
- Every status change writes application event, notification, and audit event.

Verification evidence required:

- Apply success and duplicate smoke.
- Invite create/accept/reject smoke.
- Invalid transition smoke.
- Terminal lock smoke.

Handoff checklist:

- Record allowed transition graph.
- Record all side effects verified.

Implementation note (2026-05-17):

- Candidate apply now requires active owned resume plus published non-closed
  job; duplicate `(job_id, resume_id)` returns `409 duplicate_application`.
- Recruiter invite now requires active resume plus owned published non-closed
  job; duplicate pending invite returns `409 duplicate_invite`.
- Invite accept creates an application and event when absent, or returns the
  existing application without duplicate application/event rows.
- Invite reject creates no application.
- Application status transitions use the canonical graph:
  recruiter `submitted -> shortlisted | rejected | hired`, recruiter
  `shortlisted -> rejected | hired`, candidate
  `submitted | shortlisted -> withdrawn`, terminal
  `rejected | hired | withdrawn`.
- Verification: Docker Compose backend/postgres healthy; migration exit 0;
  targeted `python -m unittest tests.test_slice9_applications_invites` passed
  12/12; targeted Slice 9 + contract tests passed 30/30; full backend unittest
  suite passed 151/151; `/api/health` returned `ok`; live `/openapi.json`
  exposed 47 paths, 51 schemas, and application/invite list response schemas.

## Slice 10: Notifications, Email, Audit

Status: `not_started`

Goal: make business side effects visible and non-blocking.

Why now: parse failure, application, invite, and status changes need user-facing
and operational evidence.

In scope:

- Email sender adapter.
- Local/log sender for development.
- Provider sender if configured.
- Email failure logging without transaction rollback.
- Required notification and audit events.
- Consistent admin monitoring audit policy.

Out of scope:

- Marketing campaigns.
- Notification preference center.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/modules/notifications/`
- `backend/src/jobconnect/integrations/`
- `backend/tests/`
- `docs/backend/HLD/60-security-notifications-audit.md`

Dependencies: Slices 5 and 9.

API/OpenAPI impact: `non-breaking` unless notification response fields change.

DoD:

- Required business events create in-app notifications.
- Email attempts are recorded.
- Email failure does not roll back parse/application/invite transactions.
- Audit rows include actor, event type, target, timestamp, and metadata.

Verification evidence required:

- Notification creation smoke.
- Email failure smoke.
- Audit log query smoke.

Handoff checklist:

- Record email adapter mode.
- Record event coverage.

## Slice 11: Admin Monitoring

Status: `not_started`

Goal: complete read-only admin monitoring for MVP operations.

Why now: production-like MVP needs visibility into users, content, parse jobs,
matching, notifications, and audit state.

In scope:

- Admin filters from the API contract.
- Admin user detail with profile and operational summary.
- Document and parse job monitoring with failure context.
- Application, invite, notification, and audit monitoring filters.

Out of scope:

- Destructive moderation.
- Admin write actions.

Impacted paths:

- `backend/src/jobconnect/modules/api/router.py`
- `backend/src/jobconnect/modules/admin/`
- `backend/tests/`
- `docs/backend/LLD/40-api-contract.md`

Dependencies: Slices 2, 3, 5, 9, and 10.

API/OpenAPI impact: `non-breaking` if additive filters and richer details are
introduced.

DoD:

- Admin can monitor all required resources.
- Non-admin users are denied admin endpoints.
- Admin responses include enough operational context to debug MVP flows.

Verification evidence required:

- Admin success smoke for each endpoint.
- Non-admin denial smoke.
- Filter smoke for each monitored resource type.

Handoff checklist:

- Record admin filter coverage.
- Record any intentionally deferred monitoring metric.

## Slice 12: Backend End-to-End Hardening

Status: `not_started`

Goal: make backend ready for frontend and MVP demo flows.

Why now: this is the backend integration gate before full frontend workflow
build-out.

In scope:

- End-to-end candidate flow.
- End-to-end recruiter flow.
- End-to-end admin monitoring flow.
- OpenAPI contract review.
- Error envelope consistency.
- CORS and frontend integration assumptions.

Out of scope:

- Frontend implementation.
- Production infrastructure deployment.

Impacted paths:

- `backend/src/jobconnect/`
- `backend/tests/`
- `docs/backend/LLD/40-api-contract.md`
- `docs/backend/LLD/50-current-api-implementation-matrix.md`

Dependencies: Slices 1-11.

API/OpenAPI impact: `none` unless hardening discovers contract fixes.

DoD:

- Candidate can register, upload CV, parse, activate, match, and apply.
- Recruiter can register, create organization/profile, upload/create JD,
  publish, match, invite, and manage application.
- Admin can inspect operational state.
- Smoke-contract gate passes.

Verification evidence required:

- Full backend smoke command log.
- OpenAPI availability.
- Endpoint success and error examples.

Handoff checklist:

- Record remaining backend gaps.
- Mark frontend readiness status.

## Slice 13: Frontend Design Direction

Status: `review`

Goal: define a simple, implementable frontend direction without resurrecting the
removed prototype.

Why now: team wants UI progress in parallel, with a concrete flow for
upload/parse review before full frontend runtime implementation.

In scope:

- Select external recruiting/ATS/product references for layout inspiration.
- Define simple screen flow for Auth, Workspace Home, Jobs Library, CVs Library,
  Upload + Parse Review, Detail pages, Matching Workspace, Applications/Invites,
  Notifications, and Admin minimal pages.
- Define the screen-to-API/state matrix and Vietnamese UI copy contract while
  keeping planning documentation in English.
- Define Upload + Parse Review screen contract for both CV and JD modes.
- Define mandatory hard-filter confirmation rule in review step before
  activation/publish-ready usage when upload path is used.
- Decide low-polish visual baseline focused on data correctness.
- Document what must wait for backend contract readiness.

Out of scope:

- High-fidelity visual system.
- Frontend runtime code.

Impacted paths:

- `docs/frontend/`
- `docs/mvp-roadmap/`
- future `frontend/`

Dependencies: Slice 0 and early backend contract direction.

API/OpenAPI impact: `none`.

DoD:

- Screen inventory exists.
- Each screen maps to backend APIs or explicit mock data.
- `docs/frontend/screen/*` is established as the active Slice 13 design brief.
- Upload + Parse Review flow is explicitly documented as a dedicated page.
- Hard-filter confirmation rule is explicit in the design brief.
- Archived prototype-adjacent frontend docs remain labeled reference only.
- Style level is intentionally simple and data-first.

Verification evidence required:

- Design reference notes.
- Screen-to-API map.
- Vietnamese UI copy/state coverage for production-like error, empty,
  authorization, and lifecycle states.

Handoff checklist:

- Record chosen external references.
- Record frontend assumptions and blocked API dependencies.

## Slice 14: Frontend Shell And API Client

Status: `not_started`

Goal: create active frontend runtime foundation.

Why now: frontend can start once core auth and API contracts are stable enough.

In scope:

- Frontend scaffold under the agreed runtime root, likely `frontend/`.
- App routing.
- Auth state and session handling.
- API client based on OpenAPI or manually typed stable contracts.
- Role-aware navigation.
- Error envelope display.

Out of scope:

- Full workflow screens.
- Visual polish.

Impacted paths:

- future `frontend/`
- `docker-compose.yml`
- `README.md`

Dependencies: Slices 1-3 and Slice 13.

API/OpenAPI impact: `none` unless frontend work identifies backend contract
bugs.

DoD:

- Frontend starts through Docker Compose.
- Register/login and `/api/me` work from UI.
- Route guards work by role.
- API errors render clearly.

Verification evidence required:

- Frontend startup command.
- Auth smoke.
- Session expired smoke.
- API error smoke.

Handoff checklist:

- Record frontend stack and command.
- Record API client generation/manual typing choice.

## Slice 15: Frontend Core Workflows

Status: `not_started`

Goal: implement simple UI for the real MVP flows using real backend data.

Why now: after backend contracts and frontend shell are ready, users need to
validate data display and workflow ergonomics.

In scope:

- Candidate profile, upload, parse status, resume edit/activate, job search,
  matching, apply, invite response.
- Recruiter organization/profile, job upload/create, publish, resume search,
  matching, invite, application status management.
- Admin read-only monitoring pages.
- Exact search and semantic search as separate UI modes.
- Matching result cards with score breakdown and reasoning.

Out of scope:

- High-polish marketing-style UI.
- Saved searches, compare view, advanced analytics unless separately added.

Impacted paths:

- future `frontend/`
- `docs/frontend/`
- `docs/mvp-roadmap/`

Dependencies: Slices 12 and 14.

API/OpenAPI impact: `none` unless backend contract bugs are found.

DoD:

- Candidate, recruiter, and admin core flows can be completed from UI.
- Empty, loading, error, not found, and no-match states exist.
- UI displays real backend data without hidden static fixtures.

Verification evidence required:

- Browser smoke checklist for candidate, recruiter, and admin.
- API network smoke for critical flows.
- Responsive check for desktop and basic mobile/tablet.

Handoff checklist:

- Record incomplete polish.
- Record backend bugs found by UI.

## Slice 16: End-to-End MVP Hardening

Status: `not_started`

Goal: prepare the whole MVP for demo/release-style validation.

Why now: this is the final integration pass after backend and frontend core
flows exist.

In scope:

- Full candidate journey.
- Full recruiter journey.
- Admin operational review.
- Error recovery paths.
- Documentation and README update.
- Smoke-contract and browser smoke evidence.

Out of scope:

- Non-MVP features such as billing, scheduling, CRM campaigns, tenant isolation,
  or advanced ATS customization.

Impacted paths:

- `backend/`
- future `frontend/`
- `docs/`
- `README.md`
- `docker-compose.yml`

Dependencies: Slices 0-15.

API/OpenAPI impact: `none` unless final hardening finds contract defects.

DoD:

- MVP can be run from clean setup instructions.
- Backend smoke-contract gate passes.
- Frontend smoke checklist passes.
- Known gaps are documented, visible, and not hidden as done work.

Verification evidence required:

- Clean setup command log.
- Migration command log.
- Backend test and smoke log.
- Frontend test/build/smoke log.
- Manual scenario evidence for candidate, recruiter, and admin.

Handoff checklist:

- Record release-readiness status.
- Record remaining risks and follow-up slices.
