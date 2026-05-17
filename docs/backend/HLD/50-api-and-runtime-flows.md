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
  -> review parsed resume fields and save corrections
  -> activate resume
  -> Job Market search or match published jobs from one selected active CV
  -> apply or respond to invite
```

Recruiter JD flow:

```text
register/login
  -> choose organization, create organization, or use predefined Independent org
  -> create recruiter profile
  -> upload or create JD
  -> parse job async
  -> review parsed job fields and save corrections
  -> publish job
  -> Talent Market search or match active resumes from one selected published JD
  -> invite candidate or manage applications
```

Matching flow:

```text
validate auth and role
  -> validate anchor visibility
  -> candidate anchor: active owned resume, rendered in Job Market
  -> recruiter anchor: published owned job, rendered in Talent Market
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
  -> record email attempt through the configured email adapter
  -> write business and email audit events
```

## OpenAPI Requirements

- Every route must have explicit request and response schemas.
- Enums must be represented in OpenAPI.
- Upload endpoints must document MIME type and file-size limits.
- Parse status endpoints expose `queued`, `processing`, `succeeded`, and
  `failed`.
- Parse job detail endpoints expose the reviewed parsed-field payload, extracted
  text reference, parser metadata, embedding metadata, and linked target
  `resume_id` or `job_id` required by the frontend review form.
- Job list/search responses include linked organization display fields
  (`organization_name`, `organization_logo_url`, `organization_slug`) to avoid
  per-row organization fetches.
- Matching responses include rank, final score, component scores, exact skill
  overlap, and reasoning.
- Application and invite endpoints document allowed status transitions.
- Application and invite list/detail responses include denormalized linked
  job/resume summaries and timestamps for production frontend tables.
- The predefined Independent organization used by the recruiter `Khác` option is
  documented as seed data and exposed through organization lookup.

## Current Runtime Compatibility

The existing implementation exposes production `/api/*` routes. Legacy
`/api/v2/prototype/*` routes are not implemented in runtime code.
