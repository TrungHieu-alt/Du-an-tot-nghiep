# Frontend API Route Unification Plan

## Objective
Unify all frontend API usage to the backend canonical contract documented in:
- `docs/backend/LLD/api/backend-endpoint-schema-matrix.md`

This plan supersedes ad-hoc frontend route usage and is the execution/governance artifact for route migration.

## Backend Source-of-Truth Statement
- Backend routes are frozen for this initiative.
- No backend route additions or renames are allowed as part of this migration.
- Frontend must conform to existing backend `/api/*` routes only.
- `/api` must be included exactly once in request construction (either in base URL or route path, not both).
- Drift reference inventory:
  - `docs/frontend/frontend-api-comparison-with-backend.md`

## Route Mapping Table (Frontend Legacy -> Backend Canonical)

| Legacy frontend route | Backend canonical route | Status | Notes |
| --- | --- | --- | --- |
| `POST /auth/register` | `POST /api/users/register` | migrate | align request/response fields |
| `POST /auth/login` | `POST /api/users/login` | migrate | token keys: `access_token`, `token_type` |
| `GET /auth/profile` | `GET /api/users/{user_id}` | migrate | explicit `user_id` required |
| `PATCH /auth/change-password` | none | disable/remove | unsupported in backend contract |
| `DELETE /users/me` | `DELETE /api/users/{user_id}` | migrate | explicit `user_id` required |
| `PUT /users/me` | none | disable/remove | unsupported (only `/users/{user_id}/role` exists) |
| `PUT /users/me/career` | none | disable/remove | unsupported |
| `POST /users/me/avatar` | none | disable/remove | unsupported |
| `POST /cv` | `POST /api/cv/create/{user_id}` | migrate | explicit `user_id` required |
| `GET /cv` | `GET /api/cv/user/{user_id}` | migrate | replace list source with user-scoped route |
| `GET /cv/{id}` | `GET /api/cv/{cv_id}` | migrate | canonical id param |
| `PUT /cv/{id}` | `PUT /api/cv/{cv_id}` | migrate | canonical id param |
| `DELETE /cv/{id}` | `DELETE /api/cv/{cv_id}` | migrate | canonical id param |
| `GET /cv/user/me` | `GET /api/cv/user/{user_id}` | migrate | remove `me` alias |
| `PATCH /cv/{id}/rename` | `PUT /api/cv/{cv_id}` | migrate | use full update endpoint |
| `POST /cv/upload` | `POST /api/cv/upload/{user_id}` | migrate | multipart with explicit `user_id` |
| `POST /cvs` | `POST /api/cv/create/{user_id}` | migrate | remove plural namespace |
| `PUT /cvs/{id}` | `PUT /api/cv/{cv_id}` | migrate | remove plural namespace |
| `DELETE /cvs/{id}` | `DELETE /api/cv/{cv_id}` | migrate | remove plural namespace |
| `GET /jobs` | `GET /api/jobs` | migrate | canonical listing route |
| `POST /jobs` | `POST /api/jobs/create/{recruiter_id}` | migrate | explicit `recruiter_id` required |
| `GET /jobs/{id}` | `GET /api/jobs/{job_id}` | migrate | canonical id param |
| `PUT /jobs/{id}` | `PUT /api/jobs/{job_id}` | migrate | canonical id param |
| `DELETE /jobs/{id}` | `DELETE /api/jobs/{job_id}` | migrate | canonical id param |
| `GET /jobs/user/me` | `GET /api/jobs/recruiter/{recruiter_id}` | migrate | remove `me` alias |
| `PATCH /jobs/{id}/rename` | `PUT /api/jobs/{job_id}` | migrate | use full update endpoint |
| `PUT /requirements/{id}` | `PUT /api/jobs/{job_id}` | migrate | remove requirements namespace |
| `DELETE /requirements/{id}` | `DELETE /api/jobs/{job_id}` | migrate | remove requirements namespace |
| `POST /requirements` | `POST /api/jobs/create/{recruiter_id}` | migrate | remove requirements namespace |
| `GET /rag/match-job-cv-chunks/{jobId}/{cvId}` | `GET /api/jobs/match/{job_id}/cvs/{cv_id}` | migrate | pair match endpoint |
| `GET /rag/match-all-jobs-for-cv-doc/{cvId}` | `GET /api/cv/match/{cv_id}/jobs` | migrate | CV -> jobs matching |
| `GET /rag/match-all-cvs-for-job-doc/{reqId}` | `GET /api/jobs/match/{job_id}/cvs` | migrate | job -> CVs matching |
| `POST /rag/ask` | none | disable/remove | unsupported |
| `POST /parse-bdf` | none | disable/remove | unsupported |

## Phased Migration Checklist

### Phase A: Auth/User
- [ ] Set frontend auth routes to `/api/users/register` and `/api/users/login`.
- [ ] Store/use backend user identity fields (`user_id`, `role`, timestamps).
- [ ] Replace profile fetch path with `GET /api/users/{user_id}`.
- [ ] Replace account delete path with `DELETE /api/users/{user_id}`.
- [ ] Disable unsupported auth/account operations (`/auth/change-password`, `/users/me` update variants).
- [ ] Record evidence of completed replacements.

### Phase B: CV/Candidate
- [ ] Replace CV create route with `POST /api/cv/create/{user_id}`.
- [ ] Replace CV list/user-me variants with:
  - `GET /api/cv/user/{user_id}`
  - `GET /api/cv/main/user/{user_id}` (when main CV needed)
- [ ] Keep CV CRUD on canonical `/api/cv/{cv_id}` routes.
- [ ] Replace rename patch usage with full `PUT /api/cv/{cv_id}` updates.
- [ ] Replace CV upload path with `POST /api/cv/upload/{user_id}`.
- [ ] Remove `/cvs/*` legacy calls.
- [ ] Record evidence of completed replacements.

### Phase C: Jobs/Recruiter
- [ ] Replace job create route with `POST /api/jobs/create/{recruiter_id}`.
- [ ] Replace recruiter-me list with `GET /api/jobs/recruiter/{recruiter_id}`.
- [ ] Keep job CRUD on canonical `/api/jobs/{job_id}` routes.
- [ ] Replace rename patch usage with full `PUT /api/jobs/{job_id}` updates.
- [ ] Remove `/requirements/*` namespace usage.
- [ ] Record evidence of completed replacements.

### Phase D: Matching
- [ ] Replace `rag/*` read endpoints with canonical matching endpoints:
  - `GET /api/cv/match/{cv_id}/jobs`
  - `GET /api/cv/match/{cv_id}/jobs/{job_id}`
  - `GET /api/jobs/match/{job_id}/cvs`
  - `GET /api/jobs/match/{job_id}/cvs/{cv_id}`
- [ ] Use `/api/matching/*` routes only where persisted run/list/delete workflows are needed.
- [ ] Record evidence of completed replacements.

### Phase E: Unsupported Frontend-Only Routes
- [ ] Remove/disable unsupported calls:
  - `/auth/profile` (after replaced by `/users/{user_id}`)
  - `/auth/change-password`
  - `/users/me` update/career/avatar variants
  - `/requirements/*`
  - `/parse-bdf`
  - `/rag/ask`
- [ ] Ensure UI fallbacks communicate unavailability where needed.
- [ ] Record evidence of completed removals/disablements.

## Validation Checklist
- [ ] Contract check before each phase:
  - verify target routes exist in backend `/openapi.json`.
- [ ] Per-phase smoke checks:
  - one success request for each migrated route family.
  - one error/validation request confirming FastAPI error body (`detail`).
- [ ] End-to-end UI checks after each phase:
  - register/login
  - CV create/edit/delete and owner list
  - job create/edit/delete and recruiter list
  - match retrieval views (job->CV and CV->job)
- [ ] Regression gate:
  - no remaining frontend calls to `/auth/*`, `/rag/*`, `/requirements/*`, `/cvs/*`, `/users/me*`.
- [ ] Documentation parity:
  - this file remains consistent with `docs/frontend/frontend-api-comparison-with-backend.md`.

## Error/Envelope Handling Policy
- FastAPI-first error parsing for non-application routes:
  - expect `{"detail": "..."}`.
- Preserve application envelope handling for `/api/applications/*`:
  - `{"success": boolean, "data": ..., "message"?: string}`.

## Rollback Notes
- Rollback unit is phase-based, not big-bang.
- If a phase fails smoke checks:
  - revert only that phase’s frontend route changes.
  - restore previous stable frontend behavior for impacted screens.
  - keep earlier completed phases intact.
- Do not rollback by adding backend compatibility routes during this initiative.
- Any rollback must update this plan with:
  - rollback date/time,
  - impacted route families,
  - reason,
  - re-entry criteria.
