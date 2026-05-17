"""Slice 10: Notifications, Email, Audit."""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from typing import Any, Iterable, Optional
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.email import EmailSendError, EmailSendResult
from jobconnect.main import app
from jobconnect.modules.api import router as api_router
from jobconnect.modules.documents import worker as worker_module
from jobconnect.modules.documents.worker import _ParseJobInfo, _execute, _fail


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


class LocalSender:
    provider_name = "local"

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def send_email(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailSendResult:
        self.messages.append({"to": to, "subject": subject, "body": body, "metadata": metadata or {}})
        return EmailSendResult(status="logged", provider="local")


class FailingSender:
    provider_name = "test-failing"

    def send_email(
        self,
        to: Optional[str],
        subject: str,
        body: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> EmailSendResult:
        raise EmailSendError("smtp down", provider=self.provider_name)


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


def _parse_job_info() -> _ParseJobInfo:
    return _ParseJobInfo(
        parse_job_id=99,
        document_id=11,
        target_entity_type="candidate_resume",
        existing_resume_id=None,
        existing_job_id=None,
        status="queued",
        object_key="documents/bad.pdf",
        mime_type="application/pdf",
        original_filename="bad.pdf",
        owner_user_id=10,
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


def _params_for(state: dict[str, Any], fragment: str) -> list[Any]:
    needle = fragment.lower()
    return [
        params
        for sql, params in state["statements"]
        if needle in " ".join(sql.lower().split())
    ]


class Slice10NotificationEmailAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_application_apply_creates_notification_email_attempt_and_audit(self) -> None:
        token = _token(10, "candidate")
        sender = LocalSender()
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(),
                _job_row(),
                None,
                (100,),
                None,
                *_notify_script(notification_id=901, attempt_id=801, email="recruiter@example.com"),
                None,
                _application_detail_row(),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=sender):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )

        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["application_id"], 100)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[0], "recruiter@example.com")
        self.assertEqual(email_attempt_params[4], "application_submitted")
        self.assertEqual(email_attempt_params[5], "logged")
        self.assertEqual(email_attempt_params[6], "local")
        business_audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("candidate_applied", business_audit_events)
        self.assertIn("email_attempt_recorded", business_audit_events)
        self.assertEqual(sender.messages[0]["to"], "recruiter@example.com")

    def test_email_failure_does_not_rollback_application_apply(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _resume_row(),
                _job_row(),
                None,
                (101,),
                None,
                *_notify_script(notification_id=902, attempt_id=802, email="recruiter@example.com"),
                None,
                _application_detail_row(application_id=101),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=FailingSender()):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )

        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["application_id"], 101)
        self.assertEqual(state["rollbacks"], 0)
        self.assertEqual(_count_sql(state, "insert into applications"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[5], "failed")
        self.assertEqual(email_attempt_params[6], "test-failing")
        self.assertIn("smtp down", email_attempt_params[7])
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("email_send_failed", audit_events)
        self.assertIn("candidate_applied", audit_events)

    def test_invite_create_records_notification_email_and_audit(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _resume_row(),
                _job_row(),
                None,
                (200, 5, 7, 10, 20, "pending", "Please apply."),
                *_notify_script(notification_id=903, attempt_id=803, email="candidate@example.com"),
                None,
                _invite_detail_row(),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=LocalSender()):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7, "message": "Please apply."},
            )

        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["status"], "pending")
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[4], "recruiter_invite_sent")
        self.assertEqual(email_attempt_params[5], "logged")
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("recruiter_invite_sent", audit_events)

    def test_email_failure_does_not_rollback_invite_create(self) -> None:
        token = _token(20, "recruiter")
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _resume_row(),
                _job_row(),
                None,
                (201, 5, 7, 10, 20, "pending", "Please apply."),
                *_notify_script(notification_id=910, attempt_id=810, email="candidate@example.com"),
                None,
                _invite_detail_row(invite_id=201),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=FailingSender()):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7, "message": "Please apply."},
            )

        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["invite_id"], 201)
        self.assertEqual(state["rollbacks"], 0)
        self.assertEqual(_count_sql(state, "insert into recruiter_invites"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[4], "recruiter_invite_sent")
        self.assertEqual(email_attempt_params[5], "failed")
        self.assertEqual(email_attempt_params[6], "test-failing")
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("email_send_failed", audit_events)
        self.assertIn("recruiter_invite_sent", audit_events)

    def test_accept_invite_creates_application_and_records_side_effects(self) -> None:
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
                *_notify_script(notification_id=904, attempt_id=804, email="recruiter@example.com"),
                None,
                _application_detail_row(),
                (200, 5, 7, 10, 20, "accepted", "Please apply."),
                *_notify_script(notification_id=905, attempt_id=805, email="recruiter@example.com"),
                None,
                _invite_detail_row(status="accepted"),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=LocalSender()):
            resp = self.client.post(
                "/api/invites/200/accept",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["invite"]["status"], "accepted")
        self.assertEqual(resp.json()["application"]["application_id"], 100)
        self.assertEqual(_count_sql(state, "insert into applications"), 1)
        self.assertEqual(_count_sql(state, "insert into application_events"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 2)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 2)
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("candidate_applied", audit_events)
        self.assertIn("invite_accepted", audit_events)

    def test_reject_invite_records_side_effects_without_application(self) -> None:
        token = _token(10, "candidate")
        factory, state = _fake_get_connection(
            [
                (10, "c@example.com", "candidate", "active"),
                _invite_detail_row(),
                (200, 5, 7, 10, 20, "rejected", "Please apply."),
                *_notify_script(notification_id=906, attempt_id=806, email="recruiter@example.com"),
                None,
                _invite_detail_row(status="rejected"),
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=LocalSender()):
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
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("invite_rejected", audit_events)

    def test_application_status_change_records_notification_event_audit(self) -> None:
        token = _token(20, "recruiter")
        events = [
            (1, None, "submitted", 10, "Applied", "2026-05-16T01:00:00+00:00"),
            (2, "submitted", "shortlisted", 20, "Strong match", "2026-05-16T01:05:00+00:00"),
        ]
        factory, state = _fake_get_connection(
            [
                (20, "r@example.com", "recruiter", "active"),
                _application_detail_row(status="submitted"),
                (100,),
                None,
                *_notify_script(notification_id=907, attempt_id=807, email="candidate@example.com"),
                None,
                _application_detail_row(status="shortlisted"),
                events,
            ]
        )
        with patch.object(api_router, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=LocalSender()):
            resp = self.client.post(
                "/api/applications/100/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "shortlisted", "note": "Strong match"},
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "shortlisted")
        self.assertEqual([event["to_status"] for event in resp.json()["events"]], ["submitted", "shortlisted"])
        self.assertEqual(_count_sql(state, "insert into application_events"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("application_status_changed", audit_events)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[4], "application_status_changed")

    def test_admin_audit_log_query_returns_required_fields(self) -> None:
        token = _token(1, "admin")
        audit_row = (
            77,
            10,
            "candidate_applied",
            "application",
            100,
            {"job_id": 5, "resume_id": 7},
            "2026-05-16T01:00:00+00:00",
        )
        factory, state = _fake_get_connection(
            [
                (1, "admin@example.com", "admin", "active"),
                None,
                (1,),
                [audit_row],
            ]
        )
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.get(
                "/api/admin/audit-logs",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(resp.status_code, 200, resp.text)
        item = resp.json()["items"][0]
        self.assertEqual(item["actor_user_id"], 10)
        self.assertEqual(item["event_type"], "candidate_applied")
        self.assertEqual(item["target_entity_type"], "application")
        self.assertEqual(item["target_entity_id"], 100)
        self.assertEqual(item["metadata"]["job_id"], 5)
        self.assertEqual(item["created_at"], "2026-05-16T01:00:00+00:00")
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("admin_monitoring_access", audit_events)

    def test_parse_failure_email_failure_is_non_blocking(self) -> None:
        factory, state = _fake_get_connection(
            [
                None,
                *_notify_script(notification_id=908, attempt_id=808, email="candidate@example.com"),
                None,
            ]
        )
        with patch.object(worker_module, "get_connection", factory), patch.object(api_router, "get_email_sender", return_value=FailingSender()):
            _fail(_parse_job_info(), "empty_extraction", "No text could be extracted from the file.")

        self.assertEqual(state["rollbacks"], 0)
        self.assertEqual(_count_sql(state, "update parse_jobs"), 1)
        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[4], "parse_failed")
        self.assertEqual(email_attempt_params[5], "failed")
        self.assertEqual(email_attempt_params[6], "test-failing")
        audit_events = [params[1] for params in _params_for(state, "insert into audit_logs")]
        self.assertIn("email_send_failed", audit_events)
        self.assertIn("parse_job_failed", audit_events)

    def test_worker_empty_extraction_records_parse_failure_side_effects(self) -> None:
        load_row = (
            99,
            11,
            "candidate_resume",
            None,
            None,
            "queued",
            "documents/bad.pdf",
            "application/pdf",
            "bad.pdf",
            10,
        )
        factory, state = _fake_get_connection(
            [
                load_row,
                None,
                None,
                *_notify_script(notification_id=909, attempt_id=809, email="candidate@example.com"),
                None,
            ]
        )
        mock_storage = MagicMock()
        mock_storage.open.return_value = io.BytesIO(b"")

        with patch.object(worker_module, "get_connection", factory), \
             patch.object(worker_module, "get_storage", return_value=mock_storage), \
             patch.object(api_router, "get_email_sender", return_value=LocalSender()):
            _execute(99)

        self.assertEqual(_count_sql(state, "insert into notifications"), 1)
        self.assertEqual(_count_sql(state, "insert into email_attempts"), 1)
        self.assertEqual(_count_sql(state, "insert into audit_logs"), 2)
        email_attempt_params = _params_for(state, "insert into email_attempts")[0]
        self.assertEqual(email_attempt_params[4], "parse_failed")
        self.assertEqual(email_attempt_params[5], "logged")


if __name__ == "__main__":
    unittest.main()
