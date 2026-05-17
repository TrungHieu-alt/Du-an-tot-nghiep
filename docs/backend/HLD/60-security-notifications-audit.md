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

### Email Adapter

Runtime email delivery uses an adapter boundary:

- `integrations/email/base.py` — `EmailSender` abstract interface (`send(to, subject, body)`).
- `integrations/email/local.py` — `LocalLogEmailSender`: writes to application log; attempts recorded as `logged`. Default for dev/test.
- `integrations/email/__init__.py` — `get_email_sender()` factory; env var `EMAIL_PROVIDER` (default `local`).
- `EMAIL_PROVIDER=local` or unset: local/log sender; no real email is sent.
- `EMAIL_PROVIDER=smtp`: SMTP sender if `SMTP_HOST` and `EMAIL_FROM` are set; otherwise falls back to local/log.
- SMTP optional env vars: `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_USE_TLS`, `SMTP_TIMEOUT_SECONDS`.

`notify()` in `shared.py` writes the `notifications` row, records an
`email_attempts` row, and calls `audit()` — all within the same cursor/transaction
as the business action. Email send exceptions are caught; the business action
continues and the email attempt is marked `failed`. Email delivery failure must
not roll back the business transaction.

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

