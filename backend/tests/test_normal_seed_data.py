import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "backend" / "db_v2" / "seeds" / "004_normal_jobs_cvs_seed.sql"
MIGRATION_006_PATH = REPO_ROOT / "backend" / "db_v2" / "migrations" / "006_normal_multi_industry_fields.sql"
MIGRATION_008_PATH = REPO_ROOT / "backend" / "db_v2" / "migrations" / "008_remove_normal_embeddings_translation.sql"
MIGRATION_009_PATH = REPO_ROOT / "backend" / "db_v2" / "migrations" / "009_v2_normal_sync_links.sql"


class NormalSeedDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SEED_PATH.read_text(encoding="utf-8")
        cls.migration_006 = MIGRATION_006_PATH.read_text(encoding="utf-8")
        cls.migration_008 = MIGRATION_008_PATH.read_text(encoding="utf-8")
        cls.migration_009 = MIGRATION_009_PATH.read_text(encoding="utf-8")

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
        display_industries = {
            "Công nghệ thông tin",
            "Marketing",
            "Kinh doanh",
            "Kế toán - Tài chính",
            "Nhân sự",
            "Giáo dục",
            "Y tế",
            "Thiết kế sáng tạo",
            "Logistics",
            "Dịch vụ khách hàng",
            "Sản xuất",
            "Pháp lý",
            "Bán lẻ",
            "Khách sạn - Du lịch",
        }
        for industry in display_industries:
            self.assertIn(industry, self.sql)
        normalized_industries = {
            "information_technology",
            "accounting_finance",
            "sales",
            "marketing",
            "human_resources",
            "education",
            "healthcare",
            "design_creative",
            "customer_service",
            "logistics_supply_chain",
            "manufacturing",
            "retail",
            "legal",
            "hospitality_tourism",
        }
        for industry in normalized_industries:
            self.assertIn(industry, self.sql)
        self.assertGreaterEqual(len(re.findall(r"91000000-0000-0000-0000-", self.sql)), 16)
        self.assertIn("'published'", self.sql)
        self.assertIn("'public'", self.sql)
        self.assertIn("archived = false", self.sql)

    def test_seed_records_reference_demo_users(self):
        self.assertIn("demo.recruiter@example.com", self.sql)
        self.assertIn("demo.candidate@example.com", self.sql)
        self.assertIn("Nhà tuyển dụng Demo", self.sql)
        self.assertIn("Ứng viên Demo", self.sql)
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

    def test_seed_demo_content_is_vietnamese_with_normalized_enum_keys(self):
        self.assertIn("Lập trình viên Backend Python", self.sql)
        self.assertIn("Nguyễn Văn An", self.sql)
        self.assertIn("Có kinh nghiệm xây dựng API", self.sql)
        self.assertIn("'middle'", self.sql)
        self.assertIn("'bachelor'", self.sql)
        self.assertIn("software_engineering", self.sql)
        self.assertIn("fulltime", self.sql)

    def test_seed_has_no_normal_translation_or_embedding_data(self):
        forbidden_terms = [
            "translated",
            "translationWarnings",
            "translatedText",
            "translation_model_unavailable",
            "embedding",
            "embedding_text",
            "embedding_vector",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, self.sql)

    def test_normal_migrations_do_not_create_normal_embedding_columns(self):
        self.assertNotIn("ADD COLUMN IF NOT EXISTS embedding", self.migration_006)
        self.assertNotIn("jobs_embedding_gin_idx ON jobs", self.migration_006)
        self.assertNotIn("cvs_embedding_gin_idx ON cvs", self.migration_006)
        self.assertIn("ALTER TABLE jobs DROP COLUMN IF EXISTS embedding", self.migration_008)
        self.assertIn("ALTER TABLE cvs DROP COLUMN IF EXISTS embedding", self.migration_008)

    def test_v2_sync_migration_links_normal_rows_without_normal_embeddings(self):
        self.assertIn("normal_cv_id UUID UNIQUE REFERENCES cvs(id) ON DELETE CASCADE", self.migration_009)
        self.assertIn("normal_job_id UUID UNIQUE REFERENCES jobs(id) ON DELETE CASCADE", self.migration_009)
        self.assertIn("prepared_text TEXT NOT NULL DEFAULT ''", self.migration_009)
        self.assertIn("prepared_text_en TEXT NOT NULL DEFAULT ''", self.migration_009)
        self.assertIn("translation_warnings JSONB NOT NULL DEFAULT '[]'::jsonb", self.migration_009)
        self.assertNotIn("ALTER TABLE cvs ADD COLUMN IF NOT EXISTS embedding", self.migration_009)
        self.assertNotIn("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS embedding", self.migration_009)


if __name__ == "__main__":
    unittest.main()
