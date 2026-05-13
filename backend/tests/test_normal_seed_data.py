import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "backend" / "db_v2" / "seeds" / "004_normal_jobs_cvs_seed.sql"


class NormalSeedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SEED_PATH.read_text(encoding="utf-8")

    def test_seed_file_exists_and_targets_normal_tables_only(self):
        self.assertTrue(SEED_PATH.exists())
        self.assertIn("INSERT INTO users", self.sql)
        self.assertIn("INSERT INTO jobs", self.sql)
        self.assertIn("INSERT INTO cvs", self.sql)
        self.assertNotIn("job_posts_v2", self.sql)
        self.assertNotIn("candidate_profiles_v2", self.sql)
        self.assertNotIn("backend/db_v2/scenario", self.sql)
        self.assertNotIn("backend/db_v2/scenarios", self.sql)

    def test_seed_is_idempotent(self):
        self.assertGreaterEqual(self.sql.count("ON CONFLICT (id) DO UPDATE"), 3)

    def test_seed_jobs_are_public_and_multi_industry(self):
        industries = {
            "Information Technology",
            "Marketing",
            "Sales",
            "Accounting",
            "Finance",
            "Human Resources",
            "Education",
            "Healthcare",
            "Design",
            "Logistics",
            "Customer Service",
            "Manufacturing",
            "Legal",
            "Real Estate",
            "Hospitality",
        }
        for industry in industries:
            self.assertIn(industry, self.sql)
        self.assertGreaterEqual(len(re.findall(r"91000000-0000-0000-0000-", self.sql)), 16)
        self.assertIn("'published'", self.sql)
        self.assertIn("'public'", self.sql)
        self.assertIn("archived = false", self.sql)

    def test_seed_records_reference_demo_users(self):
        self.assertIn("demo.recruiter@example.com", self.sql)
        self.assertIn("demo.candidate@example.com", self.sql)
        self.assertIn("99999999-9999-9999-9999-999999999991", self.sql)
        self.assertIn("99999999-9999-9999-9999-999999999992", self.sql)

    def test_seed_cvs_use_normal_cv_shape(self):
        self.assertGreaterEqual(len(re.findall(r"92000000-0000-0000-0000-", self.sql)), 8)
        self.assertIn("target_role", self.sql)
        self.assertIn("experiences", self.sql)
        self.assertIn("projects", self.sql)
        self.assertIn("certifications", self.sql)
        self.assertIn("visibility", self.sql)
        self.assertIn("archived", self.sql)


if __name__ == "__main__":
    unittest.main()
