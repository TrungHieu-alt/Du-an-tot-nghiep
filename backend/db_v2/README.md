# Matching V2 Prototype — Database (Run-Only)

Run-only PostgreSQL + pgvector workspace for the Matching V2 prototype.
Schema is the source of truth defined in `docs/REQUIREMENTS.md` §5.

## Layout

```
backend/db_v2/
├── migrations/001_init.sql   # 4 prototype tables + CHECK constraints + pgvector
├── seeds/001_seed.sql        # deterministic JD/CV rows + 384-dim embeddings
└── reset.py                  # reset + migrate + seed in one command
```

There are exactly **four** tables: `candidate_profiles_v2`, `job_posts_v2`,
`candidate_embeddings_v2`, `job_embeddings_v2`. There is **no** `match_results_v2`
table — the prototype is run-only.

## One-shot reset + migrate + seed

Start the database (docker compose service `postgres`, exposed on host port 5433):

```bash
docker compose up -d postgres
```

Then run the reset script from the repo root:

```bash
python backend/db_v2/reset.py
```

This drops the `public` schema, re-applies every SQL file in
`migrations/` (lexical order), then every SQL file in `seeds/` (lexical order).

## Connection settings

Defaults come from `.env.example`. Override via env vars:

| Var               | Default (host)   | Default (compose) |
|-------------------|------------------|-------------------|
| POSTGRES_HOST     | `localhost`      | `postgres`        |
| POSTGRES_PORT     | `5433`           | `5432`            |
| POSTGRES_USER     | `jobmatcher`     | `jobmatcher`      |
| POSTGRES_PASSWORD | `jobmatcher`     | `jobmatcher`      |
| POSTGRES_DB       | `jobmatcher_v2`  | `jobmatcher_v2`   |

## Sanity check

```bash
docker compose exec postgres psql -U jobmatcher -d jobmatcher_v2 -c "
  SELECT 'candidate_profiles_v2' AS table, COUNT(*) FROM candidate_profiles_v2
  UNION ALL SELECT 'job_posts_v2',            COUNT(*) FROM job_posts_v2
  UNION ALL SELECT 'candidate_embeddings_v2', COUNT(*) FROM candidate_embeddings_v2
  UNION ALL SELECT 'job_embeddings_v2',       COUNT(*) FROM job_embeddings_v2;"
```

Expected after seed: 5 rows in each table.
