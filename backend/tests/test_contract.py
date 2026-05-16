"""Slice 3: API Contract Drift Cleanup.

Covers:
- Partial PATCH semantics for resumes and jobs.
- Lifecycle transition guards (publish/close/activate/archive).
- `read-all` response key rename to `updated_count`.
- `GET /applications/{id}` includes event history.
- Duplicate pending-invite guard (409).
- OpenAPI schemas reflect explicit semantic-search + invite-accept response models.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.main import app
from jobconnect.modules.api import router as api_router


class FakeCursor:
    def __init__(self, shared_script: list[Any]):
        self._script = shared_script
        self._current: Any = None
        self.rowcount: int = 0

    def execute(self, *_args, **_kwargs) -> None:
        self._current = self._script.pop(0) if self._script else None
        # Best-effort rowcount for UPDATE statements that don't return rows.
        if isinstance(self._current, int):
            self.rowcount = self._current
            self._current = None

    def fetchone(self) -> Any:
        return self._current

    def fetchall(self) -> list[Any]:
        return list(self._current or [])

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_exc) -> None:
        return None


class FakeConnection:
    def __init__(self, shared_script: list[Any]):
        self._shared = shared_script

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._shared)

    def commit(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_exc) -> None:
        return None


def _fake_get_connection(script: Iterable[Any]):
    shared = list(script)

    def _factory():
        return FakeConnection(shared)

    return _factory


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


def _resume_row(resume_id: int, candidate_user_id: int, status: str = "draft") -> tuple:
    return (
        resume_id, candidate_user_id, "Backend CV", "summary", "experience",
        ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], False, status,
    )


def _job_row(job_id: int, recruiter_user_id: int, status: str = "draft") -> tuple:
    return (
        job_id, 100, recruiter_user_id, "Backend Engineer", "Build APIs",
        ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], status, None, None,
    )


class PartialPatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_resume_patch_accepts_title_only(self) -> None:
        token = _token(10, "candidate")
        original = _resume_row(7, 10)
        updated = list(original)
        updated[2] = "New Title"
        script = [
            (10, "c@example.com", "candidate", "active"),  # current_user
            original,                                      # _get_resume_row
            tuple(updated),                                # UPDATE RETURNING
            None,                                          # _upsert_resume_embeddings INSERT
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/candidate/resumes/7",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "New Title"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["title"], "New Title")

    def test_resume_patch_empty_body_is_noop(self) -> None:
        token = _token(10, "candidate")
        original = _resume_row(7, 10)
        script = [
            (10, "c@example.com", "candidate", "active"),
            original,
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/candidate/resumes/7",
                headers={"Authorization": f"Bearer {token}"},
                json={},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["title"], "Backend CV")

    def test_resume_patch_rejects_unknown_field(self) -> None:
        token = _token(10, "candidate")
        script = [(10, "c@example.com", "candidate", "active")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/candidate/resumes/7",
                headers={"Authorization": f"Bearer {token}"},
                json={"unknown_field": "x"},
            )
        self.assertEqual(resp.status_code, 422, resp.text)

    def test_job_patch_accepts_partial(self) -> None:
        token = _token(10, "recruiter")
        original = _job_row(5, 10)
        updated = list(original)
        updated[3] = "Senior Backend"
        script = [
            (10, "r@example.com", "recruiter", "active"),
            original,
            tuple(updated),
            None,  # embedding upsert
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/jobs/5",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "Senior Backend"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["title"], "Senior Backend")


class TransitionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_publish_rejects_already_published_job(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            _job_row(5, 10, status="published"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/jobs/5/publish",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")

    def test_close_rejects_already_closed_job(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            _job_row(5, 10, status="closed"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/jobs/5/close",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)

    def test_activate_rejects_already_active_resume(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(7, 10, status="active"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/candidate/resumes/7/activate",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)

    def test_archive_rejects_already_archived_resume(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(7, 10, status="archived"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/candidate/resumes/7/archive",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)

    def test_candidate_can_withdraw_shortlisted_application(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            (8, 5, 10, 7, "shortlisted"),
            (8,),
            None,  # application_events insert
            None,  # notification insert
            None,  # audit insert
            (8, 5, 10, 7, "withdrawn"),
            [],  # refreshed event history
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/applications/8/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "withdrawn"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "withdrawn")

    def test_recruiter_cannot_change_terminal_application(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            (8, 5, 99, 7, "rejected"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/applications/8/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "hired"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")

    def test_recruiter_cannot_withdraw_application(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            (8, 5, 99, 7, "submitted"),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/applications/8/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "withdrawn"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)


class NotificationsReadAllTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_read_all_returns_updated_count_key(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            3,  # FakeCursor maps int → rowcount on next execute (no row returned)
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/notifications/read-all",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertIn("updated_count", body)
        self.assertNotIn("updated", body)
        self.assertEqual(body["updated_count"], 3)


class DuplicateInviteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_duplicate_pending_invite_rejected(self) -> None:
        token = _token(10, "recruiter")
        resume = _resume_row(7, 99, status="active")
        job = _job_row(5, 10, status="published")
        script = [
            (10, "r@example.com", "recruiter", "active"),  # current_user
            resume,                                        # _get_resume_row
            job,                                           # _get_job_row
            (1,),                                          # duplicate-invite check → row exists
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "duplicate_invite")


class AdminMonitoringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_user_detail_includes_profile_and_ops_summary(self) -> None:
        token = _token(1, "admin")
        script = [
            (1, "admin@example.com", "admin", "active"),
            None,  # audit insert
            (10, "candidate@example.com", "candidate", "active", "2026-05-16T00:00:00+00:00"),
            (10, "Nguyen An", None, "ha_noi", 3, "Backend engineer"),
            (2,),  # resumes
            (0,),  # jobs
            (1,),  # applications
            (3,),  # invites
            (4,),  # documents
            (1,),  # parse_failures
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get(
                "/api/admin/users/10",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["user"]["role"], "candidate")
        self.assertEqual(body["candidate_profile"]["full_name"], "Nguyen An")
        self.assertEqual(body["ops_summary"]["parse_failures"], 1)


class OpenAPIShapeTests(unittest.TestCase):
    """Schema-level checks that don't need DB."""

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_openapi_exposes_explicit_response_schemas(self) -> None:
        schema = self.client.get("/openapi.json").json()
        components = schema["components"]["schemas"]
        for name in (
            "AdminUserDetail",
            "ApplicationSummary",
            "ApplicationListResponse",
            "ResumeUpdateRequest",
            "JobUpdateRequest",
            "ApplicationEvent",
            "InviteListResponse",
            "InviteAcceptResponse",
            "NotificationsReadAllResponse",
            "SemanticResumeItem",
            "SemanticJobItem",
            "SemanticResumeSearchResponse",
            "SemanticJobSearchResponse",
        ):
            self.assertIn(name, components, f"{name} missing from OpenAPI components")
        # ApplicationDetail must include `events` field.
        self.assertIn("events", components["ApplicationDetail"]["properties"])
        self.assertIn("job_summary", components["ApplicationSummary"]["properties"])
        self.assertIn("resume_summary", components["ApplicationSummary"]["properties"])
        self.assertIn("created_at", components["InviteDetail"]["properties"])
        self.assertIn("job_summary", components["InviteDetail"]["properties"])
        # PATCH resumes/jobs reference the partial request bodies.
        patch_resume = schema["paths"]["/api/candidate/resumes/{resume_id}"]["patch"]
        body_ref = patch_resume["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        self.assertTrue(body_ref.endswith("/ResumeUpdateRequest"))
        patch_job = schema["paths"]["/api/jobs/{job_id}"]["patch"]
        body_ref = patch_job["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        self.assertTrue(body_ref.endswith("/JobUpdateRequest"))

    def test_list_jobs_exposes_filter_query_parameters(self) -> None:
        schema = self.client.get("/openapi.json").json()
        params = {p["name"] for p in schema["paths"]["/api/jobs"]["get"]["parameters"]}
        for name in ("status", "location", "job_type", "seniority", "q", "limit", "offset"):
            self.assertIn(name, params)

    def test_list_organizations_exposes_q_filter(self) -> None:
        schema = self.client.get("/openapi.json").json()
        params = {p["name"] for p in schema["paths"]["/api/organizations"]["get"]["parameters"]}
        self.assertIn("q", params)

    def test_admin_endpoints_expose_monitoring_filters(self) -> None:
        schema = self.client.get("/openapi.json").json()
        expected = {
            "/api/admin/documents": {"document_type", "parse_status", "owner_user_id", "limit", "offset"},
            "/api/admin/parse-jobs": {"status", "document_type", "limit", "offset"},
            "/api/admin/applications": {"status", "job_id", "resume_id", "limit", "offset"},
            "/api/admin/invites": {"status", "job_id", "resume_id", "limit", "offset"},
            "/api/admin/notifications": {"status", "user_id", "limit", "offset"},
            "/api/admin/audit-logs": {"actor_user_id", "target_type", "target_id", "event_type", "limit", "offset"},
        }
        for path, names in expected.items():
            params = {p["name"] for p in schema["paths"][path]["get"]["parameters"]}
            self.assertTrue(names.issubset(params), f"{path} missing {names - params}")


if __name__ == "__main__":
    unittest.main()
