# MVP Roadmap Progress

Use this file as the team-maintained source for where MVP implementation stands.
Keep updates concrete and evidence-backed.

## Status Values

- `not_started`: no implementation work has begun.
- `in_progress`: implementation is actively being worked.
- `blocked`: work cannot continue until a specific blocker is resolved.
- `review`: implementation is complete and waiting for review or verification.
- `done`: DoD and verification evidence are complete.

## Update Rules

- When a slice starts, set status to `in_progress`, fill owner, branch/PR,
  started date, last updated date, and next action.
- When a slice is blocked, set status to `blocked` and write the exact blocker.
  Do not use vague blockers such as "needs checking".
- When a slice enters review, set status to `review` and link or describe the
  verification evidence already gathered.
- When a slice is done, set status to `done`, record command-backed
  verification, API/OpenAPI impact, risks, and follow-up actions.
- Keep `Verification evidence` as commands plus outcomes, not intentions.
- Keep requirement acceptance evidence in
  `docs/mvp-roadmap/requirements-acceptance-matrix.md` in sync with each code
  slice.
- Record worktree/branch status before each code slice starts.

## Progress Table

| Slice ID | Status | Owner | Current branch/PR | Started date | Last updated | Worktree status | Blocker | Current next action | Verification evidence | Acceptance evidence | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 Baseline Contract Audit | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | clean before run; CLAUDE.md untracked + matrix/progress edits after | none | Hand off impact-classified backlog to Slice 1 owner. | docker compose up postgres+backend (both healthy); `db/apply_migrations.py` exit 0; `GET /api/health` → `{"status":"ok"}`; `/openapi.json` 200, 47 paths / 58 operations matching router.py enum; `python -m unittest discover -s tests` → 6/6 OK in 0.067s | Matrix updated with `Gap Impact Classification And Slice Mapping` section: 5 confirmed breaking + 2 policy-pending breaking + ~30 non-breaking + 5 none. | See `docs/backend/LLD/50-current-api-implementation-matrix.md` for slice-mapped impact tables. |
| 1 Auth, Session, `/api/me` | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: router.py, test_auth.py, matrix, progress | none | Hand off to Slice 2 (Ownership And Authorization). | docker compose healthy; migrations exit 0; `python -m unittest discover -s tests` → 15/15 OK (9 new auth tests); `/openapi.json` `AuthResponse.required=[access_token, expires_in, user]`; `/api/me` returns `MeResponse` shape. | `expires_in` present in register/login; JWT carries `exp`; expired/missing-exp tokens → 401 `expired_token`; `/api/me` returns role-specific bootstrap; disabled users blocked on protected actions. | Breaking change: `/api/me` shape changed from `UserSummary` to `MeResponse`. Non-breaking: register/login add `expires_in`. `JWT_TTL_SECONDS` env default 86400. |
| 2 Ownership And Authorization | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: router.py, test_authorization.py, matrix, progress | none | Hand off to Slice 3 (API Contract Drift Cleanup). | docker compose healthy; `python -m unittest discover -s tests` → 25/25 OK (10 new authorization tests); `/api/health` 200. | Matching jobs/run + resumes/run enforce anchor ownership; PATCH /organizations enforces recruiter membership; admin removed from candidate/recruiter profile GET; existing ownership guards (resume PATCH, job PATCH) re-verified. Disabled-user guard confirmed via require_roles chain. | Non-breaking change: tighter 403/404 on invalid ownership paths. Admin-removal from profile GET may impact admin tooling but admins should use /api/admin/users/{id}. |
| 3 API Contract Drift Cleanup | not_started | TBD | TBD | TBD | TBD | not checked | none | Use Slice 0 drift list to prioritize. | none yet | none yet | Includes PATCH semantics, filters, explicit response models. |
| 4 Document Upload Foundation | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for contract cleanup and auth guards. | none yet | none yet | Current runtime JSON metadata endpoint must move to multipart upload. |
| 5 Parse Worker V1 | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for upload foundation. | none yet | none yet | First pass may be deterministic/local. |
| 6 LLM Parser Adapter | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for deterministic parser pipeline. | none yet | none yet | Provider integration can be staged behind adapter. |
| 7 Embedding And Semantic Search | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for parse/entity pipeline and contract cleanup. | none yet | none yet | Keep local hash fallback for dev/test. |
| 8 Matching Production Hardening | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for ownership and embedding readiness. | none yet | none yet | Matching remains recommendation-only. |
| 9 Applications And Invites | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for ownership rules and API drift cleanup. | none yet | none yet | Enforce transition graph and closed-job blocks. |
| 10 Notifications, Email, Audit | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for parse and lifecycle side effects. | none yet | none yet | Email failure must not roll back transactions. |
| 11 Admin Monitoring | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for main backend workflows to expose operational data. | none yet | none yet | Admin MVP is read-only. |
| 12 Backend End-to-End Hardening | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for backend feature slices. | none yet | none yet | Integration gate before full frontend workflow build-out. |
| 13 Frontend Design Direction | not_started | TBD | TBD | TBD | TBD | not checked | none | Choose external references and define simple screen brief. | none yet | none yet | `docs/frontend/*` is archived reference only. |
| 14 Frontend Shell And API Client | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for stable auth/API contracts and design direction. | none yet | none yet | Future runtime root likely `frontend/`. |
| 15 Frontend Core Workflows | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for frontend shell and backend end-to-end readiness. | none yet | none yet | Validate real data display before visual polish. |
| 16 End-to-End MVP Hardening | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for backend and frontend core workflows. | none yet | none yet | Final release/demo readiness pass. |

## Latest Read-Only Baseline

- Backend surface exists under `/api/*`.
- Production schema exists under `backend/db/migrations/001_production_mvp.sql`.
- Matching helpers exist under `backend/src/jobconnect/modules/matching/`.
- Frontend runtime is not active.
- Upload, parser/provider execution, real embedding provider, email delivery,
  and several contract drifts remain open.

## Slice 0 Verification Snapshot (2026-05-16)

- Docker Compose: `jobmatcher-postgres` healthy, `jobmatcher-backend` healthy.
- Migration: `docker compose exec backend python db/apply_migrations.py` exit 0.
- Health: `GET /api/health` → `{"status":"ok"}` (200).
- OpenAPI: `GET /openapi.json` → 200, 47 paths, 58 operations, no
  `/api/v2/prototype/*` routes present.
- Tests: `python -m unittest discover -s tests` → 6/6 passing.
- Impact backlog confirmed:
  - 5 confirmed breaking: `/api/me`, `POST /api/documents`,
    `GET /api/documents/{id}/download-url`, `POST /api/notifications/read-all`,
    plus auth `expires_in` if treated as required.
  - 2 policy-pending breaking: role scope of `POST /api/organizations` and
    `POST /api/jobs` (admin currently allowed).
  - ~30 non-breaking adjustments (partial PATCH, additive filters, ownership
    tightening, transition guards, additive response fields).
  - 5 already aligned (`logout`, `GET /api/organizations/{id}`, list listings,
    basic notifications read).
