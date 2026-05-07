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

This drops the `public` schema, re-applies every SQL file in
`migrations/` (lexical order), then every SQL file in `seeds/` (lexical order).
The seed is deterministic and currently inserts 5 CV rows, 5 JD rows, and their
384-dimensional pgvector embeddings.

If you prefer to run the command inside the backend container, start the backend
service first and use the compose-network PostgreSQL host:

```bash
docker compose up -d postgres mongo backend
docker compose exec backend python db_v2/reset.py
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

Expected after seed: 5 rows in each table.

## Read-only verification (DoD guard)

Run full slice-1 checks without mutating data:

```bash
python backend/db_v2/verify.py
```

## Run the app

Start the API with Docker Compose:

```bash
docker compose up -d postgres mongo backend
```

The backend listens on `http://localhost:8000`. OpenAPI is available at:

```bash
curl "http://localhost:8000/openapi.json"
```

## Live DB integration smoke

Use this as the slice-5 live-stack evidence path. It starts `postgres`, `mongo`,
and `backend`, resets and seeds PostgreSQL from scratch, waits for OpenAPI, then
calls both run-only endpoints against the real backend:

```bash
bash scripts/smoke_match_v2_live.sh
```

Assertions covered:

- JD -> CV: `POST /api/v2/prototype/matching/job/2003/run` returns `200`.
- CV -> JD: `POST /api/v2/prototype/matching/cv/1003/run` returns `200`.
- Response includes `rank`, score components, `reasoning`, and runtime metrics.
- Deterministic top match for JD `2003` is CV `1003`.
- Deterministic top match for CV `1003` is JD `2003`.

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
curl -X POST "http://localhost:8000/api/v2/prototype/matching/job/2003/run" \
  -H "Content-Type: application/json" \
  -d '{"top_k":10,"min_score":0.7}'
```

CV -> JD:

```bash
curl -X POST "http://localhost:8000/api/v2/prototype/matching/cv/1003/run" \
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
  "anchor_id": 2003,
  "total_candidates": 5,
  "total_after_filter": 1,
  "total_returned": 1,
  "runtime_ms_total": 4.31,
  "runtime_ms_filter": 0.02,
  "runtime_ms_scoring": 0.18,
  "runtime_ms_sort": 0.01,
  "matches": [
    {
      "rank": 1,
      "cv_id": 1003,
      "job_id": 2003,
      "final_score": 0.965,
      "title_score": 1.0,
      "skills_score": 0.95,
      "req_exp_score": 0.9,
      "req_summary_score": 0.9,
      "reasoning": "Strongest signal: 'title' (score 1.000). Exact skill matches (3): aws, python, sql."
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
- No dedicated auth for this prototype unless already present in the project.
- No legacy Chroma/RAG matching dependency in the V2 prototype path.
