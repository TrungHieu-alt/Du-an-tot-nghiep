# Frontend V2

React + Vite frontend for the Matching V2 prototype.

## Routes

| Path | Component | Notes |
|---|---|---|
| `/` | `pages/Home.tsx` | JobConnect landing homepage |
| `/login` | `pages/Login.tsx` | Password login against `/api/auth/login` |
| `/register` | `pages/Register.tsx` | Account registration against `/api/auth/register` |
| `/v2/search` | `pages/V2Search.tsx` | Catalog semantic search for jobs and CVs |
| `/v2/jobs/:id` | `pages/V2JobDetail.tsx` | Full job detail with matching CTA |
| `/v2/cvs/:id` | `pages/V2CvDetail.tsx` | Full CV detail with matching CTA |
| `/v2/matching` | `pages/V2Matching.tsx` | Run-only matching workbench; supports `?anchor=&id=` deep-links |

Unknown routes redirect to `/v2/search`.

## API

The clients in `src/api/v2.ts` and `src/services/authApi.ts` call the backend
through `lib/api.ts`.
`VITE_API_BASE_URL` may point either at the backend origin
(`http://localhost:8000`) or the API root (`http://localhost:8000/api`); the
config normalizes both forms.

`contexts/AuthContext.tsx` stores `jobconnect_access_token` and
`jobconnect_user` in `localStorage`, refreshes `/api/auth/me` when a token is
present, and exposes `login`, `register`, and `logout`.

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
