# CLAUDE.md

Hướng dẫn ngắn gọn cho Claude Code khi làm việc trong repo này.
Nguồn canonical đầy đủ: `AGENTS.md`. File này chỉ là bản rút gọn.

## 1. Startup bắt buộc (đọc theo thứ tự)
1. `AGENTS.md`
2. `docs/agent-rules/quick-context.md`
3. `docs/agent-rules/codemap.md`
4. `docs/agent-rules/doc-map.md`
5. `docs/agent-rules/playbook.md`
6. `docs/agent-rules/definition-of-done.md`
7. `docs/agent-rules/working-contract.md`

Sau đó: phân loại task theo `playbook.md`, chỉ load thêm doc theo `doc-map.md`.

## 2. Pre-execution checkpoint (BẮT BUỘC)
Trước mọi external action (edit/write/run/generate), trả lời với 3 mục:

1. **Task Summary** — Intent, success criteria, constraints, task type.
2. **Scope** — Touch files cụ thể, out-of-scope, workflow ảnh hưởng từ `codemap.md`.
3. **Plan** — Implementation steps, verification steps, API/OpenAPI impact (`none`/`non-breaking`/`breaking`).

Yêu cầu chỉ output chat (không sửa file): vẫn phải có 3 mục trên, đánh dấu touched files = `none`.

## 3. REQUIREMENTS.md Gate
Đọc `docs/REQUIREMENTS.md` khi: feature mới, đổi behavior user-visible, sửa domain/business logic (matching, scoring, data model), giải quyết mâu thuẫn code↔spec, viết test product behavior.
Bỏ qua khi: format, rename, bug fix local rõ ràng, config không liên quan behavior.
Khi mâu thuẫn: spec thắng.

## 4. Hard Stops (không được vi phạm)
- Không ship behavior change mà thiếu verification evidence.
- Mọi bug/regression phải có test reproduce trước khi đóng task.
- Đổi API → phải sync OpenAPI contract + ghi chú.
- Đổi behavior/flow → phải cập nhật docs.
- Không giả định ngầm về security/auth/tenant boundary.
- Sửa `AGENTS.md` hoặc `docs/agent-rules/*` → phải duplicate-rule check.

## 5. Runtime Rule
- Mặc định dùng **Docker Compose** cho mọi runtime execution (tests, smoke, services).
- Host-local chỉ khi Docker không khả dụng hoặc user yêu cầu, và phải ghi rõ trong handoff.
- Migrations không auto-load: chạy `docker compose exec backend python db/apply_migrations.py`.

## 6. MCP & Tool Approval Gate
- **Phải xin xác nhận user** trước khi dùng bất kỳ MCP tool nào (nêu rõ tool nào, vì sao).
- Không có blanket approval; mỗi lần dùng cần explicit.
- Áp dụng cho cả Context7, Notion, Playwright write actions.
- `notion` trong prompt → ưu tiên Notion MCP (vẫn cần approval).
- Chỉ dùng Playwright khi prompt chứa từ `playwright`.
- Context7 chỉ khi cần API/framework external; default đọc source local trước.

## 7. Completion Handoff Template
1. What changed
2. Why it changed
3. Verification steps + outcomes
4. API/OpenAPI impact
5. Risks, gaps, follow-up actions

## 8. Repository Baseline (nhớ nhanh)
- Backend active: `backend/src/jobconnect/` (FastAPI, module-based).
- API monolithic hiện ở `modules/api/router.py` — feature folders đang trống, là target ownership.
- DB: Postgres + pgvector port `5433`, schema tại `backend/db/migrations/001_production_mvp.sql`.
- Matching helpers: `backend/src/jobconnect/modules/matching/` (hash embedding local, chưa có provider).
- Frontend runtime: chưa có. `docs/frontend/` chỉ là tham khảo, không phải source of truth.
- Test hiện rất ít → smoke-contract verification là bắt buộc.

## 9. Conflict Priority
1. System/developer instructions runtime.
2. `AGENTS.md`.
3. `docs/agent-rules/*`.
4. Inline comments / historical docs.

Khi conflict: theo cấp cao hơn + ghi vào handoff.
