# Frontend API Contract Comparison Against Backend API Matrix

## Purpose
This document defines a frontend-facing API contract view and compares it with the current backend source-of-truth document:
- Backend reference: `docs/backend/LLD/api/backend-endpoint-schema-matrix.md`

Primary goal: make frontend integration decisions explicit by classifying each currently used frontend route as:
- `MATCHED`: backend route exists with compatible semantics.
- `PARTIAL`: backend route exists but path params/body/response shape differ.
- `MISSING`: no backend route exists for the frontend call.

## Source Inputs
- Backend contract and runtime docs:
  - `docs/backend/LLD/api/backend-endpoint-schema-matrix.md`
  - `docs/backend/HLD/40-api-and-runtime-flows.md`
  - `backend/main.py`
- Frontend API usage:
  - `frontend/lib/api.ts`
  - `frontend/src/api/http.ts`
  - `frontend/src/api/auth.ts`
  - UI/API callsites under `frontend/pages`, `frontend/components`, `frontend/utils`

## Global Alignment Summary

### Base URL and Prefix
- Backend mounts all routers under `/api`.
- Frontend clients currently use base URL `http://localhost:3000` and call paths like `/cv`, `/jobs`, `/auth/*`.
- Required alignment for direct backend integration:
  - Backend dev URL is typically `http://localhost:8000`.
  - Frontend request paths should include `/api` prefix (either in base URL or in per-call paths).

### Auth/Identity Model
- Backend exposes auth as `/api/users/register` and `/api/users/login`.
- Frontend currently calls `/auth/register`, `/auth/login`, and `/auth/profile`.
- Current status: `PARTIAL` for register/login naming mismatch; `MISSING` for `/auth/profile`.

### Response Shape Consistency
- Backend mostly returns direct models and standard FastAPI error shape `{ "detail": "..." }`.
- Application endpoints use envelope shape `{ success, data, message? }`.
- Frontend helper `src/api/http.ts` currently assumes Nest-style error shape (`message`, `statusCode`), which is not backend-native.

## Endpoint Comparison Matrix

### 1) Authentication and User

| Frontend call | Observed use | Backend counterpart | Status | Notes |
| --- | --- | --- | --- | --- |
| `POST /auth/register` | `src/api/auth.ts` | `POST /api/users/register` | PARTIAL | Rename path and align request/response keys. |
| `POST /auth/login` | `pages/Login.tsx` | `POST /api/users/login` | PARTIAL | Same logic, different route namespace. |
| `GET /auth/profile` | `pages/ProfilePage.tsx` | none | MISSING | Use `GET /api/users/{user_id}` after storing `user_id`. |
| `PATCH /auth/change-password` | `components/profile/AccountSettings.tsx` | none | MISSING | No backend endpoint exists. |
| `DELETE /users/me` | `components/profile/AccountSettings.tsx` | `DELETE /api/users/{user_id}` | PARTIAL | Requires explicit `user_id` path param. |
| `PUT /users/me` | `components/profile/ProfileInfoForm.tsx` | none | MISSING | Closest backend update is `PUT /api/users/{user_id}/role` only. |
| `PUT /users/me/career` | `components/profile/CareerInfoForm.tsx` | none | MISSING | No backend user-career endpoint. |
| `POST /users/me/avatar` | `components/profile/AvatarUploader.tsx` | none | MISSING | No backend avatar upload endpoint. |

### 2) Candidate Profile and CV

| Frontend call | Observed use | Backend counterpart | Status | Notes |
| --- | --- | --- | --- | --- |
| `POST /cv` | multiple forms/modals | `POST /api/cv/create/{user_id}` | PARTIAL | Backend requires path `user_id`; schema differs in several UI flows. |
| `GET /cv` | `CvSelectorModal`, `mockApi` | none | MISSING | Backend has `GET /api/cv/user/{user_id}` and `GET /api/cv/main/user/{user_id}` only. |
| `GET /cv/{id}` | detail/edit | `GET /api/cv/{cv_id}` | PARTIAL | Route is close; add `/api` prefix and ensure numeric/ID contract alignment. |
| `PUT /cv/{id}` | detail/edit | `PUT /api/cv/{cv_id}` | PARTIAL | Route exists with prefix + schema alignment needed. |
| `DELETE /cv/{id}` | selector/detail | `DELETE /api/cv/{cv_id}` | PARTIAL | Route exists with prefix + delete response shape alignment. |
| `GET /cv/user/me` | jobs/detail/modals | `GET /api/cv/user/{user_id}` | PARTIAL | Replace `me` alias with explicit user id or add backend alias endpoint. |
| `PATCH /cv/{id}/rename` | `CvSelectorModal` | none | MISSING | No rename endpoint in backend; use `PUT /api/cv/{cv_id}`. |
| `POST /cv/upload` | `BdfUploadParser` | `POST /api/cv/upload/{user_id}` | PARTIAL | Backend requires path `user_id` and multipart contract. |
| `POST /cvs` and `/cvs/{id}` | `utils/mockApi.ts` | none | MISSING | Plural route family not present in backend. |

### 3) Recruiter and Job

| Frontend call | Observed use | Backend counterpart | Status | Notes |
| --- | --- | --- | --- | --- |
| `GET /jobs` | search/list | `GET /api/jobs` | PARTIAL | Route exists with prefix; query parameter contracts may differ. |
| `POST /jobs` | create/profile form | `POST /api/jobs/create/{recruiter_id}` | PARTIAL | Backend requires `recruiter_id` in path. |
| `GET /jobs/{id}` | detail | `GET /api/jobs/{job_id}` | PARTIAL | Route exists with prefix + ID type alignment needed. |
| `PUT /jobs/{id}` | edit | `PUT /api/jobs/{job_id}` | PARTIAL | Route exists with prefix + request body alignment needed. |
| `DELETE /jobs/{id}` | delete | `DELETE /api/jobs/{job_id}` | PARTIAL | Route exists with prefix. |
| `GET /jobs/user/me` | requirements/detail | `GET /api/jobs/recruiter/{recruiter_id}` | PARTIAL | Replace `me` alias with recruiter id or add alias endpoint. |
| `PATCH /jobs/{id}/rename` | `RequirementSelectorModal` | none | MISSING | No dedicated rename endpoint; use `PUT /api/jobs/{job_id}`. |
| `POST /requirements`, `PUT /requirements/{id}`, `DELETE /requirements/{id}` | `utils/mockApi.ts` | none | MISSING | Backend uses `jobs` domain, not `requirements`. |

### 4) Matching and AI/RAG

| Frontend call | Observed use | Backend counterpart | Status | Notes |
| --- | --- | --- | --- | --- |
| `GET /rag/match-job-cv-chunks/{jobId}/{cvId}` | candidate/job detail | closest: `GET /api/jobs/match/{job_id}/cvs/{cv_id}` or `GET /api/cv/match/{cv_id}/jobs/{job_id}` | PARTIAL | Backend has pair-match endpoints but not `rag/*` path. |
| `GET /rag/match-all-jobs-for-cv-doc/{cvId}` | `utils/mockApi.ts` | closest: `GET /api/cv/match/{cv_id}/jobs` | PARTIAL | Switch to `/api/cv/match/{cv_id}/jobs`. |
| `GET /rag/match-all-cvs-for-job-doc/{reqId}` | `utils/mockApi.ts` | closest: `GET /api/jobs/match/{job_id}/cvs` | PARTIAL | Switch to `/api/jobs/match/{job_id}/cvs`. |
| `POST /rag/ask` | `utils/mockApi.ts` | none | MISSING | No chat/ask endpoint in backend matrix. |
| `POST /parse-bdf` | `utils/parseBdf.ts` | none | MISSING | No parse-bdf endpoint in backend matrix. |

### 5) Applications

| Frontend call | Backend counterpart | Status | Notes |
| --- | --- | --- | --- |
| no active direct calls detected | `/api/applications/*` family exists | GAP | Frontend currently does not wire application create/query/status endpoints. |

## Required Frontend Contract (Recommended Target)
Use backend contracts directly (preferred for immediate integration):

1. Base URL
- `VITE_API_BASE_URL=http://localhost:8000/api`
- Update frontend paths from `/cv` to `/cv/...` etc under this base.

2. Auth
- `POST /users/register`
- `POST /users/login`
- Store `user_id` from login/register response for subsequent user-scoped routes.

3. CV and Jobs
- Replace `/cv` create with `/cv/create/{user_id}`.
- Replace `/jobs` create with `/jobs/create/{recruiter_id}`.
- Replace `/cv/user/me` and `/jobs/user/me` with explicit id routes.
- Replace rename patch endpoints with full `PUT` updates.

4. Matching
- Replace `rag/*` endpoints with existing matching routes:
  - `/cv/match/{cv_id}/jobs`
  - `/cv/match/{cv_id}/jobs/{job_id}`
  - `/jobs/match/{job_id}/cvs`
  - `/jobs/match/{job_id}/cvs/{cv_id}`
  - `/matching/*` run/list/delete as needed for persisted match workflows.

## Highest-Risk Drift Items
1. Path namespace mismatch (`/auth`, `/rag`, `/requirements`, `/cvs`) vs backend canonical routes.
2. Missing `/api` prefix and backend port mismatch.
3. `me` alias assumption in frontend while backend requires explicit ids.
4. Error-shape parser mismatch in frontend HTTP helper.
5. Frontend profile/account endpoints that do not exist in backend contract.

## Integration Decision Log
- Option A: change backend to match current frontend paths.
- Option B: change frontend calls to match current backend matrix.
- Chosen recommendation: Option B.
- Reason: backend contract is already documented and is the current implemented system baseline.
- Risk tradeoff: frontend changes are broader in count but lower risk than introducing new backend compatibility routes without clear ownership and tests.

## Comparison Status Snapshot
- `MATCHED`: 0 direct fully aligned paths when considering current frontend call patterns and backend prefix requirements.
- `PARTIAL`: existing capabilities can cover many calls with route and payload refactors.
- `MISSING`: several frontend features require either backend endpoint additions or temporary feature disablement.
