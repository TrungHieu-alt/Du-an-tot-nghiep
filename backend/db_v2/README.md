# Matching V2 Prototype — Database (Run-Only)

Run-only PostgreSQL + pgvector workspace for the Matching V2 prototype.
Schema is the source of truth defined in `docs/REQUIREMENTS.md` §5, with an
additive `users` table for the auth surface.

## Layout

```
backend/db_v2/
├── migrations/001_init.sql   # 4 prototype matching tables + CHECK constraints + pgvector
├── migrations/002_auth_users.sql # auth users table
├── seeds/001_seed.sql        # deterministic JD/CV rows + 384-dim embeddings
├── seeds/002_extra_test_data.sql
├── seeds/003_broad_ranking_test_data.sql
├── scenarios/                # Slice 6B compact scenario JSON + schema
│   └── matching_v2_slice_6c_rank_expectations.json
├── scenario_embeddings.py    # deterministic local 384-dim embedding generator
├── seed_scenario.py          # non-additive scenario seed
├── validate_scenario_dataset.py
└── reset.py                  # reset + migrate + seed in one command
```

Matching data still lives in exactly **four** tables: `candidate_profiles_v2`,
`job_posts_v2`, `candidate_embeddings_v2`, `job_embeddings_v2`. Auth data lives
separately in `users`. There is **no** `match_results_v2` table — the matching
prototype is run-only.

## Start the database

Start the database (docker compose service `postgres`, exposed on host port 5433):

```bash
docker compose up -d postgres
```

## Reset, migrate, and seed

Run the reset script from the repo root after `postgres` is healthy:

```bash
python backend/db_v2/reset.py
```

This drops the `public` schema, re-applies every SQL file in `migrations/`
(lexical order), then every SQL file in `seeds/` (lexical order). The default
`base` profile preserves the historical SQL seed path and leaves `users` empty.

If you prefer to run the command inside the backend container, start the backend
service first and use the compose-network PostgreSQL host:

```bash
docker compose up -d postgres backend
docker compose exec backend python db_v2/reset.py
```

## Slice 6B scenario reset and seed

Use the `scenario` profile for the compact Matching V2 scenario dataset:

```bash
docker compose up -d postgres backend
docker compose exec backend python db_v2/reset.py --profile scenario
docker compose exec backend python db_v2/validate_scenario_dataset.py --db
```

The scenario profile is non-additive. It drops and recreates the schema, applies
the V2 migration, validates `scenarios/matching_v2_slice_6b.json`, generates
deterministic local embeddings, and inserts only:

| Table | Expected count |
|---|---:|
| `job_posts_v2` | 6 |
| `candidate_profiles_v2` | 36 |
| `job_embeddings_v2` | 6 |
| `candidate_embeddings_v2` | 35 |

CV `3018` intentionally has no row in `candidate_embeddings_v2` to exercise the
missing embedding-row behavior. Matching still returns the hard-filter pass with
semantic components defaulted to `0` and missing-embedding reasoning.

To validate the scenario JSON and deterministic embedding workflow without a
database connection:

```bash
python backend/db_v2/validate_scenario_dataset.py
```

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

Expected after the default SQL seed path: use the current SQL files under
`seeds/`.

| Table | Expected count after default SQL seed |
|---|---:|
| `job_posts_v2` | 10 |
| `candidate_profiles_v2` | 34 |
| `job_embeddings_v2` | 10 |
| `candidate_embeddings_v2` | 33 |
| `users` | 0 |

The default SQL seed path is the Slice 6C broad ranking verification dataset.
It contains 10 representative JD anchors (`2001..2010`) and deterministic
strong/good/noisy candidate rows for ranking checks. CV `1010` intentionally has
no embedding row so min_score exclusion can be tested separately from hard
filters.

Expected after the Slice 6B scenario profile: 6 JD, 36 CV, 6 job embedding
rows, and 35 candidate embedding rows.

## Read-only verification (DoD guard)

Run full slice-1 checks without mutating data:

```bash
python backend/db_v2/verify.py
```

## Run the app

Start the API with Docker Compose:

```bash
docker compose up -d postgres backend
```

The backend listens on `http://localhost:8000`. OpenAPI is available at:

```bash
curl "http://localhost:8000/openapi.json"
```

## Live DB integration smoke

Use this as the Slice 6C live-stack evidence path. It starts `postgres` and
`backend`, resets and seeds PostgreSQL from scratch through the default broad
SQL seed path, waits for OpenAPI, then calls both run-only
endpoints against the real backend:

```bash
bash scripts/smoke_match_v2_live.sh
```

Assertions covered:

- JD -> CV: `POST /api/v2/prototype/matching/job/2006/run` returns `200`.
- CV -> JD: `POST /api/v2/prototype/matching/cv/1006/run` returns `200`.
- Response includes `rank`, score components, `reasoning`, and runtime metrics.
- Deterministic top match for JD `2006` is CV `1006`.
- Deterministic top match for CV `1006` is JD `2006`.
- OpenAPI V2 prototype namespace contains exactly:
  `/api/v2/prototype/matching/job/{job_id}/run` and
  `/api/v2/prototype/matching/cv/{cv_id}/run`.

Test labels:

- Router contract test: FastAPI `TestClient` with mocked DB/matching.
- Live DB integration smoke: `bash scripts/smoke_match_v2_live.sh`.
- Manual smoke: the `curl` commands below.

For local host-only debugging, run from `backend/` after installing backend
dependencies and setting PostgreSQL env vars:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Prototype run endpoint examples

JD -> CV:

```bash
curl -X POST "http://localhost:8000/api/v2/prototype/matching/job/2006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}'
```

CV -> JD:

```bash
curl -X POST "http://localhost:8000/api/v2/prototype/matching/cv/1006/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}'
```

`top_k` must be between `1` and `10`. `min_score` must be between `0.0` and
`1.0`. Both endpoints accept an omitted body and use defaults:
`{"top_k": 10, "min_score": 0.7}`.

## Example response shape

```json
{
  "anchor_type": "job",
  "anchor_id": 2006,
  "total_candidates": 34,
  "total_after_filter": 4,
  "total_returned": 4,
  "runtime_ms_total": 4.31,
  "runtime_ms_filter": 0.02,
  "runtime_ms_scoring": 0.18,
  "runtime_ms_sort": 0.01,
  "matches": [
    {
      "rank": 1,
      "cv_id": 1006,
      "job_id": 2006,
      "final_score": 1.0,
      "title_score": 1.0,
      "skills_score": 1.0,
      "req_exp_score": 1.0,
      "req_summary_score": 1.0,
      "reasoning": "Strongest signal: 'title' (score 1.000). Exact skill matches (4): aws, docker, kubernetes, terraform."
    }
  ]
}
```

Runtime values can vary by machine. For unchanged data, ranks, IDs, scores, and
reasoning are expected to stay deterministic.

## Scope limitations

- Run-only prototype.
- No persistence of matching results.
- No `match_results_v2` table.
- No GET/DELETE match result APIs.
- No benchmark or labeled quality metrics.
- No ANN tuning requirement (`hnsw`/`ivfflat` are out of scope).
- No LLM scoring or LLM reasoning.
- Auth exists as an additive app surface; no dedicated auth guard is applied to
  Matching V2 endpoints yet.
