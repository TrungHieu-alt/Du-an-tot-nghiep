# Production HLD: Security, Notifications, And Audit

## Authentication

- Email/password authentication with secure password hashing.
- JWT sessions for API access.
- Disabled users cannot publish, activate, apply, invite, or run matching.

## Authorization

- Candidates manage only their own profile, documents, resumes, applications,
  invites, and notifications.
- Recruiters manage only their own job posts and organization-linked recruiting
  actions.
- Admin MVP is read-only monitoring unless requirements change.
- The product has no tenant isolation in MVP; do not add hidden private company
  behavior.

## Privacy

- Recruiters can search/match only active resumes.
- Candidates can search/match only published jobs.
- Candidate contact data exposure must be limited to the role and flow that
  needs it.
- Logs must not store passwords, JWTs, or raw file contents.

## Notifications

Create in-app notifications and attempt basic email for:

- application submitted.
- recruiter invite sent.
- invite accepted or rejected.
- application status changed.
- parse job failed.

Email delivery failure must be logged and must not roll back the business
transaction.

Runtime email delivery uses an adapter boundary:

- `EMAIL_PROVIDER=local` or unset: local/log sender; no real email is sent and
  attempts are recorded as `logged`.
- `EMAIL_PROVIDER=smtp`: SMTP sender if `SMTP_HOST` and `EMAIL_FROM` are set;
  otherwise runtime falls back to local/log.
- SMTP optional env vars: `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
  `SMTP_USE_TLS`, and `SMTP_TIMEOUT_SECONDS`.

Every notification side effect records an `email_attempts` row with recipient,
event type, target, provider, status, error message when present, timestamps,
and metadata. Email send exceptions are caught after the notification is
created; the business action continues and the email attempt is marked
`failed`.

## Audit

Business audit events are required for:

- resume activated or archived.
- job published or closed.
- parse job failed.
- candidate applied.
- recruiter invite sent.
- invite accepted or rejected.
- application status changed.
- admin monitoring access where useful.

Audit events must include actor user ID when known, target entity, event type,
timestamp, and metadata JSON.

Admin monitoring read endpoints use the same audit policy: read-only access is
audited as `admin_monitoring_access` with the monitored resource and filters in
metadata. This keeps Slice 11 operational monitoring data visible without
adding admin write behavior.

## Observability

Minimum operational signals:

- parse queue state and failure reasons.
- matching request count and latency.
- notification creation and email delivery failures.
- application and invite lifecycle events.
- API error rates for auth, upload, parse, matching, and application flows.

