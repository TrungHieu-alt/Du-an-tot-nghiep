# Production HLD: API And Runtime Flows

## API Surface

Production API namespaces replace the prototype routes:

- `/api/auth/*`
- `/api/me`
- `/api/candidate/profile`
- `/api/candidate/resumes/*`
- `/api/recruiter/profile`
- `/api/organizations/*`
- `/api/jobs/*`
- `/api/documents/*`
- `/api/matching/*`
- `/api/applications/*`
- `/api/invites/*`
- `/api/notifications/*`
- `/api/admin/*`

This is a breaking change from `/api/v2/prototype/*`.

## Core Runtime Flows

Candidate CV flow:

```text
register/login
  -> upload CV
  -> parse job async
  -> review parsed resume
  -> activate resume
  -> search/match published jobs
  -> apply or respond to invite
```

Recruiter JD flow:

```text
register/login
  -> create organization/profile
  -> upload or create JD
  -> parse job async
  -> review parsed job
  -> publish job
  -> search/match active resumes
  -> invite candidate or manage applications
```

Matching flow:

```text
validate auth and role
  -> validate anchor visibility
  -> retrieve eligible opposite pool
  -> apply hard filters
  -> score and optional rerank
  -> return ranked results with reasoning
```

Application flow:

```text
candidate apply OR accepted invite
  -> create application
  -> append application event
  -> create notification
  -> write audit event
```

## OpenAPI Requirements

- Every route must have explicit request and response schemas.
- Enums must be represented in OpenAPI.
- Upload endpoints must document MIME type and file-size limits.
- Parse status endpoints expose `queued`, `processing`, `succeeded`, and
  `failed`.
- Matching responses include rank, final score, component scores, exact skill
  overlap, and reasoning.
- Application and invite endpoints document allowed status transitions.

## Current Runtime Compatibility

The existing implementation exposes production `/api/*` routes. Legacy
`/api/v2/prototype/*` routes are not implemented in runtime code.
