import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from routers.auth import create_access_token, hash_password, router


class _StubCursor:
    def __init__(self, responses):
        self._responses = list(responses)
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._responses.pop(0)


class _StubConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _make_conn(responses):
    cur = _StubCursor(responses)
    return _StubConnection(cur), cur


class AuthRouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)
        self.env_patch = patch.dict(
            os.environ,
            {
                "JWT_SECRET_KEY": "test-secret-key",
                "JWT_ALGORITHM": "HS256",
                "JWT_EXPIRE_MINUTES": "30",
            },
        )
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()

    def test_register_creates_user_without_returning_password_hash(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        conn, cur = _make_conn(
            responses=[
                None,
                (user_id, "user@example.com", "Nguyen Van A", "user"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/auth/register",
                json={
                    "email": "USER@example.com",
                    "password": "12345678",
                    "full_name": " Nguyen Van A ",
                    "role": "admin",
                },
            )

        self.assertEqual(res.status_code, 201)
        self.assertEqual(
            res.json(),
            {
                "id": user_id,
                "email": "user@example.com",
                "full_name": "Nguyen Van A",
                "role": "user",
            },
        )
        insert_params = cur.executed[1][1]
        self.assertEqual(insert_params[0], "user@example.com")
        self.assertNotEqual(insert_params[1], "12345678")
        self.assertTrue(insert_params[1].startswith("$2"))
        self.assertEqual(insert_params[2], "Nguyen Van A")
        self.assertEqual(insert_params[3], "user")
        self.assertTrue(conn.committed)
        self.assertTrue(conn.closed)

    def test_register_rejects_duplicate_email(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        conn, _ = _make_conn(
            responses=[
                (user_id, "user@example.com", None, "candidate"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/auth/register",
                json={
                    "email": "user@example.com",
                    "password": "12345678",
                    "role": "candidate",
                },
            )

        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json(), {"detail": "Email already exists"})
        self.assertFalse(conn.committed)

    def test_register_validates_email_and_password(self):
        res = self.client.post(
            "/api/auth/register",
            json={"email": "bad-email", "password": "short", "role": "owner"},
        )

        self.assertEqual(res.status_code, 422)

    def test_google_login_creates_user_and_returns_app_token(self):
        user_id = "22222222-2222-2222-2222-222222222222"
        conn, cur = _make_conn(
            responses=[
                None,
                (user_id, "google@example.com", "Google User", "user"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn), patch(
            "routers.auth._verify_google_id_token",
            return_value={
                "sub": "google-sub-1",
                "email": "Google@example.com",
                "email_verified": True,
                "name": "Google User",
                "picture": "https://example.com/avatar.png",
            },
        ):
            res = self.client.post(
                "/api/auth/google",
                json={"credential": "valid-google-id-token"},
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(body["access_token"])
        self.assertEqual(
            body["user"],
            {
                "id": user_id,
                "email": "google@example.com",
                "full_name": "Google User",
                "role": "user",
            },
        )
        insert_sql, insert_params = cur.executed[1]
        self.assertIn("INSERT INTO users", insert_sql)
        self.assertEqual(insert_params[0], "google@example.com")
        self.assertTrue(str(insert_params[1]).startswith("google:google-sub-1:"))
        self.assertEqual(insert_params[2], "Google User")
        self.assertEqual(insert_params[3], "user")
        self.assertEqual(insert_params[4], "google-sub-1")
        self.assertEqual(insert_params[5], "https://example.com/avatar.png")
        self.assertTrue(conn.committed)

    def test_google_login_links_existing_user_without_duplicate_insert(self):
        user_id = "22222222-2222-2222-2222-222222222222"
        conn, cur = _make_conn(
            responses=[
                (user_id, "user@example.com", "Existing User", "candidate"),
                (user_id, "user@example.com", "Existing User", "candidate"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn), patch(
            "routers.auth._verify_google_id_token",
            return_value={
                "sub": "google-sub-2",
                "email": "user@example.com",
                "email_verified": True,
                "name": "Google User",
            },
        ):
            res = self.client.post(
                "/api/auth/google",
                json={"credential": "valid-google-id-token"},
            )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["user"]["email"], "user@example.com")
        self.assertEqual(res.json()["user"]["role"], "candidate")
        combined_sql = "\n".join(sql for sql, _ in cur.executed)
        self.assertIn("UPDATE users", combined_sql)
        self.assertNotIn("INSERT INTO users", combined_sql)
        self.assertTrue(conn.committed)

    def test_google_login_rejects_invalid_token(self):
        conn, _ = _make_conn(responses=[])

        with patch("routers.auth.get_connection", return_value=conn), patch(
            "routers.auth._verify_google_id_token",
            side_effect=HTTPException(status_code=401, detail="Invalid Google credential"),
        ):
            res = self.client.post(
                "/api/auth/google",
                json={"credential": "bad-token"},
            )

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {"detail": "Invalid Google credential"})

    def test_login_returns_bearer_token_and_user(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        password_hash = hash_password("12345678")
        conn, _ = _make_conn(
            responses=[
                (user_id, "user@example.com", "Nguyen Van A", "candidate", password_hash),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "12345678"},
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["token_type"], "bearer")
        self.assertTrue(body["access_token"])
        self.assertEqual(
            body["user"],
            {
                "id": user_id,
                "email": "user@example.com",
                "full_name": "Nguyen Van A",
                "role": "candidate",
            },
        )

    def test_login_rejects_invalid_credentials(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        password_hash = hash_password("12345678")
        conn, _ = _make_conn(
            responses=[
                (user_id, "user@example.com", None, "candidate", password_hash),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "wrongpass"},
            )

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {"detail": "Invalid email or password"})

    def test_me_returns_current_user_for_valid_token(self):
        user_id = "11111111-1111-1111-1111-111111111111"
        token = create_access_token(
            user=type(
                "User",
                (),
                {
                    "id": user_id,
                    "email": "user@example.com",
                    "role": "candidate",
                },
            )()
        )
        conn, _ = _make_conn(
            responses=[
                (user_id, "user@example.com", "Nguyen Van A", "candidate"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.get(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["email"], "user@example.com")

    def test_me_rejects_expired_token(self):
        token = jwt.encode(
            {
                "sub": "11111111-1111-1111-1111-111111111111",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            },
            "test-secret-key",
            algorithm="HS256",
        )

        res = self.client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json(), {"detail": "Invalid or expired token"})

    def test_openapi_contract(self):
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]

        self.assertIn("/api/auth/register", paths)
        self.assertIn("/api/auth/login", paths)
        self.assertIn("/api/auth/google", paths)
        self.assertIn("/api/auth/me", paths)
        self.assertEqual(paths["/api/auth/register"]["post"]["responses"]["201"]["description"], "Successful Response")


if __name__ == "__main__":
    unittest.main()
