# Production HLD: Overview And Problem

## Problem

The product target is no longer a run-only matching prototype. The target system
is a production MVP recruiting marketplace where candidates and recruiters share
one public pool of active CVs and published jobs, then use explainable matching
to start applications or recruiter invites.

Current repository code now exposes the production `/api/*` backend surface and
uses a module-oriented FastAPI layout under `backend/src/jobconnect`.

## Users

- Candidate: uploads CVs, reviews parsed data, activates one or more resumes,
  matches against published jobs, applies to jobs, and responds to invites.
- Recruiter: manages an employer organization profile, creates or uploads jobs,
  publishes jobs, matches against active resumes, invites candidates, and moves
  applications through the ATS-lite pipeline.
- Admin: monitors users, content, parse jobs, matching, notifications, and audit
  events. MVP admin is read-only unless requirements change.

## Target Outcomes

- Production API surface for auth, profiles, documents, jobs, resumes, matching,
  applications, invites, notifications, and admin monitoring.
- Upload-to-structured-data pipeline for CV/JD files.
- Shared marketplace visibility: only active resumes and published jobs enter
  public search and matching.
- Two-way matching remains explainable and deterministic for the same model
  versions and source data.
- Application records are created only by candidate apply or accepted recruiter
  invite; matching results alone never create applications.

## Non-Goals

- Tenant/company isolation.
- Billing and quotas.
- Full ATS interview scheduling, offer approval, onboarding, or CRM campaigns.
- Admin destructive moderation UI.
- AI-only automatic reject/advance decisions.
- Production quality claims without labeled evaluation data.

## Current Implementation Gap

The current backend has the production route surface and production schema
migration in place. Provider-level implementations for real object storage,
file extraction, LLM parsing, embedding model selection, email delivery, and
production frontend integration remain future work.

## Related Docs

- Product spec: `docs/REQUIREMENTS.md`
- Architecture: `docs/backend/HLD/10-architecture-overview.md`
- Ingestion: `docs/backend/HLD/20-ingestion-and-normalization.md`
- Data/storage: `docs/backend/HLD/30-data-and-storage.md`
- Matching/search: `docs/backend/HLD/40-matching-and-search-pipeline.md`
- API/runtime: `docs/backend/HLD/50-api-and-runtime-flows.md`
- Security/audit: `docs/backend/HLD/60-security-notifications-audit.md`
