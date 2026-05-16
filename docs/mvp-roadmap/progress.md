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
| 3 API Contract Drift Cleanup | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: router.py, test_contract.py, matrix, progress | none | Hand off to Slice 4 (Document Upload Foundation). | docker compose healthy; `python -m unittest discover -s tests` → 38/38 OK (13 new contract tests); `/openapi.json` exposes ResumeUpdateRequest, JobUpdateRequest, ApplicationEvent, InviteAcceptResponse, NotificationsReadAllResponse, SemanticResume/JobItem + …Response. | Partial PATCH for resumes/jobs; list filters for orgs (`q`) and jobs (`location/job_type/seniority/q`); jobs/search q covers org name; read-all returns `updated_count`; applications detail includes events; lifecycle transition guards (job publish/close, resume activate/archive) → 409 on invalid; explicit semantic-search response schemas; duplicate pending-invite → 409; explicit invite-accept response model. | Breaking: `read-all` key rename. PATCH partial (non-breaking — relaxes validation). Policy-pending: `POST /api/organizations` and `POST /api/jobs` still allow admin (deferred). |
| 4 Document Upload Foundation | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: router.py, requirements.txt, integrations/storage/*, test_documents.py, matrix, progress | none | Hand off to Slice 5 (Parse Worker V1). | docker compose rebuild backend (python-multipart added); `python -m unittest discover -s tests` → 49/49 OK (11 new document tests); `/openapi.json` shows `POST /api/documents` content-type `multipart/form-data`, components include `DocumentUploadResponse`, `DocumentDownloadUrlResponse`, `ParseJobDetail`; `DocumentDetail.parse_jobs` exposed; `DocumentRequest` removed. | Multipart upload through `LocalFilesystemStorage` (STORAGE_BACKEND=local, STORAGE_LOCAL_ROOT=/app/backend/uploads); MIME allow-list (PDF/DOC/DOCX) with 415; 10 MiB cap with 413; `download-url` returns `{download_url, expires_at}`; document detail includes parse_jobs; parse-jobs retry audits `parse_job_retried`. | Breaking: `POST /api/documents` request type (JSON → multipart) + response wraps in `{document, parse_job}`; `download-url` field rename. Storage adapter is dev-only filesystem; Slice 5/12 may swap in S3/MinIO. |
| 5 Parse Worker V1 | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: modules/documents/*, integrations/storage/*, router.py, requirements.txt, tests/test_parse_worker.py | none | Hand off to Slice 6 (LLM Parser Adapter). | docker compose healthy; `python -m unittest discover -s tests` → 81/81 OK (32 new parse-worker tests); `GET /api/health` 200; `/openapi.json` 200, 47 paths. | CV fixture (plain text) → ParsedResume with skills+enums; JD fixture → ParsedJob; empty-extraction → failed parse_job + notification + audit; all prior 49 tests unchanged. | Parser version=local-v1, embedding version=hash-v1. BackgroundTasks wires upload+retry into worker. DOCX extraction returns '' (Slice 6 scope). |
| 6 LLM Parser Adapter | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: integrations/llm/*, modules/documents/{worker,local_parser}.py, tests/test_llm_parser.py, HLD §20, progress | none | Hand off to Slice 7 (Embedding And Semantic Search). | docker compose healthy; `python -m unittest discover -s tests` → 103/103 OK (22 new LLM parser tests); `GET /api/health` 200; `/openapi.json` 47 paths / 58 ops (no contract change). | EN/VN/mixed CV+JD fixtures map to canonical enums via LocalDeterministicParser; OpenAIParser sanitizes invalid enums to safe defaults; raw unsupported values never persisted; ParserError raised on network/HTTP/JSON failures (worker marks `llm_parse_failed`); `get_parser()` falls back to local when `OPENAI_API_KEY` missing. | Env vars: `LLM_PROVIDER` (local\|openai, default local), `OPENAI_API_KEY`, `OPENAI_MODEL` (default gpt-4o-mini), `OPENAI_BASE_URL`, `OPENAI_TIMEOUT_SECONDS=30`. Parser versions: `local-v1` / `openai-{model}-v1`. API/OpenAPI impact: `none`. |
| 7 Embedding And Semantic Search | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: integrations/embedding/*, router.py, worker.py, tests/test_embedding_provider.py, test_documents.py, HLD §40, implementation matrix, roadmap | none | Go for Slice 8 with condition: carry application lifecycle transition graph / terminal-lock drift as P2 backlog. | docker compose healthy; migrations exit 0; targeted `python -m unittest tests.test_embedding_provider tests.test_documents tests.test_llm_parser tests.test_contract` → 69/69 OK; full `python -m unittest discover -s tests` → 126/126 OK; `GET /api/health` 200; `/openapi.json` 47 paths / 58 ops; live smoke covered auth, document/parse, semantic search, matching, apply duplicate, invite accept/reject. | LocalHashEmbeddingProvider and OpenAIEmbeddingProvider remain provider-backed boundaries; semantic resume search now uses summary/experience embeddings; semantic job search now uses requirement embedding; parse-job upload/retry and worker success metadata persist active provider embedding version; missing-embedding scoring + reasoning regression covered. | Env vars unchanged: `EMBEDDING_PROVIDER` (local\|openai, default local), `OPENAI_EMBEDDING_API_KEY` (fallback to `OPENAI_API_KEY`), `OPENAI_EMBEDDING_MODEL`, `OPENAI_EMBEDDING_BASE_URL`, `OPENAI_EMBEDDING_TIMEOUT_SECONDS=30`. DB dim fixed at 384. API/OpenAPI impact: `non-breaking`. |
| 8 Matching Production Hardening | done | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: matching service/schemas, rerank integration, tests, LLD/HLD/roadmap docs | none | Hand off to Slice 9 (Applications And Invites). | `docker compose exec backend python -m unittest tests.test_matching_slice8 tests.test_rerank_provider tests.test_app_surface` → 12/12 OK; `docker compose exec backend python -m unittest discover -s tests` → 139/139 OK; `GET /api/health` → `{"status":"ok"}`; `GET /openapi.json` saved to `/tmp/openapi-slice8.json` (77632 bytes). | Matching defaults aligned (`top_k=10`, `min_score=0.7`); runtime now attempts local cross-encoder rerank with deterministic fallback warnings; semantic-search embedding failures return `503 embedding_unavailable`; additive runtime/breakdown fields documented in LLD/HLD + implementation matrix. | API/OpenAPI impact: non-breaking additive fields + default behavior tightening. Matching remains recommendation-only (no application/invite side effects). |
| 9 Applications And Invites | done | AI agent | v2 (working tree) | 2026-05-17 | 2026-05-17 | clean before run; dirty after Slice 9 code/docs/tests + ignored `.env` local setup file | none | Hand off to Slice 10 (Notifications, Email, Audit). | Docker 28.5.2 / Compose v2.40.3; `.env` created from `.env.example`; initial `docker compose up -d --build` installed deps but hit a transient Docker Desktop BuildKit export snapshot error, `docker compose up -d` started backend/postgres healthy from the built image, and retry `docker compose up -d --build` completed successfully; migration `docker compose exec backend python db/apply_migrations.py` exit 0; targeted `python -m unittest tests.test_slice9_applications_invites` -> 12/12 OK; targeted Slice 9 + contract `python -m unittest tests.test_slice9_applications_invites tests.test_contract` -> 30/30 OK; final full `python -m unittest discover -s tests` -> 151/151 OK; `Invoke-RestMethod /api/health` -> `ok`; `/openapi.json` -> 47 paths, 51 schemas, `ApplicationListResponse` and `InviteListResponse` present. | Apply success/duplicate/inactive/closed, invite create/closed, accept create/existing, reject, invalid transition, terminal lock, ordered application event history, notification/audit/application-event side effects verified in Slice 9 tests. | API/OpenAPI impact: non-breaking behavior hardening plus additive typed list response schemas and linked summary/timestamp fields. Canonical app statuses remain `submitted`, `shortlisted`, `rejected`, `hired`, `withdrawn`; terminal: `rejected`, `hired`, `withdrawn`. |
| 10 Notifications, Email, Audit | done | AI agent | v2 (working tree) | 2026-05-17 | 2026-05-17 | clean before run; dirty after Slice 10 code/docs/tests + ignored `.env` local setup file | none | Hand off to Slice 11 (Admin Monitoring) with email/audit side effects in place. | Docker 28.5.2 / Compose v2.40.3; `docker compose up -d --build` completed; migration `docker compose exec backend python db/apply_migrations.py` exit 0; targeted `python -m unittest tests.test_slice10_notifications_email_audit` -> 10/10 OK; full `python -m unittest discover -s tests` -> 161/161 OK; `Invoke-RestMethod /api/health` -> `ok`; `/openapi.json` -> 47 paths, 51 schemas, `NotificationDetail.metadata` and `NotificationDetail.email_delivery_status` present. | Business notification creation, email attempt recording, fake email failure non-rollback for application/invite/parse failure, invite create/accept/reject side effects, application status-change side effects, and audit log query smoke verified by Slice 10 tests. | Email adapter mode defaults to local/log (`EMAIL_PROVIDER` unset or `local`); SMTP provider path is available with `EMAIL_PROVIDER=smtp`, `SMTP_HOST`, and `EMAIL_FROM`. |
| 11 Admin Monitoring | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for main backend workflows to expose operational data. | none yet | none yet | Admin MVP is read-only. |
| 12 Backend End-to-End Hardening | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for backend feature slices. | none yet | none yet | Integration gate before full frontend workflow build-out. |
| 13 Frontend Design Direction | review | AI agent | v2 (working tree) | 2026-05-16 | 2026-05-16 | dirty: docs/frontend/screen/*, docs/frontend/README.md, roadmap docs | none | Review production-like screen specs and matrix before Slice 14 frontend shell starts. | production-like screen specs updated; `docs/frontend/screen-to-api-state-matrix.md` added; shared Vietnamese UI state contract added | Full MVP screen set maps to backend APIs/states for candidate, recruiter, shared, and admin flows; visible UI copy is Vietnamese while docs remain English. | Frontend runtime remains out of scope; archived docs remain reference only. |
| 14 Frontend Shell And API Client | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for stable auth/API contracts and design direction. | none yet | none yet | Future runtime root likely `frontend/`. |
| 15 Frontend Core Workflows | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for frontend shell and backend end-to-end readiness. | none yet | none yet | Validate real data display before visual polish. |
| 16 End-to-End MVP Hardening | not_started | TBD | TBD | TBD | TBD | not checked | none | Wait for backend and frontend core workflows. | none yet | none yet | Final release/demo readiness pass. |

## Latest Read-Only Baseline

- Backend surface exists under `/api/*`.
- API runtime no longer uses monolith fallback; domain routers/services are
  active and `_legacy_api_impl.py` was removed.
- Production schema exists under `backend/db/migrations/001_production_mvp.sql`.
- Matching helpers exist under `backend/src/jobconnect/modules/matching/`.
- Frontend runtime is not active; active Slice 13 screen specs now live under
  `docs/frontend/screen/`.
- Upload, parse worker, LLM parser adapter, embedding provider boundary,
  semantic search, auth/session, ownership, and core API drift cleanup have
  slice-level verification evidence.
- Remaining open work includes admin monitoring smoke coverage, backend
  end-to-end smoke, frontend runtime implementation, and final MVP hardening.

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
