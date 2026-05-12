# Frontend V2

React + Vite frontend for the Matching V2 prototype.

## Routes

| Path | Component | Notes |
|---|---|---|
| `/` | redirect | Redirects to `/v2/search` |
| `/v2/search` | `pages/V2Search.tsx` | Catalog semantic search for jobs and CVs |
| `/v2/jobs/:id` | `pages/V2JobDetail.tsx` | Full job detail with matching CTA |
| `/v2/cvs/:id` | `pages/V2CvDetail.tsx` | Full CV detail with matching CTA |
| `/v2/matching` | `pages/V2Matching.tsx` | Run-only matching workbench; supports `?anchor=&id=` deep-links |

Unknown routes redirect to `/v2/search`.

## API

The client in `src/api/v2.ts` calls the backend through `lib/api.ts`.
`VITE_API_BASE_URL` may point either at the backend origin
(`http://localhost:8000`) or the API root (`http://localhost:8000/api`); the
config normalizes both forms.

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
