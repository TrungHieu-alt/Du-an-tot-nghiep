"""Slice 9: Applications And Invites lifecycle hardening."""
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
    def __init__(self, state: dict[str, Any]):
        self._state = state
        self._current: Any = None
        self.rowcount = 0

    def execute(self, sql: str, params: Any = None, *_args, **_kwargs) -> None:
        self._state["statements"].append((sql, params))
        script = self._state["script"]
        self._current = script.pop(0) if script else None
        if isinstance(self._current, Exception):
            raise self._current
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
    def __init__(self, state: dict[str, Any]):
        self._state = state

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._state)

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        self._state["rollbacks"] += 1

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_exc) -> None:
        return None


def _fake_get_connection(script: Iterable[Any]):
    state = {"script": list(script), "statements": [], "rollbacks": 0}

    def _factory():
        return FakeConnection(state)

    return _factory, state


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


def _resume_row(resume_id: int = 7, candidate_user_id: int = 10, status: str = "active") -> tuple:
    return (
        resume_id,
        candidate_user_id,
        "Backend CV",
        "summary",
        "experience",
        ["python", "fastapi"],
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        [],
        True,
        status,
    )


def _job_row(job_id: int = 5, recruiter_user_id: int = 20, status: str = "published") -> tuple:
    return (
        job_id,
        100,
        recruiter_user_id,
        "Backend Engineer",
        "Build APIs",
        ["python", "fastapi"],
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        [],
        status,
        "2026-05-16T00:00:00+00:00",
        None,
    )


def _job_summary_tuple(job_id: int = 5, status: str = "published") -> tuple:
    return (
        job_id,
        "Backend Engineer",
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        ["python", "fastapi"],
        [],
        status,
        "2026-05-16T00:00:00+00:00",
    )


def _resume_summary_tuple(resume_id: int = 7, status: str = "active") -> tuple:
    return (
        resume_id,
        "Backend CV",
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        ["python", "fastapi"],
        [],
        status,
    )


def _application_detail_row(
    application_id: int = 100,
    status: str = "submitted",
    recruiter_user_id: int = 20,
) -> tuple:
    return (
        application_id,
        5,
        10,
        7,
        status,
        "2026-05-16T01:00:00+00:00",
        "2026-05-16T01:00:00+00:00",
        recruiter_user_id,
        *_job_summary_tuple(5),
        *_resume_summary_tuple(7),
    )


def _invite_detail_row(invite_id: int = 200, status: str = "pending") -> tuple:
    return (
        invite_id,
        5,
        7,
        10,
        20,
        status,
        "Please apply.",
        "2026-05-16T01:00:00+00:00",
        "2026-05-16T01:00:00+00:00",
        *_job_summary_tuple(5),
        *_resume_summary_tuple(7),
    )


def _notify_script(notification_id: int = 900, attempt_id: int = 800, email: str = "recipient@example.com") -> list[Any]:
    return [
        (notification_id,),
        (email,),
        (attempt_id,),
        None,
        None,
    ]


def _count_sql(state: dict[str, Any], fragment: str) -> int:
    needle = fragment.lower()
    return sum(1 for sql, _params in state["statements"] if needle in " ".join(sql.lower().split()))


class Slice9ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_candidate_apply_success_writes_event_notification_and_audit(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(),
                _job_row(),
                None,
                (100,),
                None,
                *_notify_script(),
                None,
                _application_detail_row(),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertEqual(body["application_id"], 100)
        self.assertEqual(body["status"], "submitted")
        self.assertEqual(body["job_summary"]["job_id"], 5)
        self.assertEqual(body["resume_summary"]["resume_id"], 7)
        self.assertEqual(_count_sql(state, "insert into application_events"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)

    def test_duplicate_apply_returns_409_without_side_effects(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(),
                _job_row(),
                _application_detail_row(),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "duplicate_application")
        self.assertEqual(_count_sql(state, "insert into application_events"), 0)
        self.assertEqual(_count_sql(state, "insert into notifications"), 0)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 0)

    def test_apply_with_inactive_resume_is_rejected(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(status="draft"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "inactive_resume")
        self.assertEqual(_count_sql(state, "insert into applications"), 0)

    def test_apply_to_closed_job_is_rejected(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(),
                _job_row(status="closed"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "closed_job")
        self.assertEqual(_count_sql(state, "insert into applications"), 0)

    def test_invalid_transition_does_not_write_side_effects(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _application_detail_row(status="submitted"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications/100/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "withdrawn"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(_count_sql(state, "insert into application_events"), 0)
        self.assertEqual(_count_sql(state, "insert into notifications"), 0)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 0)

    def test_terminal_application_state_cannot_transition_further(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _application_detail_row(status="rejected"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications/100/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "hired"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")
        self.assertEqual(_count_sql(state, "update applications set status"), 0)

    def test_application_detail_includes_ordered_event_history(self) -> None:
        token = _token(10, "candidate")
        events = [
            (1, None, "submitted", 10, "Applied", "2026-05-16T01:00:00+00:00"),
            (2, "submitted", "shortlisted", 20, "Strong match", "2026-05-16T01:05:00+00:00"),
        ]
        factory, _state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _application_detail_row(),
                events,
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/applications/100",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual([event["to_status"] for event in body["events"]], ["submitted", "shortlisted"])
        self.assertEqual(body["job_summary"]["title"], "Backend Engineer")
        self.assertEqual(body["resume_summary"]["title"], "Backend CV")


class Slice9InviteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_recruiter_invite_success_writes_notification_and_audit(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _resume_row(),
                _job_row(),
                None,
                (200, 5, 7, 10, 20, "pending", "Please apply."),
                *_notify_script(),
                None,
                _invite_detail_row(),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7, "message": "Please apply."},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["status"], "pending")
        self.assertEqual(_count_sql(state, "insert into recruiter_invites"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)
        self.assertEqual(_count_sql(state, "insert into applications"), 0)

    def test_invite_to_closed_job_is_rejected(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _resume_row(),
                _job_row(status="closed"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "closed_job")
        self.assertEqual(_count_sql(state, "insert into recruiter_invites"), 0)

    def test_accept_invite_creates_application_and_side_effects(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _invite_detail_row(),
                _resume_row(),
                _job_row(),
                None,
                (100,),
                None,
                *_notify_script(notification_id=901, attempt_id=801),
                None,
                _application_detail_row(),
                (200, 5, 7, 10, 20, "accepted", "Please apply."),
                *_notify_script(notification_id=902, attempt_id=802),
                None,
                _invite_detail_row(status="accepted"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/invites/200/accept",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertEqual(body["invite"]["status"], "accepted")
        self.assertEqual(body["application"]["application_id"], 100)
        self.assertEqual(_count_sql(state, "insert into applications"), 1)
        self.assertEqual(_count_sql(state, "insert into application_events"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 2)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 2)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 4)

    def test_accept_invite_returns_existing_application_without_duplicate(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _invite_detail_row(),
                _resume_row(),
                _job_row(),
                _application_detail_row(application_id=101),
                (200, 5, 7, 10, 20, "accepted", "Please apply."),
                *_notify_script(),
                None,
                _invite_detail_row(status="accepted"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/invites/200/accept",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["application"]["application_id"], 101)
        self.assertEqual(_count_sql(state, "insert into applications"), 0)
        self.assertEqual(_count_sql(state, "insert into application_events"), 0)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)

    def test_reject_invite_creates_no_application(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _invite_detail_row(),
                (200, 5, 7, 10, 20, "rejected", "Please apply."),
                *_notify_script(),
                None,
                _invite_detail_row(status="rejected"),
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/invites/200/reject",
                headers={"Authorization": f"Bearer {token}"},
                json={"note": "Not interested."},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "rejected")
        self.assertEqual(_count_sql(state, "insert into applications"), 0)
        self.assertEqual(_count_sql(state, "insert into application_events"), 0)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)


if __name__ == "__main__":
    unittest.main()
