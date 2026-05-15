"""Slice 1: Auth, Session, /api/me.

Tests cover:
- register/login responses include expires_in.
- JWT tokens carry an `exp` claim.
- Expired tokens are rejected with 401.
- Invalid signatures are rejected with 401.
- /api/me returns role-specific bootstrap data.
- Disabled users are blocked on protected actions.

These tests stub `get_connection` to avoid requiring a live database.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import sys
import time
import unittest
from pathlib import Path
from typing import Any, Iterable, Optional
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.main import app
from jobconnect.modules.api import router as api_router


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_json(payload: dict[str, Any]) -> str:
    return _b64(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _sign_token(payload: dict[str, Any], secret: bytes | None = None) -> str:
    secret = secret if secret is not None else api_router._jwt_secret()
    header = _b64_json({"alg": "HS256", "typ": "JWT"})
    body = _b64_json(payload)
    signed = f"{header}.{body}".encode("ascii")
    sig = _b64(hmac.new(secret, signed, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


class FakeCursor:
    """Minimal cursor that consumes from a shared scripted sequence of rows."""

    def __init__(self, shared_script: list[Any]):
        self._script = shared_script  # shared reference across cursors
        self._current: Any = None

    def execute(self, *_args, **_kwargs) -> None:
        self._current = self._script.pop(0) if self._script else None

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
    """Build a get_connection patcher; script is shared across all connections."""
    shared = list(script)

    def _factory():
        return FakeConnection(shared)

    return _factory


class AuthExpiresInTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_register_response_includes_expires_in(self) -> None:
        created_at = "2026-05-16T00:00:00+00:00"
        row = (1, "alice@example.com", "candidate", "active", created_at)
        with patch.object(api_router, "get_connection", _fake_get_connection([row])):
            resp = self.client.post(
                "/api/auth/register",
                json={"email": "alice@example.com", "password": "password123", "role": "candidate"},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertIn("expires_in", body)
        self.assertIsInstance(body["expires_in"], int)
        self.assertGreater(body["expires_in"], 0)
        # Token must carry an `exp` claim.
        token = body["access_token"]
        _, payload_b64, _ = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4)))
        self.assertIn("exp", payload)
        self.assertGreater(payload["exp"], int(time.time()))

    def test_login_response_includes_expires_in(self) -> None:
        # login fetches password hash too; build a real hash for "password123".
        pwd_hash = api_router.hash_password("password123")
        row = (1, "alice@example.com", "candidate", "active", "2026-05-16T00:00:00+00:00", pwd_hash)
        with patch.object(api_router, "get_connection", _fake_get_connection([row])):
            resp = self.client.post(
                "/api/auth/login",
                json={"email": "alice@example.com", "password": "password123"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertIn("expires_in", resp.json())


class TokenValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_expired_token_is_rejected(self) -> None:
        expired_at = int(time.time()) - 60
        token = _sign_token({"sub": 1, "role": "candidate", "iat": expired_at - 3600, "exp": expired_at})
        resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "expired_token")

    def test_token_missing_exp_is_rejected(self) -> None:
        token = _sign_token({"sub": 1, "role": "candidate", "iat": int(time.time())})
        resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "expired_token")

    def test_invalid_signature_is_rejected(self) -> None:
        token = _sign_token({"sub": 1, "role": "candidate", "exp": int(time.time()) + 3600}, secret=b"wrong-secret")
        resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_token")


class MeBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def _valid_token(self, user_id: int, role: str) -> str:
        token, _ = api_router.create_access_token(user_id, role)
        return token

    def test_me_returns_candidate_profile_when_present(self) -> None:
        user_row = (1, "alice@example.com", "candidate", "active", "2026-05-16T00:00:00+00:00")
        profile_row = (1, "Alice Nguyen", "0900000000", "ha_noi", 3, "Backend engineer")
        token = self._valid_token(1, "candidate")
        # current_user dependency runs one query first; /api/me handler runs two.
        script = [
            (1, "alice@example.com", "candidate", "active"),  # current_user
            user_row,  # /api/me users row
            profile_row,  # /api/me candidate_profiles row
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["user"]["role"], "candidate")
        self.assertIsNotNone(body["candidate_profile"])
        self.assertEqual(body["candidate_profile"]["full_name"], "Alice Nguyen")
        self.assertIsNone(body["recruiter_profile"])
        self.assertIsNone(body["organization"])

    def test_me_returns_recruiter_profile_with_organization(self) -> None:
        user_row = (2, "bob@example.com", "recruiter", "active", "2026-05-16T00:00:00+00:00")
        recruiter_row = (
            2, 10, "Bob Tran", "Tech Recruiter", "0911111111",
            10, "Acme Corp", "acme", None, "About Acme",
        )
        token = self._valid_token(2, "recruiter")
        script = [
            (2, "bob@example.com", "recruiter", "active"),
            user_row,
            recruiter_row,
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["user"]["role"], "recruiter")
        self.assertIsNone(body["candidate_profile"])
        self.assertEqual(body["recruiter_profile"]["organization_id"], 10)
        self.assertEqual(body["organization"]["name"], "Acme Corp")

    def test_me_admin_returns_user_only(self) -> None:
        user_row = (3, "admin@example.com", "admin", "active", "2026-05-16T00:00:00+00:00")
        token = self._valid_token(3, "admin")
        script = [
            (3, "admin@example.com", "admin", "active"),
            user_row,
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["user"]["role"], "admin")
        self.assertIsNone(body["candidate_profile"])
        self.assertIsNone(body["recruiter_profile"])


class DisabledUserGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_disabled_user_blocked_on_protected_action(self) -> None:
        token, _ = api_router.create_access_token(99, "candidate")
        # First query is current_user lookup; status = disabled.
        script = [(99, "ghost@example.com", "candidate", "disabled")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            # Hit any endpoint that uses require_active. PUT candidate/profile is one.
            resp = self.client.put(
                "/api/candidate/profile",
                headers={"Authorization": f"Bearer {token}"},
                json={"full_name": "Ghost"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "disabled_user")


if __name__ == "__main__":
    unittest.main()
