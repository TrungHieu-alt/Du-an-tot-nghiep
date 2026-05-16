"""Slice 12: Backend End-to-End Hardening — Contract Shape Tests.

Covers:
- Error envelope consistency: every non-2xx response wraps in {"error": {...}}.
- Standard HTTP status codes return the documented error codes.
- CORS headers are present for known frontend origins.
- OpenAPI schema is available and contains required paths.
- Validation errors (422) are normalized into the error envelope.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fastapi.testclient import TestClient

from jobconnect.main import app
from jobconnect.modules.api import router as api_router


class FakeCursor:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared
        self._current: Any = None
        self.rowcount: int = 0

    def execute(self, sql: str, params: Any = None) -> None:
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
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._shared)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_exc) -> None:
        return None


def _fake_conn(script: list[Any]):
    shared = list(script)

    def _factory():
        return FakeConnection(shared)

    return _factory


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


# ---------------------------------------------------------------------------
# 1. Error envelope consistency
# ---------------------------------------------------------------------------


class TestErrorEnvelope(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def _assert_error_envelope(self, resp, expected_status: int, expected_code: str | None = None) -> None:
        self.assertEqual(resp.status_code, expected_status, resp.text)
        body = resp.json()
        self.assertIn("error", body, f"Missing 'error' key: {body}")
        error = body["error"]
        self.assertIn("code", error, f"Missing 'code' in error: {error}")
        self.assertIn("message", error, f"Missing 'message' in error: {error}")
        if expected_code:
            self.assertEqual(error["code"], expected_code)

    # 401 — missing/invalid token
    def test_missing_token_returns_401_envelope(self) -> None:
        resp = self.client.get("/api/me")
        self._assert_error_envelope(resp, 401, "invalid_token")

    def test_invalid_token_returns_401_envelope(self) -> None:
        resp = self.client.get("/api/me", headers={"Authorization": "Bearer bad.token.here"})
        self._assert_error_envelope(resp, 401)

    # 403 — wrong role
    def test_wrong_role_returns_403_envelope(self) -> None:
        token = _token(1, "candidate")
        factory = _fake_conn([(1, "c@example.com", "candidate", "active")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
        self._assert_error_envelope(resp, 403, "forbidden")

    # 404 — resource not found
    def test_not_found_returns_404_envelope(self) -> None:
        token = _token(1, "candidate")
        factory = _fake_conn([
            (1, "c@example.com", "candidate", "active"),
            None,  # application not found
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get("/api/applications/99999", headers={"Authorization": f"Bearer {token}"})
        self._assert_error_envelope(resp, 404, "not_found")

    # 409 — duplicate resource
    def test_duplicate_registration_returns_409_envelope(self) -> None:
        import psycopg
        factory = _fake_conn([psycopg.errors.UniqueViolation("dup")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/auth/register",
                json={"email": "a@b.com", "password": "Password1!", "role": "candidate"},
            )
        self._assert_error_envelope(resp, 409, "duplicate_email")

    # 422 — validation error normalized into error envelope
    def test_validation_error_returns_422_error_envelope(self) -> None:
        resp = self.client.post("/api/auth/register", json={"email": "not-an-email"})
        self.assertEqual(resp.status_code, 422)
        body = resp.json()
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "validation_error")
        self.assertIn("fields", body["error"])

    def test_extra_field_in_request_returns_422_envelope(self) -> None:
        resp = self.client.post(
            "/api/auth/register",
            json={"email": "a@b.com", "password": "pw", "role": "candidate", "unknown_field": "x"},
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("error", resp.json())

    # 405 — method not allowed (FastAPI default, becomes 405 without our handler)
    def test_unknown_path_returns_404_not_error_500(self) -> None:
        resp = self.client.get("/api/does-not-exist")
        self.assertNotEqual(resp.status_code, 500)


# ---------------------------------------------------------------------------
# 2. CORS headers
# ---------------------------------------------------------------------------


class TestCORSHeaders(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def _options(self, origin: str) -> Any:
        return self.client.options(
            "/api/health",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

    def test_vite_dev_origin_allowed(self) -> None:
        resp = self._options("http://localhost:5173")
        self.assertIn(resp.status_code, (200, 204))
        origin_header = resp.headers.get("access-control-allow-origin", "")
        self.assertEqual(origin_header, "http://localhost:5173")

    def test_nextjs_dev_origin_allowed(self) -> None:
        resp = self._options("http://localhost:3000")
        self.assertIn(resp.status_code, (200, 204))
        origin_header = resp.headers.get("access-control-allow-origin", "")
        self.assertEqual(origin_header, "http://localhost:3000")

    def test_credentials_allowed(self) -> None:
        resp = self._options("http://localhost:5173")
        self.assertEqual(resp.headers.get("access-control-allow-credentials"), "true")

    def test_unknown_origin_not_reflected(self) -> None:
        resp = self._options("http://attacker.example.com")
        origin_header = resp.headers.get("access-control-allow-origin", "")
        self.assertNotEqual(origin_header, "http://attacker.example.com")


# ---------------------------------------------------------------------------
# 3. OpenAPI availability and required paths
# ---------------------------------------------------------------------------


class TestOpenAPIContract(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self._schema = None

    def _schema_json(self) -> dict:
        if self._schema is None:
            resp = self.client.get("/openapi.json")
            self.assertEqual(resp.status_code, 200)
            self._schema = resp.json()
        return self._schema

    def test_openapi_available(self) -> None:
        schema = self._schema_json()
        self.assertIn("paths", schema)
        self.assertIn("components", schema)

    def test_openapi_has_auth_paths(self) -> None:
        paths = self._schema_json()["paths"]
        self.assertIn("/api/auth/register", paths)
        self.assertIn("/api/auth/login", paths)
        self.assertIn("/api/me", paths)

    def test_openapi_has_admin_paths(self) -> None:
        paths = self._schema_json()["paths"]
        for path in [
            "/api/admin/users",
            "/api/admin/documents",
            "/api/admin/parse-jobs",
            "/api/admin/applications",
            "/api/admin/invites",
            "/api/admin/notifications",
            "/api/admin/audit-logs",
        ]:
            self.assertIn(path, paths)

    def test_openapi_has_matching_paths(self) -> None:
        paths = self._schema_json()["paths"]
        self.assertIn("/api/matching/jobs/{job_id}/run", paths)
        self.assertIn("/api/matching/resumes/{resume_id}/run", paths)

    def test_openapi_error_schemas_defined(self) -> None:
        schemas = self._schema_json()["components"]["schemas"]
        self.assertIn("ErrorEnvelope", schemas)
        self.assertIn("ErrorBody", schemas)

    def test_health_endpoint_available(self) -> None:
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})


# ---------------------------------------------------------------------------
# 4. Auth flow shape — register + login + me
# ---------------------------------------------------------------------------


class TestAuthFlow(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_register_returns_access_token_and_expires_in(self) -> None:
        from datetime import datetime, timezone
        user_row = (1, "new@example.com", "candidate", "active",
                    datetime(2026, 5, 17, tzinfo=timezone.utc))
        factory = _fake_conn([user_row])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/auth/register",
                json={"email": "new@example.com", "password": "Password1!", "role": "candidate"},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertIn("access_token", body)
        self.assertIn("expires_in", body)
        self.assertIn("user", body)
        self.assertEqual(body["user"]["role"], "candidate")

    def test_login_wrong_password_returns_401(self) -> None:
        from jobconnect.modules.api.shared import hash_password
        stored_hash = hash_password("correct_password")
        user_row = (1, "u@example.com", "candidate", "active", stored_hash, "active")
        factory = _fake_conn([user_row])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/auth/login",
                json={"email": "u@example.com", "password": "wrong_password"},
            )
        self._assert_error_envelope(resp, 401)

    def _assert_error_envelope(self, resp, status: int) -> None:
        self.assertEqual(resp.status_code, status, resp.text)
        self.assertIn("error", resp.json())


# ---------------------------------------------------------------------------
# 5. Disabled user guard
# ---------------------------------------------------------------------------


class TestDisabledUserGuard(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_disabled_user_cannot_access_protected_endpoint(self) -> None:
        token = _token(5, "candidate")
        factory = _fake_conn([(5, "d@example.com", "candidate", "disabled")])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get("/api/candidate/profile", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "disabled_user")


if __name__ == "__main__":
    unittest.main()
