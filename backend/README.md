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
      api/router.py               # compatibility import path for API runtime symbols
      api/_legacy_api_impl.py     # current legacy core implementation
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
integrations, and feature modules. The module folders now include
`router.py/schemas.py/service.py` scaffolds for API split work; runtime behavior
is still driven by the current legacy API core implementation.

Runtime data access uses `psycopg` + raw SQL in module services. SQLAlchemy ORM
is currently used only for seed/reset tooling under `backend/db/seeds/*`.

## Runtime

```bash
docker compose up -d postgres backend
```

The API is available at `http://localhost:8000`.

Apply schema migrations:

```bash
docker compose exec backend python db/apply_migrations.py
```

Apply demo seed data (SQLAlchemy ORM tooling, separate from migrations):

```bash
# install tooling dependency for the running backend container
docker compose exec backend pip install -r db/seeds/requirements-seed.txt

# seed profile
docker compose exec backend python -m db.seeds.cli seed --profile demo

# scoped reset + reseed (table changed + related records)
docker compose exec backend python -m db.seeds.cli reset --target jobs --with-related
docker compose exec backend python -m db.seeds.cli reseed --target jobs --profile demo --with-related

# dry-run without commit
docker compose exec backend python -m db.seeds.cli dry-run --mode seed --profile demo --target all
```

## Tests

```bash
docker compose exec backend python -m unittest discover -s tests
```

Legacy V2 prototype backend and frontend runtime code has been removed. Legacy
reference docs remain under `docs/`.
