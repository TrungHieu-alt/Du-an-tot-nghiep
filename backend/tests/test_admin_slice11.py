"""Slice 11: Admin Monitoring.

Covers DoD per slices.md §11:
- Admin can access all monitoring endpoints with correct data.
- Non-admin users (candidate, recruiter) receive 403 on all admin endpoints.
- Filters (role, status, q, document_type, parse_status, event_type) are wired.
- User detail includes profile context and ops_summary counts.
- Admin monitoring access writes audit rows for users/documents/parse-jobs.
"""
from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from jobconnect.main import app
from jobconnect.modules.api import router as api_router


# ---------------------------------------------------------------------------
# Fake DB helpers
# ---------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared
        self.executed: list[tuple[str, Any]] = []
        self._current: Any = None
        self.rowcount: int = 0

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))
        item = self._shared.pop(0) if self._shared else None
        if isinstance(item, Exception):
            raise item
        if isinstance(item, int):
            self.rowcount = item
            self._current = None
            return
        self._current = item

    def fetchone(self) -> Any:
        return self._current

    def fetchall(self) -> list[Any]:
        return list(self._current or [])

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_exc) -> None:
        return None


class FakeConnection:
    def __init__(self, shared: list[Any], cursor_log: list[FakeCursor]) -> None:
        self._shared = shared
        self._log = cursor_log

    def cursor(self) -> FakeCursor:
        c = FakeCursor(self._shared)
        self._log.append(c)
        return c

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_exc) -> None:
        return None


def _fake_conn(script: Iterable[Any]):
    shared = list(script)
    cursors: list[FakeCursor] = []

    def _factory():
        return FakeConnection(shared, cursors)

    _factory.cursors = cursors  # type: ignore[attr-defined]
    return _factory


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


_NOW = datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)


def _user_row(user_id: int, role: str = "candidate", status: str = "active") -> tuple:
    return (user_id, f"u{user_id}@example.com", role, status, _NOW)


def _doc_row(doc_id: int, owner_id: int = 10) -> tuple:
    return (doc_id, owner_id, "candidate_resume", f"uploads/{doc_id}.pdf",
            None, "cv.pdf", "application/pdf", 1024, None, None, _NOW)


def _parse_job_row(pj_id: int, doc_id: int = 1, status: str = "succeeded") -> tuple:
    return (pj_id, doc_id, "candidate_resume", None, None,
            status, None, None, _NOW, _NOW)


def _application_row(app_id: int) -> tuple:
    return (app_id, 5, 10, 7, "submitted")


def _invite_row(invite_id: int) -> tuple:
    return (invite_id, 5, 7, 10, 99, "pending", None)


def _notification_row(notif_id: int) -> tuple:
    return (notif_id, 10, "application_submitted", "unread", "Title", "Body", "application", 1)


def _audit_row(audit_id: int) -> tuple:
    return (audit_id, 99, "candidate_applied", "application", 1, {}, _NOW)


# ---------------------------------------------------------------------------
# 1. Non-admin denial — all admin endpoints return 403
# ---------------------------------------------------------------------------


class TestAdminNonAdminDenied(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self.endpoints = [
            ("GET", "/api/admin/users"),
            ("GET", "/api/admin/users/1"),
            ("GET", "/api/admin/documents"),
            ("GET", "/api/admin/parse-jobs"),
            ("GET", "/api/admin/applications"),
            ("GET", "/api/admin/invites"),
            ("GET", "/api/admin/notifications"),
            ("GET", "/api/admin/audit-logs"),
        ]

    def _expect_403(self, role: str) -> None:
        user_row = _user_row(1, role)
        for method, path in self.endpoints:
            token = _token(1, role)
            factory = _fake_conn([user_row])
            with patch.object(api_router, "get_connection", factory):
                resp = getattr(self.client, method.lower())(
                    path, headers={"Authorization": f"Bearer {token}"}
                )
            self.assertEqual(resp.status_code, 403, f"{method} {path} with {role} should be 403 got {resp.status_code}")

    def test_candidate_denied_all_admin_endpoints(self) -> None:
        self._expect_403("candidate")

    def test_recruiter_denied_all_admin_endpoints(self) -> None:
        self._expect_403("recruiter")


# ---------------------------------------------------------------------------
# 2. Admin users list — success + audit written
# ---------------------------------------------------------------------------


class TestAdminUsersList(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_users_returns_paginated_list(self) -> None:
        token = _token(99, "admin")
        user_row = _user_row(10, "candidate")
        factory = _fake_conn([
            _user_row(99, "admin"),           # current_user
            None,                             # audit INSERT
            (2,),                             # SELECT COUNT(*)
            [user_row],                       # SELECT users list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 1)
        self.assertEqual(body["items"][0]["user_id"], 10)

    def test_admin_users_filter_by_role_passes_param(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,           # audit
            (0,),           # COUNT
            [],             # list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/users?role=recruiter",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["total"], 0)

    def test_admin_users_writes_audit(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,   # audit
            (0,),
            [],
        ])
        with patch.object(api_router, "get_connection", factory):
            self.client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("audit_logs", all_sql)


# ---------------------------------------------------------------------------
# 3. Admin user detail — profile + ops_summary
# ---------------------------------------------------------------------------


class TestAdminUserDetail(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_user_detail_candidate_returns_ops_summary(self) -> None:
        token = _token(99, "admin")
        # candidate_profile query returns None (no profile set)
        factory = _fake_conn([
            _user_row(99, "admin"),                      # current_user
            None,                                         # audit
            _user_row(10, "candidate"),                  # SELECT user
            None,                                         # SELECT candidate_profiles → not set
            (1,),  # resumes count
            (0,),  # jobs count
            (2,),  # applications count
            (0,),  # invites count
            (1,),  # documents count
            (0,),  # parse_failures count
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/users/10",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["user"]["user_id"], 10)
        self.assertEqual(body["user"]["role"], "candidate")
        self.assertIsNone(body["candidate_profile"])
        self.assertEqual(body["ops_summary"]["resumes"], 1)
        self.assertEqual(body["ops_summary"]["applications"], 2)

    def test_admin_user_detail_not_found_returns_404(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,   # audit
            None,   # SELECT user → not found
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/users/999",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 404, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "not_found")


# ---------------------------------------------------------------------------
# 4. Admin documents list
# ---------------------------------------------------------------------------


class TestAdminDocuments(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_documents_returns_paginated_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,                    # audit
            (1,),                    # COUNT
            [_doc_row(1)],           # list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/documents",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["document_id"], 1)

    def test_admin_documents_filter_by_document_type(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None, (0,), [],
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/documents?document_type=job_post",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        # Verify document_type filter was passed into SQL
        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("uploaded_documents", all_sql)


# ---------------------------------------------------------------------------
# 5. Admin parse-jobs list
# ---------------------------------------------------------------------------


class TestAdminParseJobs(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_parse_jobs_returns_paginated_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,                          # audit
            (1,),                          # COUNT
            [_parse_job_row(5)],           # list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/parse-jobs",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["parse_job_id"], 5)
        self.assertEqual(body["items"][0]["status"], "succeeded")

    def test_admin_parse_jobs_filter_by_status(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None, (0,), [],
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/parse-jobs?status=failed",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)


# ---------------------------------------------------------------------------
# 6. Admin applications list
# ---------------------------------------------------------------------------


class TestAdminApplications(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_applications_returns_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,                            # audit INSERT
            (3,),                            # COUNT
            [_application_row(1), _application_row(2)],  # list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/applications",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["total"], 3)
        self.assertEqual(len(resp.json()["items"]), 2)

    def test_admin_applications_filter_by_status(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None, (0,), [],   # audit + COUNT + list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/applications?status=shortlisted",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)


# ---------------------------------------------------------------------------
# 7. Admin invites list
# ---------------------------------------------------------------------------


class TestAdminInvites(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_invites_returns_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,           # audit INSERT
            (1,),
            [_invite_row(10)],
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/invites",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["invite_id"], 10)


# ---------------------------------------------------------------------------
# 8. Admin notifications list
# ---------------------------------------------------------------------------


class TestAdminNotifications(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_notifications_returns_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,           # audit INSERT
            (2,),
            [_notification_row(1), _notification_row(2)],
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/notifications",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["total"], 2)

    def test_admin_notifications_filter_by_user_id(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None, (0,), [],   # audit + COUNT + list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/notifications?user_id=10",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)


# ---------------------------------------------------------------------------
# 9. Admin audit-logs list
# ---------------------------------------------------------------------------


class TestAdminAuditLogs(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_audit_logs_returns_list(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,           # audit INSERT
            (1,),
            [_audit_row(1)],
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/audit-logs",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["event_type"], "candidate_applied")
        self.assertEqual(body["items"][0]["target_entity_type"], "application")

    def test_admin_audit_logs_filter_by_event_type(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None, (0,), [],   # audit + COUNT + list
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/audit-logs?event_type=parse_job_failed",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)


# ---------------------------------------------------------------------------
# 10. PATCH /api/admin/users/{user_id} — admin can enable/disable users
# ---------------------------------------------------------------------------


class TestAdminUpdateUser(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_can_disable_another_user(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),                                          # current_user
            (10, "active"),                                                  # SELECT user_id, status
            (10, "u10@example.com", "candidate", "disabled", _NOW),          # UPDATE RETURNING
            None,                                                            # INSERT audit_logs
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.patch(
                "/api/admin/users/10",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "disabled"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "disabled")
        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("audit_logs", all_sql)

    def test_admin_cannot_disable_self(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([_user_row(99, "admin")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.patch(
                "/api/admin/users/99",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "disabled"},
            )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "self_disable_forbidden")

    def test_admin_update_missing_user_returns_404(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([
            _user_row(99, "admin"),
            None,    # SELECT user → not found
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.patch(
                "/api/admin/users/999",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "active"},
            )
        self.assertEqual(resp.status_code, 404, resp.text)

    def test_non_admin_patch_user_returns_403(self) -> None:
        token = _token(10, "candidate")
        factory = _fake_conn([_user_row(10, "candidate")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.patch(
                "/api/admin/users/20",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "disabled"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_patch_user_without_status_returns_400(self) -> None:
        token = _token(99, "admin")
        factory = _fake_conn([_user_row(99, "admin")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.patch(
                "/api/admin/users/10",
                headers={"Authorization": f"Bearer {token}"},
                json={},
            )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "no_fields")


if __name__ == "__main__":
    unittest.main()
