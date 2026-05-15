# Backend

FastAPI backend for the JobConnect MVP recruiting marketplace.

## Module Layout

```text
backend/
  main.py                         # compatibility wrapper for older imports
  sitecustomize.py                # adds backend/src to Python path in local runs
  src/jobconnect/
    main.py                       # FastAPI app bootstrap
    app.py                        # app-level router registry and OpenAPI metadata
    core/
      database.py                 # PostgreSQL connection helper
    common/
      constants.py
      pagination.py
      responses.py
      utils.py
    integrations/
      pgvector/vector.py          # pgvector literal helper
    modules/
      api/router.py               # /api/* routers
      auth/
      users/
      organizations/
      jobs/
      resumes/
      documents/
      matching/                   # deterministic matching helpers
      applications/
      invites/
      notifications/
      admin/
      system/router.py            # health route
  db/
    migrations/
    apply_migrations.py
  tests/
```

This keeps the Python/FastAPI runtime but follows a NestJS-style module
boundary: app bootstrap, core infrastructure, shared common helpers,
integrations, and feature modules. The current `/api/*` router remains
centralized in `modules/api/router.py` until feature route files are split.

## Runtime

```bash
docker compose up -d postgres backend
```

The API is available at `http://localhost:8000`.

Apply schema migrations:

```bash
docker compose exec backend python db/apply_migrations.py
```

## Tests

```bash
docker compose exec backend python -m unittest discover -s tests
```

Legacy V2 prototype backend and frontend runtime code has been removed. Legacy
reference docs remain under `docs/`.
