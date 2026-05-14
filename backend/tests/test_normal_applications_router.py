import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import application_router
from routers.auth import AuthUser, create_access_token


CANDIDATE_ID = "11111111-1111-1111-1111-111111111111"
OTHER_CANDIDATE_ID = "22222222-2222-2222-2222-222222222222"
RECRUITER_ID = "33333333-3333-3333-3333-333333333333"
OTHER_RECRUITER_ID = "44444444-4444-4444-4444-444444444444"
JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
CV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
APPLICATION_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"
NOW = datetime(2026, 5, 14, tzinfo=timezone.utc)


class _StubCursor:
    def __init__(self, responses):
        self._responses = list(responses)
        self.executed: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, tuple(params)))

    def fetchone(self):
        return self._responses.pop(0)

    def fetchall(self):
        return self._responses.pop(0)


class _StubConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def _make_conn(responses):
    cur = _StubCursor(responses)
    return _StubConnection(cur), cur


def _user_row(user_id=CANDIDATE_ID, role="candidate"):
    return (user_id, f"{role}@example.com", f"Demo {role.title()}", role)


def _cv_row(created_by=CANDIDATE_ID):
    return (CV_ID, created_by, "Nguyen Van A", "Backend Candidate")


def _job_row(created_by=RECRUITER_ID, status="published", visibility="public", archived=False):
    return (JOB_ID, created_by, "Backend Engineer", "Demo Co", status, visibility, archived)


def _application_row(status="submitted", candidate_id=CANDIDATE_ID, recruiter_id=RECRUITER_ID):
    return (
        APPLICATION_ID,
        JOB_ID,
        CV_ID,
        candidate_id,
        recruiter_id,
        status,
        "I can start next month.",
        NOW,
        NOW,
        JOB_ID,
        "Backend Engineer",
        "Demo Co",
        CV_ID,
        "Nguyen Van A",
        "Backend Candidate",
        candidate_id,
        "candidate@example.com",
        "Demo Candidate",
        "candidate",
    )


def _token(user_id=CANDIDATE_ID, role="candidate"):
    return create_access_token(
        AuthUser(
            id=user_id,
            email=f"{role}@example.com",
            full_name=f"Demo {role.title()}",
            role=role,
        )
    )


def _auth_header(user_id=CANDIDATE_ID, role="candidate"):
    return {"Authorization": f"Bearer {_token(user_id, role)}"}


class NormalApplicationsRouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(application_router.router, prefix="/api")
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

    def test_candidate_can_apply_with_own_cv_and_count_increments(self):
        conn, cur = _make_conn(
            [
                _user_row(),
                _cv_row(),
                _job_row(),
                None,
                (APPLICATION_ID,),
                _application_row(),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/applications",
                headers=_auth_header(),
                json={
                    "jobId": JOB_ID,
                    "cvId": CV_ID,
                    "coverLetter": "I can start next month.",
                },
            )

        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["jobId"], JOB_ID)
        self.assertEqual(body["cvId"], CV_ID)
        self.assertEqual(body["candidateId"], CANDIDATE_ID)
        self.assertEqual(body["recruiterId"], RECRUITER_ID)
        self.assertEqual(body["status"], "submitted")
        self.assertEqual(body["job"]["title"], "Backend Engineer")
        self.assertEqual(body["cv"]["fullname"], "Nguyen Van A")
        self.assertNotIn("matchScore", body)
        self.assertNotIn("totalScore", body)
        self.assertNotIn("recommendation", body)
        combined_sql = "\n".join(sql for sql, _ in cur.executed)
        self.assertIn("INSERT INTO applications", combined_sql)
        self.assertIn("applications_count = applications_count + 1", combined_sql)
        self.assertTrue(conn.committed)

    def test_candidate_cannot_apply_with_another_users_cv(self):
        conn, _ = _make_conn([_user_row(), _cv_row(created_by=OTHER_CANDIDATE_ID)])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/applications",
                headers=_auth_header(),
                json={"jobId": JOB_ID, "cvId": CV_ID},
            )

        self.assertEqual(res.status_code, 404)
        self.assertFalse(conn.committed)

    def test_candidate_cannot_apply_to_nonexistent_job(self):
        conn, _ = _make_conn([_user_row(), _cv_row(), None])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/applications",
                headers=_auth_header(),
                json={"jobId": JOB_ID, "cvId": CV_ID},
            )

        self.assertEqual(res.status_code, 404)
        self.assertFalse(conn.committed)

    def test_candidate_cannot_apply_twice_to_same_job(self):
        conn, _ = _make_conn([_user_row(), _cv_row(), _job_row(), (APPLICATION_ID,)])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/applications",
                headers=_auth_header(),
                json={"jobId": JOB_ID, "cvId": CV_ID},
            )

        self.assertEqual(res.status_code, 409)
        self.assertTrue(conn.rolled_back)

    def test_candidate_can_list_only_their_applications(self):
        conn, cur = _make_conn([_user_row(), (1,), [_application_row()]])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.get("/api/applications/me", headers=_auth_header())

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["items"][0]["candidateId"], CANDIDATE_ID)
        count_params = cur.executed[1][1]
        self.assertEqual(count_params, (CANDIDATE_ID,))
        self.assertNotIn("matchLevel", body["items"][0])

    def test_candidate_does_not_see_other_users_applications(self):
        conn, _ = _make_conn([_user_row(), (0,), []])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.get("/api/applications/me", headers=_auth_header())

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"], [])

    def test_recruiter_can_list_applicants_for_own_job(self):
        conn, _ = _make_conn(
            [
                _user_row(RECRUITER_ID, "employer"),
                _job_row(created_by=RECRUITER_ID),
                (1,),
                [_application_row()],
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.get(
                f"/api/job/{JOB_ID}/applications",
                headers=_auth_header(RECRUITER_ID, "employer"),
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["items"][0]["jobId"], JOB_ID)
        self.assertEqual(body["items"][0]["cv"]["fullname"], "Nguyen Van A")

    def test_recruiter_cannot_list_applicants_for_another_recruiters_job(self):
        conn, _ = _make_conn([
            _user_row(RECRUITER_ID, "employer"),
            _job_row(created_by=OTHER_RECRUITER_ID),
        ])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.get(
                f"/api/job/{JOB_ID}/applications",
                headers=_auth_header(RECRUITER_ID, "employer"),
            )

        self.assertEqual(res.status_code, 404)

    def test_recruiter_can_update_application_status_for_own_job(self):
        conn, cur = _make_conn(
            [
                _user_row(RECRUITER_ID, "employer"),
                _application_row(),
                _job_row(created_by=RECRUITER_ID),
                _application_row(status="reviewing"),
            ]
        )

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.patch(
                f"/api/applications/{APPLICATION_ID}/status",
                headers=_auth_header(RECRUITER_ID, "employer"),
                json={"status": "reviewing"},
            )

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "reviewing")
        update_sql, update_params = cur.executed[3]
        self.assertIn("UPDATE applications", update_sql)
        self.assertEqual(update_params, ("reviewing", APPLICATION_ID))
        self.assertTrue(conn.committed)

    def test_invalid_status_is_rejected(self):
        conn, _ = _make_conn([_user_row(RECRUITER_ID, "employer")])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.patch(
                f"/api/applications/{APPLICATION_ID}/status",
                headers=_auth_header(RECRUITER_ID, "employer"),
                json={"status": "maybe"},
            )

        self.assertEqual(res.status_code, 422)

    def test_closed_job_is_not_open_for_applications(self):
        conn, _ = _make_conn([
            _user_row(),
            _cv_row(),
            _job_row(status="closed", visibility="public", archived=False),
        ])

        with patch("routers.auth.get_connection", return_value=conn):
            res = self.client.post(
                "/api/applications",
                headers=_auth_header(),
                json={"jobId": JOB_ID, "cvId": CV_ID},
            )

        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
