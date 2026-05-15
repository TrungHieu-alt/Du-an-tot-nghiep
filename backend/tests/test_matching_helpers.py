import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.modules.matching.filters import passes_hard_filter
from jobconnect.modules.matching.models import CandidateProfileMatch, JobPostMatch
from jobconnect.modules.matching.scoring import compute_final_score, compute_skills_score


class MatchingHelperTests(unittest.TestCase):
    def test_hard_filter_accepts_remote_matching_pair(self):
        job = JobPostMatch(
            job_id=1,
            title="Backend Engineer",
            skills=("python", "fastapi"),
            requirement="Build APIs",
            location="ha_noi",
            job_type="remote",
            seniority="mid",
            education="dai_hoc",
            required_certifications=(),
        )
        resume = CandidateProfileMatch(
            cv_id=1,
            title="Backend Engineer",
            skills=("python", "fastapi"),
            summary="API engineer",
            experience="Built FastAPI services",
            location="tp_hcm",
            job_type="remote",
            seniority="mid",
            education="thac_si",
            certifications=(),
        )

        self.assertTrue(passes_hard_filter(job, resume))

    def test_score_formula_matches_production_weights(self):
        skills = compute_skills_score(semantic=0.5, exact=1.0)

        self.assertEqual(skills, 0.7)
        self.assertAlmostEqual(
            compute_final_score(title=1.0, skills=skills, req_exp=0.5, req_summary=0.25),
            0.72,
        )


if __name__ == "__main__":
    unittest.main()
