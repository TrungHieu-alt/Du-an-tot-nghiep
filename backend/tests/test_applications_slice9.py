"""Slice 9: Applications And Invites lifecycle hardening.

Covers DoD per slices.md §9:
- Duplicate `(job_id, resume_id)` application → 409 `duplicate_application`.
- Duplicate accepted invite returns existing application (allow_existing path).
- Terminal application states cannot move further (transition graph regression).
- Every status change writes application_event + notification + audit_log.
- Closed jobs reject NEW applications + NEW invites + invite-accept with
  explicit `closed_job` 409 (REQUIREMENTS §6.3).

Non-DoD (kept allowed by design):
- Status updates on existing applications continue to work after a job closes
  so recruiters can finalize wrap-up decisions.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch

import psycopg
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.main import app
from jobconnect.modules.api import router as api_router


# ---------------------------------------------------------------------------
# Fake DB with exception support
# ---------------------------------------------------------------------------


class FakeCursor:
    """Script-driven cursor. Pops one item per `execute` call.

    Script items:
    - tuple   → returned by next fetchone()
    - list    → returned by next fetchall()
    - int     → set rowcount, fetchone() returns None
    - None    → no-op (e.g. for INSERTs that don't return)
    - Exception instance → raised inside execute()
    """

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


# ---------------------------------------------------------------------------
# Row helpers — index layout mirrors service code (resume[12]=status, job[11]=status)
# ---------------------------------------------------------------------------


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


def _resume_row(resume_id: int, candidate_user_id: int, status: str = "active") -> tuple:
    return (
        resume_id, candidate_user_id, "Backend CV", "summary", "experience",
        ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], False, status,
    )


def _job_row(job_id: int, recruiter_user_id: int, status: str = "published") -> tuple:
    return (
        job_id, 100, recruiter_user_id, "Backend Engineer", "Build APIs",
        ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], status, None, None,
    )


def _application_row(application_id: int, candidate_user_id: int, status: str) -> tuple:
    # Matches service.application_detail row indices.
    return (application_id, 5, candidate_user_id, 7, status)


def _invite_row(invite_id: int, candidate_user_id: int, recruiter_user_id: int,
                status: str = "pending") -> tuple:
    return (invite_id, 5, 7, candidate_user_id, recruiter_user_id, status, None)


# ---------------------------------------------------------------------------
# 1. Duplicate application — psycopg UniqueViolation → 409 duplicate_application
# ---------------------------------------------------------------------------


class TestDuplicateApplication(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_duplicate_job_resume_pair_returns_409(self) -> None:
        token = _token(10, "candidate")
        # The candidate owns resume 7. Job 5 is published.
        script = [
            (10, "c@example.com", "candidate", "active"),  # current_user
            _resume_row(7, 10, "active"),                  # get_resume_row
            _job_row(5, 99, "published"),                  # get_job_row
            psycopg.errors.UniqueViolation("dup"),         # INSERT applications raises
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "duplicate_application")


# ---------------------------------------------------------------------------
# 2. Closed-job blocks — apply / invite / accept_invite
# ---------------------------------------------------------------------------


class TestClosedJobBlocks(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_apply_against_closed_job_returns_closed_job_409(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(7, 10, "active"),
            _job_row(5, 99, "closed"),
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "closed_job")

    def test_apply_against_missing_job_keeps_404(self) -> None:
        """Closed-job 409 must not regress the missing/draft-job 404 path."""
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(7, 10, "active"),
            None,  # get_job_row → not found
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 404, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "not_found")

    def test_apply_against_draft_job_keeps_400(self) -> None:
        """Draft jobs return 400 invalid_job_state (not 404) since validate_application_inputs
        fetches the job row and explicitly checks for published status."""
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(7, 10, "active"),
            _job_row(5, 99, "draft"),
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/applications",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_job_state")

    def test_invite_against_closed_job_returns_closed_job_409(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            _resume_row(7, 20, "active"),
            _job_row(5, 10, "closed"),
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/invites",
                headers={"Authorization": f"Bearer {token}"},
                json={"job_id": 5, "resume_id": 7},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "closed_job")

    def test_accept_invite_when_job_closed_returns_closed_job_409(self) -> None:
        token = _token(10, "candidate")
        # accept_invite calls validate_application_inputs which checks resume then job.
        script = [
            (10, "c@example.com", "candidate", "active"),                 # current_user
            _invite_row(invite_id=42, candidate_user_id=10,
                        recruiter_user_id=99, status="pending"),          # get_invite_row
            _resume_row(7, 10, "active"),                                 # get_resume_row (validate)
            _job_row(5, 99, "closed"),                                    # get_job_row → closed
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/invites/42/accept",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "closed_job")


# ---------------------------------------------------------------------------
# 3. Terminal state lock — transition graph regression
# ---------------------------------------------------------------------------


class TestTerminalStateLock(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def _attempt(self, *, current_status: str, target: str, role: str,
                 actor_id: int, candidate_id: int) -> Any:
        token = _token(actor_id, role)
        script = [
            (actor_id, f"u{actor_id}@example.com", role, "active"),
            _application_row(99, candidate_id, current_status),
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            return self.client.post(
                "/api/applications/99/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": target},
            )

    def test_rejected_cannot_move_to_shortlisted(self) -> None:
        resp = self._attempt(
            current_status="rejected", target="shortlisted",
            role="recruiter", actor_id=99, candidate_id=10,
        )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")

    def test_hired_cannot_move_to_rejected(self) -> None:
        resp = self._attempt(
            current_status="hired", target="rejected",
            role="recruiter", actor_id=99, candidate_id=10,
        )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")

    def test_withdrawn_cannot_move_to_submitted(self) -> None:
        resp = self._attempt(
            current_status="withdrawn", target="submitted",
            role="candidate", actor_id=10, candidate_id=10,
        )
        # Candidate role only allows the `withdrawn` target → "submitted" target is
        # role-rejected with 403 forbidden. Either way the transition is blocked.
        self.assertIn(resp.status_code, (403, 409))

    def test_terminal_withdrawn_cannot_be_changed(self) -> None:
        # Candidate tries to "withdraw" an already-withdrawn application →
        # role allows withdrawn target but transition graph requires current
        # ∈ {submitted, shortlisted}; `withdrawn` is terminal → 409.
        resp = self._attempt(
            current_status="withdrawn", target="withdrawn",
            role="candidate", actor_id=10, candidate_id=10,
        )
        self.assertEqual(resp.status_code, 409, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_transition")


# ---------------------------------------------------------------------------
# 4. Status change side effects — event + notification + audit rows
# ---------------------------------------------------------------------------


class TestStatusChangeSideEffects(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_recruiter_shortlist_writes_event_notification_audit(self) -> None:
        token = _token(99, "recruiter")
        # Flow: get_application_row → UPDATE → INSERT events → notify() [5 DB calls] →
        #        INSERT audit_logs (business) → _select_application_by_id → SELECT events
        updated_row = _application_row(99, 10, "shortlisted")
        factory = _fake_conn([
            (99, "r@example.com", "recruiter", "active"),  # current_user
            _application_row(99, 10, "submitted"),         # get_application_row
            updated_row,                                   # UPDATE applications RETURNING
            None,                                          # INSERT application_events
            (42,),                                         # notify: INSERT notifications RETURNING
            ("c@example.com",),                            # notify: SELECT email FROM users
            (88,),                                         # notify: INSERT email_attempts RETURNING
            None,                                          # notify: UPDATE notifications
            None,                                          # notify: INSERT audit_logs (email)
            None,                                          # INSERT audit_logs (business)
            updated_row,                                   # _select_application_by_id
            [],                                            # SELECT application_events
        ])
        with patch.object(api_router, "get_connection", factory):
            resp = self.client.post(
                "/api/applications/99/status",
                headers={"Authorization": f"Bearer {token}"},
                json={"status": "shortlisted"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["status"], "shortlisted")

        # Verify the key side-effect INSERTs were issued.
        all_sql = " | ".join(
            sql for c in factory.cursors for sql, _ in c.executed
        ).lower()
        self.assertIn("application_events", all_sql)
        self.assertIn("notifications", all_sql)
        self.assertIn("audit_logs", all_sql)
        self.assertIn("email_attempts", all_sql)


# ---------------------------------------------------------------------------
# 5. Duplicate accepted invite returns existing application (allow_existing path)
# ---------------------------------------------------------------------------


class TestAcceptInviteReturnsExistingApplication(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_accept_invite_when_application_already_exists(self) -> None:
        """When candidate already applied, accepting the invite must surface the
        existing application instead of raising duplicate_application."""
        token = _token(10, "candidate")
        existing_app = _application_row(77, 10, "submitted")
        invite = _invite_row(42, 10, 99, "pending")
        accepted_invite = _invite_row(42, 10, 99, "accepted")

        # Trace (verified against invites.service.accept_invite v2 flow):
        # 1. current_user
        # 2. get_invite_row
        # 3. get_resume_row (validate_application_inputs)
        # 4. get_job_row (validate_application_inputs)
        # 5. _select_application_by_pair (inside create_application_in_cursor) → existing found
        # 6. UPDATE recruiter_invites RETURNING → accepted_invite
        # 7-11. notify() [INSERT notifications, SELECT email, INSERT email_attempts, UPDATE notif, INSERT audit]
        # 12. INSERT audit_logs (business invite_accepted)
        # 13. _select_invite_by_id
        script = [
            (10, "c@example.com", "candidate", "active"),  # current_user
            invite,                                        # get_invite_row
            _resume_row(7, 10, "active"),                  # get_resume_row (validate)
            _job_row(5, 99, "published"),                  # get_job_row (validate)
            existing_app,                                  # _select_application_by_pair → found
            accepted_invite,                               # UPDATE recruiter_invites RETURNING
            (901,),                                        # notify: INSERT notifications
            ("recruiter@example.com",),                    # notify: SELECT email FROM users
            (801,),                                        # notify: INSERT email_attempts
            None,                                          # notify: UPDATE notifications
            None,                                          # notify: INSERT audit_logs (email)
            None,                                          # INSERT audit_logs (business)
            accepted_invite,                               # _select_invite_by_id
        ]
        with patch.object(api_router, "get_connection", _fake_conn(script)):
            resp = self.client.post(
                "/api/invites/42/accept",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertIn("invite", body)
        self.assertIn("application", body)
        self.assertEqual(body["invite"]["status"], "accepted")
        self.assertEqual(body["application"]["application_id"], 77)
        self.assertEqual(body["application"]["status"], "submitted")


if __name__ == "__main__":
    unittest.main()
