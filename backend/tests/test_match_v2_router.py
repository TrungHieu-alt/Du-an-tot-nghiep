import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from matching_v2.models import MatchItemV2, RunMatchingV2Response
from routers.match_v2_router import router


class MatchV2RouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)

    def test_run_job_success(self):
        payload = RunMatchingV2Response(
            anchor_type="job",
            anchor_id=2003,
            total_candidates=5,
            total_after_filter=1,
            total_returned=1,
            runtime_ms_total=10.1,
            runtime_ms_filter=1.1,
            runtime_ms_scoring=7.2,
            runtime_ms_sort=0.3,
            matches=[
                MatchItemV2(
                    rank=1,
                    cv_id=1003,
                    job_id=2003,
                    final_score=0.965,
                    title_score=1.0,
                    skills_score=0.95,
                    req_exp_score=0.9,
                    req_summary_score=0.9,
                    reasoning="ok",
                )
            ],
        )

        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_job") as mock_run:
            mock_run.return_value = payload
            res = self.client.post(
                "/api/v2/prototype/matching/job/2003/run",
                json={"top_k": 10, "min_score": 0.7},
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["anchor_type"], "job")
        self.assertIn("runtime_ms_total", data)
        self.assertEqual(data["matches"][0]["rank"], 1)

    def test_run_cv_not_found(self):
        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_cv", side_effect=ValueError("cv_id 999 not found in candidate_profiles_v2")):
            res = self.client.post(
                "/api/v2/prototype/matching/cv/999/run",
                json={"top_k": 10, "min_score": 0.7},
            )

        self.assertEqual(res.status_code, 404)

    def test_invalid_request_validation(self):
        res = self.client.post(
            "/api/v2/prototype/matching/job/2003/run",
            json={"top_k": 0, "min_score": 1.2},
        )
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
