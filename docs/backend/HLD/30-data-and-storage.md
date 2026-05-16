# Production HLD: Data And Storage

## Storage Ownership

- PostgreSQL owns users, profiles, organizations, jobs, resumes, parse jobs,
  applications, invites, notifications, email attempts, and audit logs.
- Object storage owns original CV/JD files.
- pgvector columns in PostgreSQL own semantic vectors for job and resume fields.

## Core Tables

Production implementation must provide these entity groups:

- `users`
- `organizations`
- `recruiter_profiles`
- `candidate_profiles`
- `candidate_resumes`
- `job_posts`
- `uploaded_documents`
- `parse_jobs`
- `candidate_resume_embeddings`
- `job_post_embeddings`
- `applications`
- `application_events`
- `recruiter_invites`
- `notifications`
- `email_attempts`
- `audit_logs`

Detailed table columns, constraints, relationships, and index strategy are
defined in `docs/backend/LLD/30-database-schema.md`. That LLD is design
documentation and is not an executable migration.

## Visibility Invariants

- Only `candidate_resumes.status = active` records enter public resume search and
  job -> resume matching.
- Only `job_posts.status = published` records enter public job search and
  resume -> job matching.
- Draft, archived, and closed records remain owner-visible but are excluded from
  public pool behavior.
- `is_primary` is a display/default-selection hint and does not control pool
  visibility.
- Recruiter onboarding includes one predefined Independent organization used by
  the visible `Khác` option for freelance, agency, or independent recruiters.
  This row is seed data, not a hidden tenant boundary.

## Application And Invite Invariants

- `(job_id, resume_id)` applications must be unique.
- Matching results never create applications.
- Candidate apply creates an application.
- Accepted recruiter invite creates an application if one does not already
  exist.
- Rejected invite creates no application.
- Every application status change appends an `application_events` record.
- Allowed MVP application transitions are:
  - recruiter: `submitted -> shortlisted | rejected | hired`
  - recruiter: `shortlisted -> rejected | hired`
  - candidate: `submitted | shortlisted -> withdrawn`
  - terminal: `rejected | hired | withdrawn`
- Every valid application creation/status change writes the required lifecycle
  side effects: application event where applicable, notification, email attempt,
  and audit log.
- Closed jobs reject new applications and recruiter invites.
- Application and invite API responses denormalize linked job/resume display
  summaries and timestamps for frontend list/detail rendering. These are read
  models over the canonical tables, not duplicated persisted application/invite
  columns.

## Notification, Email, And Audit Invariants

- Business events create in-app `notifications` rows before email delivery is
  attempted.
- Every email attempt is persisted to `email_attempts` with event type, target,
  provider, status, timestamps, and metadata.
- Local development uses the local/log email adapter and records attempts as
  `logged`.
- Provider-backed delivery can mark attempts `sent`; provider failures mark
  attempts `failed`.
- Email delivery failure must not roll back parse, application, invite, or
  status-change transactions.
- Audit rows always include actor user ID when known, event type, target entity,
  timestamp, and metadata JSON.

## Embedding Contract

- Initial MVP vector dimension is `384` unless a later model-selection
  requirement changes it.
- Embedding rows must store `embedding_version`.
- Missing field embeddings do not fail a matching run; the affected score
  component is `0` and reasoning must disclose the missing data.
- Re-embedding/backfill requires explicit version handling.

## Legacy Prototype Data

Legacy prototype tables are no longer runtime code artifacts:

- `job_posts_v2`
- `candidate_profiles_v2`
- `job_embeddings_v2`
- `candidate_embeddings_v2`

These tables are not the target production schema. The legacy docs and scenario
documents may remain useful for deterministic matching verification during
future migrations.
