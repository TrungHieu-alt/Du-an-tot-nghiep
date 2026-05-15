# MVP Testing Strategy

This document defines the minimum testing expectation for MVP implementation
slices.

The project has a two-week implementation target, so the testing strategy must
be strict enough to prevent regressions but small enough to keep delivery
moving.

## Testing Principles

- Every code slice must add or update tests for the behavior it changes.
- Unit tests cover local business rules and edge cases.
- Integration tests cover completed large user flows.
- Smoke-contract checks prove the running API and OpenAPI surface still work.
- Acceptance evidence connects implementation back to `docs/REQUIREMENTS.md`.
- Do not mark a code slice `done` with only manual reasoning.
- Do not add broad, slow tests when a focused test would catch the regression.

## Minimum Test Requirement Per Code Slice

For every backend code slice:

- Add or update at least one unit test for the main business rule changed.
- Add a negative/error test when the slice changes validation, authorization,
  lifecycle state, or failure behavior.
- Add or update endpoint smoke checks when the slice changes API behavior.
- Verify OpenAPI when request/response schemas, route paths, status codes, or
  error contracts change.
- Update `docs/mvp-roadmap/requirements-acceptance-matrix.md` when product
  behavior is implemented or changed.

For every frontend code slice:

- Add or update at least one component/unit test for the main UI behavior when a
  frontend test framework exists.
- Add route/API-client tests for auth, role guards, or error handling changes.
- Add a browser smoke checklist for user-visible flow changes.
- If the frontend test framework does not exist yet, the slice must create the
  framework or explicitly record the missing test capability as a blocker or
  follow-up.

For docs-only slices:

- Runtime tests are not required.
- Provide read-only verification evidence: changed files, inspected sources,
  checked links/paths, and API/OpenAPI impact.

## Backend Unit Test Targets

Use focused unit tests for:

- Auth token creation, expiry, and validation.
- Role and ownership helper logic.
- Partial update semantics.
- File validation rules: MIME, size, document type.
- Text preprocessing and skill normalization.
- Parser output validation and enum mapping.
- Embedding version and missing embedding behavior.
- Matching hard filters, score formula, tie-breaks, and reasoning notes.
- Application and invite transition rules.
- Notification and audit event creation helpers.

Expected location:

- `backend/tests/`

Existing examples:

- `backend/tests/test_app_surface.py`
- `backend/tests/test_matching_helpers.py`

## Backend Integration Test Gates

Add integration tests when a large flow is completed, not for every tiny code
change.

Minimum large-flow integration gates:

1. Candidate CV flow
   - Register/login candidate.
   - Create/update profile.
   - Upload or create resume.
   - Parse or simulate parse completion.
   - Activate resume.
   - Search/match jobs.
   - Apply to a published job.

2. Recruiter JD flow
   - Register/login recruiter.
   - Create organization/profile.
   - Upload or create job.
   - Parse or simulate parse completion.
   - Publish job.
   - Search/match active resumes.
   - Send invite.
   - Manage application status.

3. Invite acceptance flow
   - Recruiter invites candidate.
   - Candidate accepts invite.
   - Application is created once.
   - Duplicate acceptance returns existing application or fails according to
     the API contract.

4. Admin monitoring flow
   - Admin lists users, documents, parse jobs, applications, invites,
     notifications, and audit logs.
   - Non-admin access is denied.

5. Parse failure flow
   - Upload or enqueue a bad document.
   - Parse job fails.
   - Original file remains.
   - Notification and audit event are created.

Integration tests may use direct test clients, seeded database fixtures, or
Docker-backed smoke scripts. The chosen approach must be recorded in the slice
handoff.

## Smoke-Contract Gate

Backend code slices that touch runtime behavior should run:

```bash
docker compose up -d postgres backend
docker compose exec backend python db/apply_migrations.py
docker compose exec backend python -m unittest discover -s tests
curl http://localhost:8000/api/health
curl http://localhost:8000/openapi.json
```

If Docker is unavailable, record the reason and the closest safe substitute.

For API slices, also run at least:

- one success request for the touched endpoint or flow,
- one validation, authorization, or lifecycle error request,
- one OpenAPI schema availability check.

## Two-Week Delivery Guidance

Do not try to build a full enterprise test suite during the MVP sprint.

Recommended test allocation:

- Unit tests for every slice: mandatory.
- Integration tests after each completed large flow: mandatory.
- Browser/manual smoke for frontend workflows: mandatory until frontend test
  coverage matures.
- Performance/load tests: defer unless a concrete blocker appears.
- Extensive provider mocking matrix: defer; keep adapter tests focused.

The highest-value integration tests for the two-week target are:

1. Candidate apply flow.
2. Recruiter invite and application management flow.
3. Matching job-to-resume and resume-to-job flow.
4. Parse success and parse failure flow.
5. Admin read-only monitoring access.

## Done Means Tested

A code slice cannot be marked `done` unless:

- Unit tests for changed business rules pass.
- Required integration or smoke checks pass.
- Requirement acceptance evidence is updated when product behavior changes.
- OpenAPI impact is recorded.
- `docs/mvp-roadmap/progress.md` records actual verification evidence.
- Known test gaps are visible as follow-up actions.
