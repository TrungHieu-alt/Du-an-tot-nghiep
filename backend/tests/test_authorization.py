"""Slice 2: Ownership And Authorization boundaries.

Each test stubs `get_connection` with a scripted row sequence and asserts the
correct 403/404 outcome for ownership violations.
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
    shared = list(script)

    def _factory():
        return FakeConnection(shared)

    return _factory


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


def _job_row(job_id: int, recruiter_user_id: int, organization_id: int = 100) -> tuple:
    """Row matching JOB_DETAIL_COLS:
    job_id, organization_id, recruiter_user_id, title, requirement, skills,
    location, job_type, seniority, education, required_certifications,
    status, published_at, expires_at."""
    return (
        job_id,
        organization_id,
        recruiter_user_id,
        "Backend Engineer",
        "Build APIs",
        ["python"],
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        [],
        "published",
        None,
        None,
    )


def _resume_row(resume_id: int, candidate_user_id: int) -> tuple:
    """Row matching RESUME_DETAIL_COLS:
    resume_id, candidate_user_id, title, summary, experience, skills,
    location, job_type, seniority, education, certifications, is_primary,
    status."""
    return (
        resume_id,
        candidate_user_id,
        "Backend CV",
        "summary",
        "experience",
        ["python"],
        "ha_noi",
        "remote",
        "mid",
        "dai_hoc",
        [],
        True,
        "active",
    )


class MatchingOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_recruiter_cannot_match_against_other_recruiter_job(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),  # current_user
            _job_row(job_id=5, recruiter_user_id=99),       # _get_job_row
            None,                                           # _load_job embeddings
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/matching/jobs/5/run",
                headers={"Authorization": f"Bearer {token}"},
                json={"top_k": 5, "min_score": 0.7, "rerank": False},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "forbidden")

    def test_candidate_cannot_match_against_other_candidate_resume(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(resume_id=7, candidate_user_id=99),
            None,
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/matching/resumes/7/run",
                headers={"Authorization": f"Bearer {token}"},
                json={"top_k": 5, "min_score": 0.7, "rerank": False},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "forbidden")

    def test_admin_can_bypass_matching_ownership(self) -> None:
        """Admin reaches the published-anchor check rather than the ownership 403."""
        token = _token(1, "admin")
        # Job owned by recruiter 99 but in `draft` status. With admin bypass on
        # ownership, the handler then hits the `published` guard and returns 400.
        draft_job = list(_job_row(job_id=5, recruiter_user_id=99))
        draft_job[11] = "draft"
        script = [
            (1, "a@example.com", "admin", "active"),
            tuple(draft_job),
            None,
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/matching/jobs/5/run",
                headers={"Authorization": f"Bearer {token}"},
                json={"top_k": 5, "min_score": 0.7, "rerank": False},
            )
        self.assertEqual(resp.status_code, 400, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "invalid_anchor")


class OrganizationOwnershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_recruiter_not_in_organization_cannot_patch(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),  # current_user
            None,                                          # _recruiter_in_organization -> not member
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/organizations/55",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Hacked Corp"},
            )
        self.assertEqual(resp.status_code, 404, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "not_found")

    def test_recruiter_in_organization_can_patch(self) -> None:
        token = _token(10, "recruiter")
        org_row = (55, "Acme Corp", "acme", None, "About")
        script = [
            (10, "r@example.com", "recruiter", "active"),  # current_user
            (1,),                                          # _recruiter_in_organization -> member
            org_row,                                       # UPDATE returning
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/organizations/55",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Acme Corp"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        self.assertEqual(resp.json()["organization_id"], 55)

    def test_admin_can_patch_any_organization(self) -> None:
        token = _token(1, "admin")
        org_row = (55, "Acme Corp", "acme", None, "About")
        script = [
            (1, "a@example.com", "admin", "active"),  # current_user
            org_row,                                  # UPDATE returning (no membership check for admin)
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/organizations/55",
                headers={"Authorization": f"Bearer {token}"},
                json={"name": "Acme Corp"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)


class AdminProfileLeakageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_admin_cannot_read_candidate_profile_route(self) -> None:
        token = _token(1, "admin")
        script = [(1, "a@example.com", "admin", "active")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get(
                "/api/candidate/profile",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "forbidden")

    def test_admin_cannot_read_recruiter_profile_route(self) -> None:
        token = _token(1, "admin")
        script = [(1, "a@example.com", "admin", "active")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get(
                "/api/recruiter/profile",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 403, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "forbidden")


class ExistingOwnershipRegressionTests(unittest.TestCase):
    """Re-check ownership guards already present in earlier slices."""

    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_candidate_cannot_update_other_candidate_resume(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _resume_row(resume_id=7, candidate_user_id=99),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/candidate/resumes/7",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": "Hijack",
                    "location": "ha_noi",
                    "job_type": "remote",
                    "seniority": "mid",
                    "education": "dai_hoc",
                },
            )
        self.assertEqual(resp.status_code, 403, resp.text)

    def test_recruiter_cannot_update_other_recruiter_job(self) -> None:
        token = _token(10, "recruiter")
        script = [
            (10, "r@example.com", "recruiter", "active"),
            _job_row(job_id=5, recruiter_user_id=99),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.patch(
                "/api/jobs/5",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "organization_id": 100,
                    "title": "Hijack",
                    "location": "ha_noi",
                    "job_type": "remote",
                    "seniority": "mid",
                    "education": "dai_hoc",
                },
            )
        self.assertEqual(resp.status_code, 403, resp.text)


if __name__ == "__main__":
    unittest.main()
