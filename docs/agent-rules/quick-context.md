# Quick Context

Purpose: concise system reality snapshot for agents.

## Product Target

- Target product: production MVP recruiting marketplace with ATS-lite workflow.
- Source of truth: `docs/REQUIREMENTS.md`.
- Target backend HLD: `docs/backend/HLD/`.
- Users: candidate, recruiter, admin.
- Core target outcome: candidates activate CVs, recruiters publish jobs, both
  sides run explainable matching, and applications are created by apply or
  accepted invite.

## Current Runnable Baseline

- Backend source is organized under `backend/src/jobconnect` using app, core,
  common, integrations, and feature-module boundaries.
- Backend main app exposes MVP API namespaces under `/api/*`.
- Legacy V2 prototype runtime code has been removed; `/api/v2/prototype/*`
  route aliases are not available.
- Schema migration lives at `backend/db/migrations/001_production_mvp.sql`.
- Runtime data uses `users`, profiles, organizations,
  `candidate_resumes`, `job_posts`, embeddings, documents, parse jobs,
  applications, invites, notifications, and audit logs.
- Frontend runtime code is not present yet. Follow `README.md` Frontend
  Planning Rule; `docs/frontend/` is archived reference only.

## Target Runtime Components

- API server: FastAPI.
- Primary data store: PostgreSQL.
- Vector storage/scoring: pgvector in PostgreSQL.
- Object storage: original CV/JD files.
- Worker pipeline: file extraction, preprocessing, skill normalization, LLM
  structured parse, embedding generation.
- Matching engine: eligibility filters, hard filters, embedding retrieval,
  deterministic scoring, optional rerank, grounded reasoning.

## Target Constraints

- No tenant/company isolation in MVP; active resumes and published jobs share one
  public pool.
- Only `candidate_resumes.status = active` and `job_posts.status = published`
  enter public search/matching.
- Matching results never create applications automatically.
- API migration from `/api/v2/prototype/*` to `/api/*` namespaces is breaking;
  the main app does not keep prototype route aliases.

## Update Rule

Update this file when product target, current runtime baseline, or architecture
routing changes.
