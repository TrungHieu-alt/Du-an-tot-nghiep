"""Slice 10: Notifications, Email, Audit.

Covers DoD per slices.md §10:
- Required business events create in-app notification rows.
- Email attempts are recorded (email_delivery_status updated to 'sent'/'failed').
- Email failure does not roll back business transactions.
- LocalLogEmailSender logs and completes without raising.
- dispatch_email() swallows all exceptions from email sender.
- notify() returns a valid notification_id (RETURNING).
- Audit rows exist for key business events.
"""
from __future__ import annotations

import logging
import sys
import unittest
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.email import (
    EmailSendResult,
    LocalLogEmailSender,
    get_email_sender,
    reset_email_sender_cache,
)
from jobconnect.main import app
from jobconnect.modules.api import router as api_router
from jobconnect.modules.api.shared import dispatch_email, notify


# ---------------------------------------------------------------------------
# Fake DB helpers (shared with slice 9 pattern)
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


# ---------------------------------------------------------------------------
# 1. EmailSender adapter — local log sender
# ---------------------------------------------------------------------------


class TestLocalLogEmailSender(unittest.TestCase):
    def test_send_email_returns_result_and_does_not_raise(self) -> None:
        sender = LocalLogEmailSender()
        result = sender.send_email("user@example.com", "Test Subject", "Test body content")
        self.assertIsInstance(result, EmailSendResult)
        self.assertEqual(result.status, "logged")

    def test_send_email_logs_message(self) -> None:
        sender = LocalLogEmailSender()
        with self.assertLogs("jobconnect.integrations.email", level="INFO") as cm:
            sender.send_email("a@b.com", "Subject", "x" * 300)
        self.assertTrue(any("local email" in line.lower() for line in cm.output))

    def test_get_email_sender_returns_local_by_default(self) -> None:
        import os
        reset_email_sender_cache()
        original = os.environ.pop("EMAIL_PROVIDER", None)
        try:
            sender = get_email_sender()
            self.assertIsInstance(sender, LocalLogEmailSender)
        finally:
            if original is not None:
                os.environ["EMAIL_PROVIDER"] = original
            reset_email_sender_cache()

    def test_get_email_sender_explicit_local(self) -> None:
        import os
        reset_email_sender_cache()
        os.environ["EMAIL_PROVIDER"] = "local"
        try:
            sender = get_email_sender()
            self.assertIsInstance(sender, LocalLogEmailSender)
        finally:
            del os.environ["EMAIL_PROVIDER"]
            reset_email_sender_cache()

    def test_get_email_sender_unknown_falls_back_to_local(self) -> None:
        """Unknown EMAIL_PROVIDER logs a warning and falls back to LocalLogEmailSender."""
        import os
        reset_email_sender_cache()
        os.environ["EMAIL_PROVIDER"] = "nonexistent"
        try:
            sender = get_email_sender()
            self.assertIsInstance(sender, LocalLogEmailSender)
        finally:
            del os.environ["EMAIL_PROVIDER"]
            reset_email_sender_cache()


# ---------------------------------------------------------------------------
# 2. notify() writes notification row with email_attempt and audit side effects
# ---------------------------------------------------------------------------


class TestNotifyBehavior(unittest.TestCase):
    def test_notify_writes_notification_insert_with_returning(self) -> None:
        """notify() must INSERT into notifications with RETURNING notification_id."""
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (42,)
        notify(mock_cur, 1, "test_type", "Title", "Body", "application", 99)
        # First execute call should be the notifications INSERT
        first_sql = mock_cur.execute.call_args_list[0][0][0]
        self.assertIn("notifications", first_sql.lower())
        self.assertIn("RETURNING notification_id", first_sql)

    def test_notify_writes_email_attempt_and_audit(self) -> None:
        """notify() must also write email_attempts and audit_logs rows."""
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (42,)
        notify(mock_cur, 1, "test_type", "Title", "Body", "application", 99)
        all_sql = " ".join(
            call[0][0].lower() for call in mock_cur.execute.call_args_list
        )
        self.assertIn("email_attempts", all_sql)
        self.assertIn("audit_logs", all_sql)


# ---------------------------------------------------------------------------
# 3. dispatch_email() — success path updates status to 'sent'
# ---------------------------------------------------------------------------


class TestDispatchEmailSuccess(unittest.TestCase):
    def test_dispatch_email_calls_sender_and_marks_sent(self) -> None:
        # notification row: recipient_id, title, body, email
        notif_row = (5, "App submitted", "A candidate applied.", "recruiter@example.com")
        factory = _fake_conn([
            notif_row,   # SELECT notifications JOIN users
            None,        # UPDATE email_delivery_status = 'sent'
        ])
        sent_calls: list[tuple] = []

        class CaptureSender(LocalLogEmailSender):
            def send_email(self, to, subject, body, metadata=None) -> EmailSendResult:
                sent_calls.append((to, subject, body))
                return EmailSendResult(status="sent", provider="local")

        with patch.object(api_router, "get_connection", factory), \
             patch("jobconnect.integrations.email.get_email_sender", return_value=CaptureSender()):
            dispatch_email(42)

        self.assertEqual(len(sent_calls), 1)
        self.assertEqual(sent_calls[0][0], "recruiter@example.com")
        self.assertEqual(sent_calls[0][1], "App submitted")

        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("email_delivery_status", all_sql)
        self.assertIn("sent", all_sql)

    def test_dispatch_email_skips_when_notification_not_found(self) -> None:
        factory = _fake_conn([None])  # SELECT returns None
        with patch.object(api_router, "get_connection", factory):
            dispatch_email(999)  # Should not raise


# ---------------------------------------------------------------------------
# 4. dispatch_email() — failure path updates status to 'failed'
# ---------------------------------------------------------------------------


class TestDispatchEmailFailure(unittest.TestCase):
    def test_email_send_failure_marks_failed_and_does_not_raise(self) -> None:
        notif_row = (5, "Title", "Body", "user@example.com")
        factory = _fake_conn([
            notif_row,  # SELECT notifications JOIN users
            None,       # UPDATE email_delivery_status = 'failed'
        ])

        class BrokenSender(LocalLogEmailSender):
            def send_email(self, to, subject, body, metadata=None) -> EmailSendResult:
                raise RuntimeError("SMTP connection refused")

        with patch.object(api_router, "get_connection", factory), \
             patch("jobconnect.integrations.email.get_email_sender", return_value=BrokenSender()):
            # Must not raise
            dispatch_email(42)

        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("failed", all_sql)

    def test_dispatch_email_with_minus_one_id_does_not_crash(self) -> None:
        # notification_id=-1 means no notification was created (e.g. allow_existing path)
        # dispatch_email returns early without any DB call when id <= 0
        dispatch_email(-1)  # Should not raise, no DB call needed


# ---------------------------------------------------------------------------
# 5. Email failure does not affect business transaction
# ---------------------------------------------------------------------------


class TestEmailFailureDoesNotAffectBusiness(unittest.TestCase):
    def test_application_status_update_succeeds_even_if_email_fails(self) -> None:
        """When email sending raises inside notify(), the HTTP response is still 200.
        The email_attempt is marked failed and business transaction is unaffected."""
        from fastapi.testclient import TestClient

        client = TestClient(app, raise_server_exceptions=False)
        token = _token(99, "recruiter")
        updated_row = (99, 5, 10, 7, "shortlisted")

        # Full DB script matching update_application_status() with inline notify():
        # current_user → get_application_row → UPDATE RETURNING → INSERT events →
        # notify [INSERT notifications, SELECT email, INSERT email_attempts, UPDATE notif, INSERT audit] →
        # INSERT audit (business) → _select_application_by_id → SELECT events
        factory = _fake_conn([
            (99, "r@example.com", "recruiter", "active"),   # current_user
            (99, 5, 10, 7, "submitted"),                    # get_application_row
            updated_row,                                     # UPDATE applications RETURNING
            None,                                            # INSERT application_events
            (42,),                                           # notify: INSERT notifications
            ("c@example.com",),                              # notify: SELECT email
            (88,),                                           # notify: INSERT email_attempts
            None,                                            # notify: UPDATE notifications
            None,                                            # notify: INSERT audit_logs (email)
            None,                                            # INSERT audit_logs (business)
            updated_row,                                     # _select_application_by_id
            [],                                              # SELECT application_events
        ])

        class BrokenSender:
            provider_name = "broken"

            def send_email(self, to, subject, body, metadata=None) -> EmailSendResult:
                raise RuntimeError("SMTP is down")

        with patch.object(api_router, "get_connection", factory), \
             patch.object(api_router, "get_email_sender", return_value=BrokenSender()):
            resp = client.post(
                "/api/applications/99/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "shortlisted"},
            )

        # Business transaction must succeed despite email failure
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "shortlisted")
        # email_attempts row must have been inserted (email failure is recorded, not skipped)
        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("email_attempts", all_sql)
        self.assertIn("insert into email_attempts", all_sql)


# ---------------------------------------------------------------------------
# 6. notify() creates row with correct fields (SQL shape check)
# ---------------------------------------------------------------------------


class TestNotifyInsertShape(unittest.TestCase):
    def test_notify_passes_all_required_fields(self) -> None:
        mock_cur = MagicMock()
        mock_cur.fetchone.return_value = (7,)
        notify(mock_cur, 99, "invite_sent", "Invite", "You were invited.", "invite", 55)
        # First execute call is the notifications INSERT
        first_sql, first_params = mock_cur.execute.call_args_list[0][0]
        self.assertIn("notifications", first_sql)
        self.assertIn("queued", first_sql)  # email_delivery_status default
        self.assertIn(99, first_params)     # recipient_user_id
        self.assertIn("invite_sent", first_params)
        self.assertIn("invite", first_params)
        self.assertIn(55, first_params)     # entity_id


# ---------------------------------------------------------------------------
# 7. Audit side-effect SQL is issued for key business events
# ---------------------------------------------------------------------------


class TestAuditSideEffects(unittest.TestCase):
    def setUp(self) -> None:
        from fastapi.testclient import TestClient
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_invite_create_writes_audit_row(self) -> None:
        token = _token(10, "recruiter")
        resume_row = (7, 20, "CV", "sum", "exp", ["py"], "ha_noi", "remote", "mid", "dai_hoc", [], False, "active")
        job_row = (5, 100, 10, "Dev", "req", ["py"], "ha_noi", "remote", "mid", "dai_hoc", [], "published", None, None)
        invite_detail_row = (42, 5, 7, 20, 10, "pending", None)

        # create_invite() flow: get_resume_row, get_job_row, SELECT pending, INSERT invite,
        # notify() [5 DB calls], INSERT audit_logs (business), _select_invite_by_id
        factory = _fake_conn([
            (10, "r@example.com", "recruiter", "active"),  # current_user
            resume_row,                                    # get_resume_row
            job_row,                                       # get_job_row
            None,                                          # SELECT pending invite → None
            (42, 5, 7, 20, 10, "pending", None),           # INSERT recruiter_invites RETURNING
            (1,),                                          # notify: INSERT notifications
            ("c@example.com",),                            # notify: SELECT email
            (51,),                                         # notify: INSERT email_attempts
            None,                                          # notify: UPDATE notifications
            None,                                          # notify: INSERT audit_logs (email)
            None,                                          # INSERT audit_logs (business)
            invite_detail_row,                             # _select_invite_by_id
        ])

        with patch.object(api_router, "get_connection", factory), \
             patch.object(api_router, "get_email_sender", return_value=LocalLogEmailSender()):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        all_sql = " | ".join(sql for c in factory.cursors for sql, _ in c.executed).lower()
        self.assertIn("audit_logs", all_sql)
        self.assertIn("email_attempts", all_sql)


if __name__ == "__main__":
    unittest.main()
