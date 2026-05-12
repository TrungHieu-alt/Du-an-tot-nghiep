import unittest

from fastapi.testclient import TestClient

from main import app


class V2OnlyAppSurfaceTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_openapi_contains_only_v2_catalog_matching_system_and_root(self):
        schema = self.client.get("/openapi.json").json()
        paths = set(schema["paths"])

        self.assertIn("/api/v2/prototype/matching/job/{job_id}/run", paths)
        self.assertIn("/api/v2/prototype/matching/cv/{cv_id}/run", paths)
        self.assertIn("/api/v2/prototype/catalog/jobs", paths)
        self.assertIn("/api/v2/prototype/catalog/cvs", paths)
        self.assertIn("/api/health", paths)
        self.assertIn("/", paths)

        unexpected = sorted(
            path
            for path in paths
            if path not in {"/", "/api/health"}
            and not path.startswith("/api/v2/prototype/catalog/")
            and not path.startswith("/api/v2/prototype/matching/")
        )
        self.assertEqual(unexpected, [])

    def test_openapi_tags_are_v2_only(self):
        schema = self.client.get("/openapi.json").json()
        tag_names = {tag["name"] for tag in schema["tags"]}

        self.assertEqual(
            tag_names,
            {"catalog-v2-prototype", "matching-v2-prototype", "system", "root"},
        )


if __name__ == "__main__":
    unittest.main()
