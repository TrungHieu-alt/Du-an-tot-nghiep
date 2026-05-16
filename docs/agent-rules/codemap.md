# Codemap (Workflow-Centric)

Purpose: workflow ownership and path mapping. Policy and process rules are
canonical in `AGENTS.md`.

## Documentation Map

- Product source of truth:
  - `docs/REQUIREMENTS.md`
- Backend architecture:
  - `docs/backend/HLD/`
- Agent doc router:
  - `docs/agent-rules/doc-map.md`

## 1) Platform Bootstrap And API Surface

Current code paths:

- `backend/main.py` (compatibility wrapper)
- `backend/src/jobconnect/main.py`
- `backend/src/jobconnect/app.py`
- `backend/src/jobconnect/modules/api/router.py` (current monolithic `/api/*` router)
- `backend/src/jobconnect/modules/system/router.py`
- `backend/src/jobconnect/core/database.py`
- `backend/db/migrations/001_production_mvp.sql`
- `backend/db/apply_migrations.py`

Current runtime boundary:

- App routes under `/api/*`.
- Legacy `/api/v2/prototype/*` runtime code has been removed.
- PostgreSQL tables are defined in `backend/db/migrations/`.

Use this section for tasks that target the runtime surface.

## 1A) Backend Module Layout

Current source layout:

- `backend/src/jobconnect/main.py`: FastAPI app entrypoint.
- `backend/src/jobconnect/app.py`: app metadata and router registration.
- `backend/src/jobconnect/core/`: infrastructure boundaries such as config,
  database, security, exceptions, and logging.
- `backend/src/jobconnect/common/`: shared dependencies, pagination, responses,
  utilities, and constants.
- `backend/src/jobconnect/integrations/`: external integration boundaries such
  as pgvector, future object storage, email, and LLM providers.
- `backend/src/jobconnect/modules/api/router.py`: current centralized `/api/*`
  implementation. Do not split it unless the task explicitly asks for API
  module extraction.
- `backend/src/jobconnect/modules/*/`: feature ownership folders for future
  route/service/schema splits.
- `backend/db/`: migrations and database maintenance scripts.

Current feature module ownership targets:

- `modules/auth/`: authentication and token/session helpers.
- `modules/users/`: users, candidate profiles, and recruiter profiles.
- `modules/organizations/`: employer organization ownership.
- `modules/jobs/`: job post lifecycle and search ownership.
- `modules/resumes/`: candidate resume lifecycle and search ownership.
- `modules/documents/`: uploaded documents and parse jobs.
- `modules/matching/`: hard filters, scoring, reasoning, embeddings, and vector
  search helpers.
- `modules/applications/`: applications and application events.
- `modules/invites/`: recruiter invite lifecycle.
- `modules/notifications/`: notification records and email status boundaries.
- `modules/admin/`: read-only admin monitoring.
- `modules/system/`: health and runtime probes.

## 1B) Legacy Prototype Reference Surface

Legacy code paths:

- none in runtime code.

Legacy runtime boundary:

- `/api/v2/prototype/*` is no longer implemented in code.
- Legacy prototype behavior remains available only as documentation under
  `docs/backend/HLD/legacy/` and matching scenario docs.

Use this section only for reading legacy reference material.

## 2) Auth, Users, And Profiles

Target docs:

- `docs/REQUIREMENTS.md`
- `docs/backend/HLD/10-architecture-overview.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`
- `docs/backend/HLD/60-security-notifications-audit.md`

Target entities:

- `users`
- `candidate_profiles`
- `recruiter_profiles`
- `organizations`

Current code areas:

- `backend/src/jobconnect/modules/api/router.py` contains
  auth/profile/organization route handlers, schemas, and authorization
  dependencies.
- Future split target folders: `modules/auth/`, `modules/users/`, and
  `modules/organizations/`.

## 3) Documents, Parsing, And Normalization

Target docs:

- `docs/backend/HLD/20-ingestion-and-normalization.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`

Target entities:

- `uploaded_documents`
- `parse_jobs`
- `candidate_resumes`
- `job_posts`
- embedding tables.

Current code areas:

- `backend/src/jobconnect/modules/api/router.py` contains document
  metadata and parse-job routes.
- Future split target folders: `modules/documents/`, `modules/resumes/`, and
  `modules/jobs/`.
- External storage/parser/email provider adapters are represented at the API
  boundary and still need concrete provider implementations.

## 4) Matching And Search

Target docs:

- `docs/backend/HLD/40-matching-and-search-pipeline.md`
- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`

Target behavior:

- job anchor ranks active resumes.
- resume anchor ranks published jobs.
- keyword search and semantic search remain separate.
- matching results are recommendations and do not create applications.

Current code areas:

- `backend/src/jobconnect/modules/api/router.py` contains search and matching
  routes over `candidate_resumes`, `job_posts`, and embedding tables.
- `backend/src/jobconnect/modules/matching/` contains pure scoring, hard-filter,
  reasoning, and deterministic local embedding helpers.
- Future route/service split target: keep matching algorithm helpers in
  `modules/matching/` and move only API handlers out of `modules/api/` when
  explicitly requested.

## 5) Applications, Invites, Notifications, And Audit

Target docs:

- `docs/backend/HLD/30-data-and-storage.md`
- `docs/backend/HLD/50-api-and-runtime-flows.md`
- `docs/backend/HLD/60-security-notifications-audit.md`

Target entities:

- `applications`
- `application_events`
- `recruiter_invites`
- `notifications`
- `audit_logs`

Current code areas:

- `backend/src/jobconnect/modules/api/router.py` contains
  application, invite, notification, audit, and admin monitoring route handlers.
- Future split target folders: `modules/applications/`, `modules/invites/`,
  `modules/notifications/`, and `modules/admin/`.

## 6) Legacy Prototype Matching Verification

Legacy docs:

- `docs/backend/HLD/legacy/legacy-overview-and-problem.md`
- `docs/backend/HLD/legacy/legacy-architecture-overview.md`
- `docs/backend/HLD/legacy/legacy-matching-pipeline.md`
- `docs/backend/HLD/legacy/legacy-data-and-storage.md`
- `docs/backend/HLD/legacy/legacy-api-and-runtime-flows.md`
- `docs/matching-v2-scenario-test-cases.md`

Rule for agents:

- Treat these as legacy reference and migration verification assets.
- Do not edit the scenario docs unless the user explicitly asks to change legacy
  prototype matching verification.
- Reuse deterministic hard-filter/scoring cases when migrating app
  matching tests.

## 7) Frontend Planning Notes

Active screen specs:

- `docs/frontend/screen/auth-screen.md`
- `docs/frontend/screen/candidate-profile-setup.md`
- `docs/frontend/screen/recruiter-profile-setup.md`
- `docs/frontend/screen/upload-parse-review.md`
- `docs/frontend/screen/job-market.md`
- `docs/frontend/screen/talent-market.md`
- `docs/frontend/screen/job-detail.md`
- `docs/frontend/screen/resume-detail.md`
- `docs/frontend/screen/records-management.md`
- `docs/frontend/screen/invite-application-flow.md`
- `docs/frontend/screen/account-settings.md`

Archived reference notes:

- `docs/frontend/design-system.md`
- `docs/frontend/screen-specifications.md`
- `docs/frontend/user-flows.md`
- `docs/frontend/figma-implementation-guide.md`
- `docs/frontend/ATTRIBUTIONS.md`

No frontend runtime code is present. Follow `README.md` Frontend Planning Rule;
screen specs under `docs/frontend/screen/` are the active Slice 13 design
source.

## 8) Integration Boundary

- App contract evolution is OpenAPI-first.
- `/api/*` contracts are the main app baseline.
- `/api/v2/prototype/*` is legacy-only documentation and is not implemented in
  runtime code.
- The `/api/*` migration is breaking relative to the prototype API.
