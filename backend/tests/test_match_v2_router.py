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

    def _payload(self, anchor_type: str, anchor_id: int) -> RunMatchingV2Response:
        return RunMatchingV2Response(
            anchor_type=anchor_type,
            anchor_id=anchor_id,
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

    def _assert_response_contract(self, data: dict) -> None:
        response_fields = {
            "anchor_type",
            "anchor_id",
            "total_candidates",
            "total_after_filter",
            "total_returned",
            "runtime_ms_total",
            "runtime_ms_filter",
            "runtime_ms_scoring",
            "runtime_ms_sort",
            "matches",
        }
        match_fields = {
            "rank",
            "cv_id",
            "job_id",
            "final_score",
            "title_score",
            "skills_score",
            "req_exp_score",
            "req_summary_score",
            "reasoning",
        }

        self.assertTrue(response_fields.issubset(data.keys()))
        self.assertEqual(len(data["matches"]), 1)
        self.assertTrue(match_fields.issubset(data["matches"][0].keys()))

    def test_run_job_success(self):
        payload = self._payload(anchor_type="job", anchor_id=2003)

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
        self.assertEqual(data["anchor_id"], 2003)
        self._assert_response_contract(data)
        self.assertEqual(data["matches"][0]["rank"], 1)
        self.assertEqual(data["matches"][0]["cv_id"], 1003)
        self.assertEqual(data["matches"][0]["job_id"], 2003)
        mock_run.assert_called_once_with(
            conn=conn,
            job_id=2003,
            top_k=10,
            min_score=0.7,
        )

    def test_run_cv_success(self):
        payload = self._payload(anchor_type="cv", anchor_id=1003)

        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_cv") as mock_run:
            mock_run.return_value = payload
            res = self.client.post(
                "/api/v2/prototype/matching/cv/1003/run",
                json={"top_k": 10, "min_score": 0.7},
            )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["anchor_type"], "cv")
        self.assertEqual(data["anchor_id"], 1003)
        self._assert_response_contract(data)
        self.assertEqual(data["matches"][0]["cv_id"], 1003)
        self.assertEqual(data["matches"][0]["job_id"], 2003)
        mock_run.assert_called_once_with(
            conn=conn,
            cv_id=1003,
            top_k=10,
            min_score=0.7,
        )

    def test_run_job_defaults_when_body_omitted(self):
        payload = self._payload(anchor_type="job", anchor_id=2003)

        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_job") as mock_run:
            mock_run.return_value = payload
            res = self.client.post("/api/v2/prototype/matching/job/2003/run")

        self.assertEqual(res.status_code, 200)
        mock_run.assert_called_once_with(
            conn=conn,
            job_id=2003,
            top_k=10,
            min_score=0.7,
        )

    def test_run_cv_not_found(self):
        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_cv", side_effect=ValueError("cv_id 999 not found in candidate_profiles_v2")):
            res = self.client.post(
                "/api/v2/prototype/matching/cv/999/run",
                json={"top_k": 10, "min_score": 0.7},
            )

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {"detail": "cv not found"})

    def test_run_job_not_found(self):
        conn = Mock()
        with patch("routers.match_v2_router.get_connection", return_value=conn), \
             patch("routers.match_v2_router.run_for_job", side_effect=ValueError("job_id 999 not found in job_posts_v2")):
            res = self.client.post(
                "/api/v2/prototype/matching/job/999/run",
                json={"top_k": 10, "min_score": 0.7},
            )

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {"detail": "job not found"})

    def test_invalid_top_k_is_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/matching/job/2003/run",
            json={"top_k": 0, "min_score": 0.7},
        )
        self.assertEqual(res.status_code, 422)

    def test_invalid_min_score_is_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/matching/job/2003/run",
            json={"top_k": 10, "min_score": 1.2},
        )
        self.assertEqual(res.status_code, 422)

    def test_openapi_contract(self):
        schema = self.client.get("/openapi.json").json()
        paths = schema["paths"]
        self.assertEqual(
            {
                path
                for path in paths
                if path.startswith("/api/v2/prototype/matching/")
            },
            {
                "/api/v2/prototype/matching/job/{job_id}/run",
                "/api/v2/prototype/matching/cv/{cv_id}/run",
            },
        )
        request_schema = schema["components"]["schemas"]["RunMatchingV2Request"]
        self.assertEqual(request_schema["properties"]["top_k"]["minimum"], 1)
        self.assertEqual(request_schema["properties"]["top_k"]["maximum"], 10)
        self.assertEqual(request_schema["properties"]["min_score"]["minimum"], 0.0)
        self.assertEqual(request_schema["properties"]["min_score"]["maximum"], 1.0)
        response_props = schema["components"]["schemas"]["RunMatchingV2Response"]["properties"]
        self.assertIn("runtime_ms_total", response_props)
        self.assertIn("runtime_ms_filter", response_props)
        self.assertIn("runtime_ms_scoring", response_props)
        self.assertIn("runtime_ms_sort", response_props)
        match_props = schema["components"]["schemas"]["MatchItemV2Response"]["properties"]
        self.assertIn("req_summary_score", match_props)
        self.assertIn("reasoning", match_props)
        job_responses = paths["/api/v2/prototype/matching/job/{job_id}/run"]["post"]["responses"]
        self.assertIn("404", job_responses)


if __name__ == "__main__":
    unittest.main()
