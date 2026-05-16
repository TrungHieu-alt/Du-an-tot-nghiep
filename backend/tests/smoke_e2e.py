"""Slice 12: Backend End-to-End Smoke Script.

Runs against a live service (default http://localhost:8000) and exercises the
full MVP candidate flow end-to-end:

    register (candidate + recruiter) → create org → profiles → create job →
    publish job → match (job→resumes) → apply → invite → admin inspect

Exit 0 on success; non-zero on first failure with a descriptive message.

Usage (inside Docker Compose):
    docker compose exec backend python tests/smoke_e2e.py

Override base URL:
    docker compose exec backend python tests/smoke_e2e.py http://localhost:8000
"""
from __future__ import annotations

import sys
import time
import uuid
import httpx


BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

_STEP = 0


def step(name: str) -> None:
    global _STEP
    _STEP += 1
    print(f"[{_STEP:02d}] {name}", flush=True)


def check(condition: bool, msg: str) -> None:
    if not condition:
        print(f"    FAIL: {msg}", flush=True)
        sys.exit(1)
    print(f"    ok: {msg}", flush=True)


def post(path: str, json: dict, token: str | None = None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.post(f"{BASE}{path}", json=json, headers=headers, timeout=10)


def get(path: str, token: str | None = None, params: dict | None = None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.get(f"{BASE}{path}", headers=headers, params=params, timeout=10)


def patch(path: str, json: dict, token: str | None = None) -> httpx.Response:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return httpx.patch(f"{BASE}{path}", json=json, headers=headers, timeout=10)


# ── unique suffix so smoke runs don't collide on the same DB ──────────────────
uid = uuid.uuid4().hex[:8]
CAND_EMAIL = f"cand_{uid}@smoke.test"
CAND_PASS = "Smoke1234!"
REC_EMAIL = f"rec_{uid}@smoke.test"
REC_PASS = "Smoke1234!"
ADMIN_EMAIL = f"admin_{uid}@smoke.test"
ADMIN_PASS = "Smoke1234!"
ORG_NAME = f"SmokeOrg {uid}"
JOB_TITLE = f"Smoke Job {uid}"


# ── 1. Health ─────────────────────────────────────────────────────────────────
step("GET /api/health")
r = get("/api/health")
check(r.status_code == 200, f"status={r.status_code}")
check(r.json() == {"status": "ok"}, f"body={r.json()}")

# ── 2. Register candidate ─────────────────────────────────────────────────────
step("POST /api/auth/register (candidate)")
r = post("/api/auth/register", {"email": CAND_EMAIL, "password": CAND_PASS, "role": "candidate"})
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
cand_token = r.json()["access_token"]
check(bool(cand_token), "access_token present")
check("expires_in" in r.json(), "expires_in present")
cand_user_id = r.json()["user"]["user_id"]

# ── 3. Register recruiter ─────────────────────────────────────────────────────
step("POST /api/auth/register (recruiter)")
r = post("/api/auth/register", {"email": REC_EMAIL, "password": REC_PASS, "role": "recruiter"})
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
rec_token = r.json()["access_token"]

# ── 4. Register admin ─────────────────────────────────────────────────────────
step("POST /api/auth/register (admin)")
r = post("/api/auth/register", {"email": ADMIN_EMAIL, "password": ADMIN_PASS, "role": "admin"})
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
admin_token = r.json()["access_token"]

# ── 5. GET /api/me (candidate) ────────────────────────────────────────────────
step("GET /api/me (candidate)")
r = get("/api/me", token=cand_token)
check(r.status_code == 200, f"status={r.status_code}")
check(r.json()["user"]["role"] == "candidate", f"role={r.json()['user'].get('role')}")

# ── 6. Create organization ────────────────────────────────────────────────────
step("POST /api/organizations")
r = post("/api/organizations", {"name": ORG_NAME}, token=rec_token)
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
org_id = r.json()["organization_id"]

# ── 7. Create recruiter profile ───────────────────────────────────────────────
step("PUT /api/recruiter/profile")
r = httpx.put(f"{BASE}/api/recruiter/profile", json={"organization_id": org_id, "full_name": f"Rec {uid}"}, headers={"Authorization": f"Bearer {rec_token}"}, timeout=10)
check(r.status_code in (200, 201), f"status={r.status_code} body={r.text}")

# ── 8. Create candidate profile ───────────────────────────────────────────────
step("PUT /api/candidate/profile")
r = httpx.put(f"{BASE}/api/candidate/profile", json={"full_name": f"Cand {uid}"}, headers={"Authorization": f"Bearer {cand_token}"}, timeout=10)
check(r.status_code in (200, 201), f"status={r.status_code} body={r.text}")

# ── 9. Create resume ──────────────────────────────────────────────────────────
step("POST /api/candidate/resumes")
r = post(
    "/api/candidate/resumes",
    {
        "title": f"Resume {uid}",
        "location": "ha_noi",
        "job_type": "fulltime",
        "seniority": "mid",
        "education": "dai_hoc",
        "skills": ["python", "fastapi"],
        "summary": "Smoke test candidate",
        "experience": "3 years backend",
    },
    token=cand_token,
)
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
resume_id = r.json()["resume_id"]

# ── 10. Activate resume ───────────────────────────────────────────────────────
step("POST /api/candidate/resumes/{id}/activate")
r = post(f"/api/candidate/resumes/{resume_id}/activate", {}, token=cand_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")

# ── 11. Create job ────────────────────────────────────────────────────────────
step("POST /api/jobs")
r = post(
    "/api/jobs",
    {
        "title": JOB_TITLE,
        "organization_id": org_id,
        "location": "ha_noi",
        "job_type": "fulltime",
        "seniority": "mid",
        "education": "dai_hoc",
        "requirement": "Need python and fastapi skills",
        "skills": ["python", "fastapi"],
    },
    token=rec_token,
)
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
job_id = r.json()["job_id"]

# ── 12. Publish job ───────────────────────────────────────────────────────────
step("POST /api/jobs/{id}/publish")
r = post(f"/api/jobs/{job_id}/publish", {}, token=rec_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")

# ── 13. Run matching (job→resumes) ────────────────────────────────────────────
step("POST /api/matching/jobs/{id}/run")
r = post(f"/api/matching/jobs/{job_id}/run", {}, token=rec_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")
body = r.json()
check("items" in body, f"body keys={list(body.keys())}")

# ── 14. Apply to job ──────────────────────────────────────────────────────────
step("POST /api/applications")
r = post("/api/applications", {"job_id": job_id, "resume_id": resume_id}, token=cand_token)
check(r.status_code in (201, 200), f"status={r.status_code} body={r.text}")
application_id = r.json()["application_id"]

# ── 15. Shortlist application (recruiter) ─────────────────────────────────────
step("POST /api/applications/{id}/status → shortlisted")
r = post(f"/api/applications/{application_id}/status", {"status": "shortlisted"}, token=rec_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")

# ── 16. Create invite ─────────────────────────────────────────────────────────
step("POST /api/invites")
r = post(
    "/api/invites",
    {"job_id": job_id, "resume_id": resume_id},
    token=rec_token,
)
check(r.status_code == 201, f"status={r.status_code} body={r.text}")
invite_id = r.json()["invite_id"]

# ── 17. Accept invite (candidate) ─────────────────────────────────────────────
step("POST /api/invites/{id}/accept")
r = post(f"/api/invites/{invite_id}/accept", {}, token=cand_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")

# ── 18. List candidate notifications ─────────────────────────────────────────
step("GET /api/notifications")
r = get("/api/notifications", token=cand_token)
check(r.status_code == 200, f"status={r.status_code}")
check("items" in r.json(), f"body={r.json()}")

# ── 19. Admin: list users ─────────────────────────────────────────────────────
step("GET /api/admin/users")
r = get("/api/admin/users", token=admin_token)
check(r.status_code == 200, f"status={r.status_code} body={r.text}")
check("items" in r.json(), f"body keys={list(r.json().keys())}")

# ── 20. Admin: list applications ─────────────────────────────────────────────
step("GET /api/admin/applications")
r = get("/api/admin/applications", token=admin_token)
check(r.status_code == 200, f"status={r.status_code}")

# ── 21. Admin: list audit logs ────────────────────────────────────────────────
step("GET /api/admin/audit-logs")
r = get("/api/admin/audit-logs", token=admin_token)
check(r.status_code == 200, f"status={r.status_code}")

# ── 22. Error envelope — unauthenticated ─────────────────────────────────────
step("GET /api/me (no token) → 401 error envelope")
r = get("/api/me")
check(r.status_code == 401, f"status={r.status_code}")
check("error" in r.json(), f"body={r.json()}")
check("code" in r.json()["error"], f"error={r.json()['error']}")

print(f"\nAll {_STEP} smoke steps passed.", flush=True)
