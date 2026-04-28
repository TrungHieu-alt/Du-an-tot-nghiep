import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.application_service import ApplicationService


class ApplicationServiceDevPermissionsTest(unittest.IsolatedAsyncioTestCase):
    async def test_create_application_strict_mode_rejects_missing_candidate(self):
        os.environ["DEV_ALLOW_ALL_ACCOUNTS"] = "false"

        with patch("services.application_service.JobRepository.get_by_id", new=AsyncMock(return_value=SimpleNamespace(job_id=1))), \
             patch("services.application_service.CandidateRepository.get_by_user_id", new=AsyncMock(return_value=None)), \
             patch("services.application_service.CVRepository.get_by_id", new=AsyncMock(return_value=SimpleNamespace(cv_id=10, user_id=999))), \
             patch("services.application_service.ApplicationRepository.get_by_cv_job", new=AsyncMock(return_value=None)), \
             patch("services.application_service.ApplicationRepository.create", new=AsyncMock()):
            with self.assertRaisesRegex(ValueError, "Candidate not found"):
                await ApplicationService.create_application(job_id=1, candidate_id=123, cv_id=10, cover_letter="")

    async def test_create_application_dev_mode_allows_cross_role_and_cv_ownership(self):
        os.environ["DEV_ALLOW_ALL_ACCOUNTS"] = "true"

        created = SimpleNamespace(
            app_id=77,
            job_id=1,
            candidate_id=123,
            cv_id=10,
            status="pending",
            created_at="2026-01-01T00:00:00",
        )

        with patch("services.application_service.JobRepository.get_by_id", new=AsyncMock(return_value=SimpleNamespace(job_id=1))), \
             patch("services.application_service.CandidateRepository.get_by_user_id", new=AsyncMock(return_value=None)), \
             patch("services.application_service.CVRepository.get_by_id", new=AsyncMock(return_value=SimpleNamespace(cv_id=10, user_id=999))), \
             patch("services.application_service.ApplicationRepository.get_by_cv_job", new=AsyncMock(return_value=None)), \
             patch("services.application_service.ApplicationRepository.create", new=AsyncMock(return_value=created)):
            result = await ApplicationService.create_application(job_id=1, candidate_id=123, cv_id=10, cover_letter="")

        self.assertEqual(result["app_id"], 77)
        self.assertEqual(result["candidate_id"], 123)
        self.assertEqual(result["cv_id"], 10)


if __name__ == "__main__":
    unittest.main()

