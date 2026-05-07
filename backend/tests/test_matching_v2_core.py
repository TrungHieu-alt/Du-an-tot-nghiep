import unittest
from unittest.mock import patch

from matching_v2.filters import passes_hard_filter
from matching_v2.models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
)
from matching_v2.runner import _score_pair, run_for_job
from matching_v2.scoring import compute_final_score, compute_skills_score


class MatchingV2CoreTests(unittest.TestCase):
    def test_hard_filters(self):
        job_remote = JobPostV2(
            job_id=1,
            title="x",
            skills=("python",),
            requirement="x",
            location="ha_noi",
            job_type="remote",
            seniority="senior",
            education="dai_hoc",
            required_certifications=(),
        )
        cv_remote_other_location = CandidateProfileV2(
            cv_id=1,
            title="x",
            skills=("python",),
            summary="x",
            experience="x",
            location="tp_hcm",
            job_type="remote",
            seniority="senior",
            education="thac_si",
            certifications=(),
        )
        self.assertTrue(passes_hard_filter(job_remote, cv_remote_other_location))

        job_fulltime = JobPostV2(
            job_id=2,
            title="x",
            skills=("python",),
            requirement="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="dai_hoc",
            required_certifications=("aws",),
        )
        cv_pass = CandidateProfileV2(
            cv_id=2,
            title="x",
            skills=("python", "sql"),
            summary="x",
            experience="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="thac_si",
            certifications=("aws", "cka"),
        )
        cv_bad_location = CandidateProfileV2(
            cv_id=3,
            title="x",
            skills=("python",),
            summary="x",
            experience="x",
            location="tp_hcm",
            job_type="fulltime",
            seniority="senior",
            education="thac_si",
            certifications=("aws",),
        )
        cv_bad_education = CandidateProfileV2(
            cv_id=4,
            title="x",
            skills=("python",),
            summary="x",
            experience="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="lop_12",
            certifications=("aws",),
        )
        cv_bad_cert = CandidateProfileV2(
            cv_id=5,
            title="x",
            skills=("python",),
            summary="x",
            experience="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="thac_si",
            certifications=(),
        )

        self.assertTrue(passes_hard_filter(job_fulltime, cv_pass))
        self.assertFalse(passes_hard_filter(job_fulltime, cv_bad_location))
        self.assertFalse(passes_hard_filter(job_fulltime, cv_bad_education))
        self.assertFalse(passes_hard_filter(job_fulltime, cv_bad_cert))

    def test_scoring_formulas(self):
        self.assertAlmostEqual(compute_skills_score(0.5, 0.25), 0.4)
        self.assertAlmostEqual(compute_final_score(1.0, 0.4, 0.5, 0.25), 0.615)

    def test_missing_embeddings_score_zero_no_crash(self):
        job = JobPostV2(
            job_id=1,
            title="x",
            skills=("python",),
            requirement="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="dai_hoc",
            required_certifications=(),
        )
        cv = CandidateProfileV2(
            cv_id=1,
            title="x",
            skills=("python",),
            summary="x",
            experience="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="dai_hoc",
            certifications=(),
        )
        job_emb = JobEmbeddingsV2(job_id=1, emb_title=None, emb_skills=[1.0, 0.0], emb_requirement=None)
        cv_emb = CandidateEmbeddingsV2(cv_id=1, emb_title=[1.0, 0.0], emb_skills=None, emb_summary=None, emb_experience=[0.0, 1.0])

        scores, missing = _score_pair(job, job_emb, cv, cv_emb)
        self.assertEqual(scores["title_score"], 0.0)
        self.assertEqual(scores["req_exp_score"], 0.0)
        self.assertEqual(scores["req_summary_score"], 0.0)
        self.assertIn("jd.emb_title", missing)
        self.assertIn("jd.emb_requirement", missing)
        self.assertIn("cv.emb_skills", missing)
        self.assertIn("cv.emb_summary", missing)

    def test_sorting_tie_break_deterministic_by_cv_id(self):
        job = JobPostV2(
            job_id=99,
            title="x",
            skills=("python",),
            requirement="x",
            location="ha_noi",
            job_type="fulltime",
            seniority="senior",
            education="dai_hoc",
            required_certifications=(),
        )
        c1 = CandidateProfileV2(2, "x", ("python",), "x", "x", "ha_noi", "fulltime", "senior", "dai_hoc", ())
        c2 = CandidateProfileV2(1, "x", ("python",), "x", "x", "ha_noi", "fulltime", "senior", "dai_hoc", ())
        equal_emb = JobEmbeddingsV2(job_id=99, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_requirement=[1.0, 0.0])
        c1_emb = CandidateEmbeddingsV2(cv_id=2, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_summary=[1.0, 0.0], emb_experience=[1.0, 0.0])
        c2_emb = CandidateEmbeddingsV2(cv_id=1, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_summary=[1.0, 0.0], emb_experience=[1.0, 0.0])

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=equal_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[c1, c2]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={1: c2_emb, 2: c1_emb}):
            response = run_for_job(conn=object(), job_id=99, top_k=10, min_score=0.0)

        self.assertEqual([m.cv_id for m in response.matches], [1, 2])


if __name__ == "__main__":
    unittest.main()
