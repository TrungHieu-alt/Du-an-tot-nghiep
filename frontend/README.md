# Frontend V2

React + Vite frontend for the Matching V2 prototype.

## Routes

| Path | Component | Notes |
|---|---|---|
| `/` | `pages/Home.tsx` | JobConnect landing homepage |
| `/login` | `pages/Login.tsx` | Password login against `/api/auth/login` plus Google login |
| `/register` | `pages/Register.tsx` | Account registration against `/api/auth/register`; no role selection |
| `/jobs/search` | `pages/V2Search.tsx` | Normal Find Job search via `/api/job/search` |
| `/cvs/search` | `pages/V2Search.tsx` | Normal Find CV search via `/api/cv/search` |
| `/job/my` | `pages/MyJobs.tsx` | Owner-managed normal Job CRUD |
| `/applications` | `pages/MyApplications.tsx` | Candidate submitted normal applications |
| `/cv/my` | `pages/MyCvs.tsx` | Owner-managed normal CV CRUD and PDF upload |
| `/job/:id` | `pages/NormalJobDetail.tsx` | Normal public/owner Job detail with apply/applicants flow |
| `/cv/:id` | `pages/NormalCvDetail.tsx` | Owner CV detail |
| `/v2/search` | `pages/V2Search.tsx` | Compatibility route for the shared normal search UI |
| `/v2/jobs/:id` | `pages/V2JobDetail.tsx` | Full job detail with matching CTA |
| `/v2/cvs/:id` | `pages/V2CvDetail.tsx` | Full CV detail with matching CTA |
| `/v2/matching` | `pages/V2Matching.tsx` | Run-only matching workbench; supports `?anchor=&id=` deep-links |

Unknown routes redirect to `/jobs/search`.

## API

The clients in `src/api/normal.ts`, `src/api/v2.ts`, and
`src/services/authApi.ts` call the backend through `lib/api.ts`. Normal search
uses `GET /api/job/search` and `GET /api/cv/search`; compatibility aliases
`GET /api/jobs`, `GET /api/cvs`, and `GET /api/candidates` remain available.
Matching V2 and catalog semantic endpoints remain available for matching and
detail workflows.

Normal applications use `POST /api/applications`, `GET /api/applications/me`,
`GET /api/job/{job_id}/applications`, and
`PATCH /api/applications/{application_id}/status`. These endpoints link normal
Jobs and CVs only; they do not return score, recommendation, or V2 matching
fields.

The normal CV search page groups candidate filters around the normalized
multi-industry CV schema: industry, occupation group, career level, experience
range, employment type, skills, tools, domain knowledge, education, languages,
location, status, tags, sort, and pagination. Skill aliases are normalized
before query serialization, and normal search does not send or render matching
score/recommendation fields.

## Normal Create/Edit Forms

`pages/MyCvs.tsx` and `pages/MyJobs.tsx` use the shared normal form wizards in
`components/normal/` for create and inline edit. These forms save normalized
multi-industry CV/Job fields through the existing normal CRUD APIs. Enum-like
fields are selected from `src/reference/normalEnums.ts` and are submitted as
normalized values such as `fulltime`, `intermediate`, `bachelor`, or `unknown`.

The normal create/edit forms do not calculate or return matching output. Score,
match level, recommendation, hard-filter, and V2 matching behavior remains in
the separate V2 pages and APIs.

`VITE_API_BASE_URL` may point either at the backend origin
(`http://localhost:8000`) or the API root (`http://localhost:8000/api`); the
config normalizes both forms.
Set `VITE_GOOGLE_CLIENT_ID` to enable the Google login button. Password
registration/login works without this variable.

`contexts/AuthContext.tsx` stores `jobconnect_access_token` and
`jobconnect_user` in `localStorage`, refreshes `/api/auth/me` when a token is
present, and exposes `login`, `googleLogin`, `register`, and `logout`.

## Local Commands

```bash
npm install
npm run dev
npm run test:run
npm run build
```

Docker Compose is the default runtime:

```bash
docker compose up -d frontend
```
