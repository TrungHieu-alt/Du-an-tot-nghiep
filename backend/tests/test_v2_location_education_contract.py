import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DB_V2 = REPO_ROOT / "backend" / "db_v2"
OLD_VALUES = {
    "ha_noi",
    "tp_hcm",
    "da_nang",
    "dai_hoc",
    "thac_si",
    "tien_si",
    "lop_12",
    "lop_9",
}
NEW_LOCATIONS = {"Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng"}
NEW_EDUCATIONS = {"high_school", "bachelor", "master", "phd"}


class V2LocationEducationContractTests(unittest.TestCase):
    def test_v2_seed_and_scenario_data_do_not_create_old_values(self):
        paths = [
            DB_V2 / "seed_orm.py",
            DB_V2 / "scenario" / "dataset.json",
            DB_V2 / "scenario" / "schema.json",
            DB_V2 / "scenarios" / "matching_v2_slice_6b.json",
            DB_V2 / "scenarios" / "matching_v2_slice_6b.schema.json",
            *sorted((DB_V2 / "seeds").glob("*.sql")),
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for old in OLD_VALUES:
                self.assertNotIn(old, text, f"{path} still contains old V2 value {old}")

    def test_v2_initial_and_forward_migrations_define_new_constraints(self):
        initial = (DB_V2 / "migrations" / "001_init.sql").read_text(encoding="utf-8")
        forward = (DB_V2 / "migrations" / "010_v2_location_education_contract.sql").read_text(encoding="utf-8")

        for value in NEW_LOCATIONS | NEW_EDUCATIONS:
            self.assertIn(value, initial)
            self.assertIn(value, forward)

        self.assertNotIn("CHECK (location IN ('ha_noi'", initial)
        self.assertNotIn("CHECK (education IN ('lop_9'", initial)
        self.assertIn("DROP CONSTRAINT IF EXISTS candidate_profiles_v2_location_chk", forward)
        self.assertIn("DROP CONSTRAINT IF EXISTS job_posts_v2_education_chk", forward)

    def test_matching_filters_use_new_education_rank_constants(self):
        filters = (REPO_ROOT / "backend" / "matching_v2" / "filters.py").read_text(encoding="utf-8")
        self.assertIn('"unknown": 0', filters)
        self.assertIn('"high_school": 1', filters)
        self.assertIn('"bachelor": 2', filters)
        self.assertIn('"master": 3', filters)
        self.assertIn('"phd": 4', filters)
        for old in {"lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si"}:
            self.assertNotIn(old, filters)


if __name__ == "__main__":
    unittest.main()
