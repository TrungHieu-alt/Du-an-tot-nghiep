# JobConnect MVP

This repository now centers on the FastAPI backend for the JobConnect
recruiting marketplace MVP.

## Product Target

The target product is a shared-pool recruiting marketplace:

- candidates upload CVs, review parsed data, activate resumes, match against
  published jobs, apply to jobs, and respond to recruiter invites.
- recruiters create employer profiles, upload or create job descriptions,
  publish jobs, match against active resumes, invite candidates, and manage
  applications.
- admins monitor users, content, parse jobs, matching, notifications, and audit
  events.

Canonical product requirements live in `docs/REQUIREMENTS.md`.
Target backend architecture lives in `docs/backend/HLD/`.

## Current Runnable Baseline

- FastAPI backend under `backend/src/jobconnect`.
- API namespaces under `/api/*`.
- PostgreSQL + pgvector storage on host port `5433`.
- Schema migration at `backend/db/migrations/001_production_mvp.sql`.
- Legacy V2 prototype code has been removed from runtime. Legacy docs remain
  under `docs/backend/HLD/legacy/` and matching scenario docs for reference.

## Backend Layout

```text
backend/
  main.py
  src/jobconnect/
    main.py
    app.py
    core/
      config.py
      database.py
      exceptions.py
      logging.py
      security.py
    common/
      constants.py
      dependencies.py
      pagination.py
      responses.py
      utils.py
    integrations/
      pgvector/
    modules/
      api/
      auth/
      users/
      organizations/
      jobs/
      resumes/
      documents/
      matching/
      applications/
      invites/
      notifications/
      admin/
      system/
  db/
    migrations/
    apply_migrations.py
  tests/
```

The layout keeps FastAPI but organizes code around app, core, common,
integration, and feature-module boundaries similar to a NestJS project. The
current `/api/*` implementation is intentionally still centralized in
`modules/api/router.py`; the feature folders are the ownership targets for
future splits.

## Setup

Create `.env` from the example if present:

```bash
cp .env.example .env
```

Start the backend and database:

```bash
docker compose up -d postgres backend
```

Services:

- Backend API: `http://localhost:8000`
- PostgreSQL: `localhost:5433`

Apply schema migrations:

```bash
docker compose exec backend python db/apply_migrations.py
```

## Verification

Backend unit tests:

```bash
docker compose exec backend python -m unittest discover -s tests
```

OpenAPI and health:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/openapi.json
```

## Documentation

- Product spec: `docs/REQUIREMENTS.md`
- Production backend HLD: `docs/backend/HLD/`
- Production API LLD: `docs/backend/LLD/40-api-contract.md`
- MVP implementation roadmap: `docs/mvp-roadmap/README.md`
- Legacy prototype reference docs: `docs/backend/HLD/legacy/`

## Frontend Planning Rule

No frontend runtime is active right now. Files under `docs/frontend/` are
experimental prototype-adjacent notes and are not source of truth for the next
frontend implementation. Future screens must be redesigned later from
`docs/REQUIREMENTS.md`, backend HLD/LLD docs, and the current OpenAPI surface.
