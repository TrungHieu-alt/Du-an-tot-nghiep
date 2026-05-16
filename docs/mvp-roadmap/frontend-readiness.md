# Frontend Readiness And Design Source

The repository currently has no active frontend runtime. Files under
`docs/frontend/` include archived references and active Slice 13 screen specs.

This document defines what must be true before frontend implementation begins.

## Frontend Source-Of-Truth Rule

Frontend implementation must be driven by:

1. `docs/REQUIREMENTS.md`
2. `docs/backend/LLD/40-api-contract.md`
3. current OpenAPI output from `/openapi.json`
4. the Slice 13 frontend design brief in `docs/frontend/screen/*`
5. selected external product references recorded by the team

Do not implement the next frontend directly from archived prototype screens.
Archived files can inspire flows, but they are not authoritative.
Use `docs/frontend/screen/*` as the active source for current screen direction.
Use `docs/frontend/README.md` as the frontend-docs index before opening any
screen file directly.

Current active screen files:

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
- `docs/frontend/screen/application-management.md`
- `docs/frontend/screen/admin-monitoring.md`
- `docs/frontend/screen/shared-states.md`
- `docs/frontend/screen-to-api-state-matrix.md`

## Slice 13 Design Brief Must Include

- Selected external references and what is borrowed from each.
- Target frontend stack and runtime root.
- Screen inventory:
  - Auth
  - Workspace Home
  - Jobs Library
  - CVs Library
  - Upload + Parse Review (dedicated page)
  - Job Detail
  - CV Detail
  - Matching Workspace
  - Applications and Invites
  - Notifications
  - Admin Monitoring
- Explicit rule: hard-filter fields in parse review must be user-confirmed
  before upload-based entities can enter active/publish-ready usage.
- Screen-to-API map.
- Shared Vietnamese UI copy contract for empty, blocked, validation, session,
  authorization, and lifecycle states.
- Data states for each screen:
  - loading
  - empty
  - error
  - forbidden/session expired
  - success
- What is intentionally simple for MVP visual style.
- What visual polish is deferred.

## Frontend Implementation Gate

Do not start Slice 14 or Slice 15 until:

- Slice 13 is marked `done` or explicitly accepted as partial.
- The API contracts for auth, `/api/me`, jobs, resumes, documents, matching,
  applications, invites, notifications, and admin monitoring are stable enough
  for frontend wiring.
- Any temporary mocks are documented with removal criteria.
- `docs/mvp-roadmap/progress.md` names the frontend stack and startup command.

## Two-Week Frontend Guidance

For the two-week target, prioritize:

1. Correct data display.
2. Clear role-aware navigation.
3. Exact search and semantic search as separate modes.
4. Matching result readability.
5. Complete candidate and recruiter primary flows.

Defer:

- advanced visual polish,
- saved searches/history,
- compare view,
- analytics dashboards,
- collaboration features,
- marketing/landing pages.

## Frontend Acceptance Evidence

Frontend core workflow slices require:

- browser smoke checklist for candidate flow,
- browser smoke checklist for recruiter flow,
- browser smoke checklist for admin monitoring,
- API error/session-expired behavior evidence,
- note of any backend contract issue found by the UI.
