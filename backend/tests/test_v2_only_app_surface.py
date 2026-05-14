import unittest

from fastapi.testclient import TestClient

from main import app


class AppSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_openapi_contains_search_v2_catalog_matching_auth_system_and_root(self):
        schema = self.client.get("/openapi.json").json()
        paths = set(schema["paths"])

        self.assertIn("/api/jobs", paths)
        self.assertIn("/api/cvs", paths)
        self.assertIn("/api/candidates", paths)
        self.assertIn("/api/job", paths)
        self.assertIn("/api/job/my", paths)
        self.assertIn("/api/job/search", paths)
        self.assertIn("/api/job/search/filters", paths)
        self.assertIn("/api/job/{job_id}", paths)
        self.assertIn("/api/cv", paths)
        self.assertIn("/api/cv/my", paths)
        self.assertIn("/api/cv/upload", paths)
        self.assertIn("/api/cv/search", paths)
        self.assertIn("/api/cv/{cv_id}", paths)
        self.assertIn("/api/cvs", paths)
        self.assertIn("/api/cvs/my", paths)
        self.assertIn("/api/cvs/{cv_id}", paths)
        self.assertIn("/api/employer/requests", paths)
        self.assertIn("/api/employer/requests/my", paths)
        self.assertIn("/api/employer/requests/{request_id}", paths)
        self.assertIn("/api/applications", paths)
        self.assertIn("/api/applications/me", paths)
        self.assertIn("/api/applications/{application_id}/status", paths)
        self.assertIn("/api/job/{job_id}/applications", paths)
        self.assertIn("/api/v2/prototype/matching/job/{job_id}/run", paths)
        self.assertIn("/api/v2/prototype/matching/cv/{cv_id}/run", paths)
        self.assertIn("/api/v2/prototype/matching-hybrid/job/{job_id}/run", paths)
        self.assertIn("/api/v2/prototype/matching-hybrid/cv/{cv_id}/run", paths)
        self.assertIn("/api/v2/prototype/catalog/jobs", paths)
        self.assertIn("/api/v2/prototype/catalog/cvs", paths)
        self.assertIn("/api/auth/register", paths)
        self.assertIn("/api/auth/login", paths)
        self.assertIn("/api/auth/me", paths)
        self.assertIn("/api/health", paths)
        self.assertIn("/", paths)

        unexpected = sorted(
            path
            for path in paths
            if path not in {"/", "/api/health"}
            and path not in {"/api/jobs", "/api/cvs", "/api/candidates"}
            and not path.startswith("/api/job")
            and not path.startswith("/api/cv")
            and not path.startswith("/api/employer/requests")
            and not path.startswith("/api/applications")
            and not path.startswith("/api/auth/")
            and not path.startswith("/api/v2/prototype/catalog/")
            and not path.startswith("/api/v2/prototype/matching/")
            and not path.startswith("/api/v2/prototype/matching-hybrid/")
        )
        self.assertEqual(unexpected, [])

    def test_openapi_tags_are_expected_app_surface(self):
        schema = self.client.get("/openapi.json").json()
        tag_names = {tag["name"] for tag in schema["tags"]}

        self.assertEqual(
            tag_names,
            {
                "auth",
                "catalog-v2-prototype",
                "matching-v2-prototype",
                "matching-v2-hybrid-prototype",
                "normal-search",
                "normal-job",
                "normal-cv",
                "normal-cv-management",
                "normal-employer-request-management",
                "normal-applications",
                "system",
                "root",
            },
        )


if __name__ == "__main__":
    unittest.main()
