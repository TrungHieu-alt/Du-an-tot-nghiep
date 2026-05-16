import unittest
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.main import app


class AppSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_openapi_contains_production_surface_and_no_prototype_routes(self):
        schema = self.client.get("/openapi.json").json()
        paths = set(schema["paths"])

        expected = {
            "/api/auth/register",
            "/api/auth/login",
            "/api/auth/logout",
            "/api/me",
            "/api/candidate/profile",
            "/api/candidate/resumes",
            "/api/candidate/resumes/{resume_id}",
            "/api/candidate/resumes/{resume_id}/activate",
            "/api/candidate/resumes/{resume_id}/archive",
            "/api/recruiter/profile",
            "/api/organizations",
            "/api/organizations/{organization_id}",
            "/api/jobs",
            "/api/jobs/{job_id}",
            "/api/jobs/{job_id}/publish",
            "/api/jobs/{job_id}/close",
            "/api/jobs/search",
            "/api/jobs/semantic-search",
            "/api/candidate/resumes/search",
            "/api/candidate/resumes/semantic-search",
            "/api/matching/jobs/{job_id}/run",
            "/api/matching/resumes/{resume_id}/run",
            "/api/documents",
            "/api/documents/{document_id}",
            "/api/documents/{document_id}/download-url",
            "/api/documents/{document_id}/parse-jobs/{parse_job_id}",
            "/api/documents/{document_id}/parse-jobs",
            "/api/applications",
            "/api/applications/{application_id}",
            "/api/applications/{application_id}/status",
            "/api/invites",
            "/api/invites/{invite_id}",
            "/api/invites/{invite_id}/accept",
            "/api/invites/{invite_id}/reject",
            "/api/notifications",
            "/api/notifications/{notification_id}/read",
            "/api/notifications/read-all",
            "/api/admin/users",
            "/api/admin/users/{user_id}",
            "/api/admin/documents",
            "/api/admin/parse-jobs",
            "/api/admin/applications",
            "/api/admin/invites",
            "/api/admin/notifications",
            "/api/admin/audit-logs",
        }
        for path in expected:
            self.assertIn(path, paths)
        self.assertIn("/api/health", paths)
        self.assertIn("/", paths)

        self.assertFalse(any(path.startswith("/api/v2/prototype/") for path in paths))

    def test_backend_uses_modular_package_entrypoint(self):
        self.assertEqual(app.title, "Job Matcher API")
        self.assertEqual(app.version, "3.0.0")

    def test_openapi_tags_are_app_tags(self):
        schema = self.client.get("/openapi.json").json()
        tag_names = {tag["name"] for tag in schema["tags"]}

        self.assertIn("auth", tag_names)
        self.assertIn("candidate", tag_names)
        self.assertIn("jobs", tag_names)
        self.assertIn("matching", tag_names)
        self.assertIn("admin", tag_names)
        self.assertNotIn("catalog-v2-prototype", tag_names)
        self.assertNotIn("matching-v2-prototype", tag_names)

    def test_matching_contract_has_required_fields_and_top_k_limit(self):
        schema = self.client.get("/openapi.json").json()
        matching_request = schema["components"]["schemas"]["MatchingRequest"]
        self.assertEqual(matching_request["properties"]["top_k"]["maximum"], 50)
        self.assertEqual(matching_request["properties"]["top_k"]["default"], 10)
        self.assertEqual(matching_request["properties"]["min_score"]["default"], 0.7)
        matching_response = schema["components"]["schemas"]["MatchingItem"]
        for field in [
            "score_breakdown",
            "exact_skill_overlap",
            "hard_filter_notes",
            "missing_embedding_notes",
            "reasoning",
        ]:
            self.assertIn(field, matching_response["properties"])
        score_breakdown = schema["components"]["schemas"]["MatchingScoreBreakdown"]
        self.assertIn("bonus_exact_skill", score_breakdown["properties"])
        self.assertIn("penalty_missing_required", score_breakdown["properties"])
        runtime_schema = schema["components"]["schemas"]["MatchingRuntime"]
        for field in [
            "retrieval_ms",
            "filter_ms",
            "scoring_ms",
            "rerank_applied",
            "warnings",
            "candidates_total",
            "candidates_after_filter",
        ]:
            self.assertIn(field, runtime_schema["properties"])


if __name__ == "__main__":
    unittest.main()
