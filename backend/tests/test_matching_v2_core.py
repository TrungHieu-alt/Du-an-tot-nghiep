import unittest
from unittest.mock import patch

from matching_v2.filters import (
    passes_certifications,
    passes_education,
    passes_hard_filter,
    passes_job_type,
    passes_location,
    passes_seniority,
)
from matching_v2.models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
)
from matching_v2.runner import _score_pair, run_for_cv, run_for_job
from matching_v2.scoring import compute_final_score, compute_skills_score, cosine_similarity


class MatchingV2CoreTests(unittest.TestCase):
    def _job(self, **overrides) -> JobPostV2:
        data = {
            "job_id": 10,
            "title": "Backend Engineer",
            "skills": ("python", "sql", "aws"),
            "requirement": "Build APIs and operate cloud services",
            "location": "ha_noi",
            "job_type": "fulltime",
            "seniority": "senior",
            "education": "dai_hoc",
            "required_certifications": ("aws",),
        }
        data.update(overrides)
        return JobPostV2(**data)

    def _cv(self, **overrides) -> CandidateProfileV2:
        data = {
            "cv_id": 20,
            "title": "Backend Engineer",
            "skills": ("python", "sql", "aws"),
            "summary": "Senior backend engineer",
            "experience": "Built APIs and cloud services",
            "location": "ha_noi",
            "job_type": "fulltime",
            "seniority": "senior",
            "education": "thac_si",
            "certifications": ("aws", "cka"),
        }
        data.update(overrides)
        return CandidateProfileV2(**data)

    def _job_emb(self, **overrides) -> JobEmbeddingsV2:
        data = {
            "job_id": 10,
            "emb_title": [1.0, 0.0],
            "emb_skills": [1.0, 1.0],
            "emb_requirement": [0.0, 1.0],
        }
        data.update(overrides)
        return JobEmbeddingsV2(**data)

    def _cv_emb(self, **overrides) -> CandidateEmbeddingsV2:
        data = {
            "cv_id": 20,
            "emb_title": [1.0, 0.0],
            "emb_skills": [1.0, 0.0],
            "emb_summary": [0.0, 1.0],
            "emb_experience": [0.0, 1.0],
        }
        data.update(overrides)
        return CandidateEmbeddingsV2(**data)

    def test_job_type_must_match(self):
        self.assertTrue(passes_job_type(self._job(job_type="fulltime"), self._cv(job_type="fulltime")))
        self.assertFalse(passes_job_type(self._job(job_type="fulltime"), self._cv(job_type="parttime")))

    def test_remote_jd_bypasses_location(self):
        job = self._job(job_type="remote", location="ha_noi")
        cv = self._cv(job_type="remote", location="tp_hcm")
        self.assertTrue(passes_location(job, cv))
        self.assertTrue(passes_hard_filter(job, cv))

    def test_non_remote_jd_requires_exact_location(self):
        job = self._job(job_type="fulltime", location="ha_noi")
        self.assertTrue(passes_location(job, self._cv(job_type="fulltime", location="ha_noi")))
        self.assertFalse(passes_location(job, self._cv(job_type="fulltime", location="tp_hcm")))
        self.assertFalse(passes_hard_filter(job, self._cv(job_type="fulltime", location="tp_hcm")))

    def test_seniority_exact_match(self):
        self.assertTrue(passes_seniority(self._job(seniority="senior"), self._cv(seniority="senior")))
        self.assertFalse(passes_seniority(self._job(seniority="senior"), self._cv(seniority="mid")))

    def test_education_hierarchy_pass_and_fail(self):
        job = self._job(education="dai_hoc")
        self.assertTrue(passes_education(job, self._cv(education="dai_hoc")))
        self.assertTrue(passes_education(job, self._cv(education="thac_si")))
        self.assertFalse(passes_education(job, self._cv(education="lop_12")))

    def test_required_certifications_subset_pass_and_fail(self):
        job = self._job(required_certifications=("aws", "cka"))
        self.assertTrue(passes_certifications(job, self._cv(certifications=("aws", "cka", "pmp"))))
        self.assertFalse(passes_certifications(job, self._cv(certifications=("aws",))))
        self.assertTrue(passes_certifications(self._job(required_certifications=()), self._cv(certifications=())))

    def test_score_pair_components_are_deterministic(self):
        scores_a, missing_a = _score_pair(self._job(), self._job_emb(), self._cv(), self._cv_emb())
        scores_b, missing_b = _score_pair(self._job(), self._job_emb(), self._cv(), self._cv_emb())

        expected_title = cosine_similarity([1.0, 0.0], [1.0, 0.0])
        expected_semantic_skills = cosine_similarity([1.0, 1.0], [1.0, 0.0])
        expected_skills = (0.6 * expected_semantic_skills) + (0.4 * 1.0)
        expected_req_exp = cosine_similarity([0.0, 1.0], [0.0, 1.0])
        expected_req_summary = cosine_similarity([0.0, 1.0], [0.0, 1.0])
        expected_final = (
            0.35 * expected_title
            + 0.35 * expected_skills
            + 0.20 * expected_req_exp
            + 0.10 * expected_req_summary
        )

        self.assertEqual(missing_a, [])
        self.assertEqual(missing_b, [])
        self.assertEqual(scores_a, scores_b)
        self.assertAlmostEqual(scores_a["title_score"], expected_title)
        self.assertAlmostEqual(scores_a["skills_score"], expected_skills)
        self.assertAlmostEqual(scores_a["req_exp_score"], expected_req_exp)
        self.assertAlmostEqual(scores_a["req_summary_score"], expected_req_summary)
        self.assertAlmostEqual(scores_a["final_score"], expected_final)

    def test_scoring_formula_helpers_are_explicit(self):
        self.assertAlmostEqual(compute_skills_score(0.5, 0.25), 0.6 * 0.5 + 0.4 * 0.25)
        self.assertAlmostEqual(
            compute_final_score(1.0, 0.4, 0.5, 0.25),
            0.35 * 1.0 + 0.35 * 0.4 + 0.20 * 0.5 + 0.10 * 0.25,
        )

    def test_negative_cosine_similarity_is_clamped_to_zero(self):
        self.assertEqual(cosine_similarity([1.0, 0.0], [-1.0, 0.0]), 0.0)

    def test_negative_semantic_signals_do_not_make_final_score_negative(self):
        job = self._job(skills=("python",))
        cv = self._cv(skills=("java",), certifications=("aws",))
        job_emb = self._job_emb(
            emb_title=[1.0, 0.0],
            emb_skills=[1.0, 0.0],
            emb_requirement=[1.0, 0.0],
        )
        cv_emb = self._cv_emb(
            emb_title=[-1.0, 0.0],
            emb_skills=[-1.0, 0.0],
            emb_summary=[-1.0, 0.0],
            emb_experience=[-1.0, 0.0],
        )

        scores, missing = _score_pair(job, job_emb, cv, cv_emb)

        self.assertEqual(missing, [])
        self.assertEqual(scores["title_score"], 0.0)
        self.assertEqual(scores["skills_score"], 0.0)
        self.assertEqual(scores["req_exp_score"], 0.0)
        self.assertEqual(scores["req_summary_score"], 0.0)
        self.assertEqual(scores["final_score"], 0.0)

    def test_missing_embeddings_score_zero_no_crash(self):
        job_emb = self._job_emb(emb_title=None, emb_requirement=None)
        cv_emb = self._cv_emb(emb_skills=None, emb_summary=None)

        scores, missing = _score_pair(self._job(), job_emb, self._cv(), cv_emb)
        self.assertEqual(scores["title_score"], 0.0)
        self.assertEqual(scores["req_exp_score"], 0.0)
        self.assertEqual(scores["req_summary_score"], 0.0)
        self.assertIn("jd.emb_title", missing)
        self.assertIn("jd.emb_requirement", missing)
        self.assertIn("cv.emb_skills", missing)
        self.assertIn("cv.emb_summary", missing)

    def test_missing_embedding_reasoning_mentions_missing_embedding(self):
        job = self._job()
        cv = self._cv(cv_id=20)
        job_emb = self._job_emb(emb_title=None)
        cv_emb = self._cv_emb()

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=job_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[cv]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={20: cv_emb}):
            response = run_for_job(conn=object(), job_id=10, top_k=10, min_score=0.0)

        self.assertEqual(response.matches[0].title_score, 0.0)
        self.assertIn("Missing embeddings for: jd.emb_title", response.matches[0].reasoning)

    def test_sorting_by_final_score_desc_then_cv_id_asc(self):
        job = self._job(job_id=99, skills=("python",))
        high = self._cv(cv_id=3, skills=("python",))
        low = self._cv(cv_id=1, skills=("python",))
        job_emb = self._job_emb(job_id=99)
        high_emb = self._cv_emb(cv_id=3)
        low_emb = self._cv_emb(cv_id=1, emb_title=[0.0, 1.0], emb_skills=[0.0, 1.0])

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=job_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[low, high]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={1: low_emb, 3: high_emb}):
            response = run_for_job(conn=object(), job_id=99, top_k=10, min_score=0.0)

        self.assertEqual([m.cv_id for m in response.matches], [3, 1])
        self.assertGreater(response.matches[0].final_score, response.matches[1].final_score)

    def test_sorting_tie_break_deterministic_by_cv_id(self):
        job = self._job(job_id=99, required_certifications=())
        c1 = self._cv(cv_id=2, certifications=())
        c2 = self._cv(cv_id=1, certifications=())
        equal_emb = JobEmbeddingsV2(job_id=99, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_requirement=[1.0, 0.0])
        c1_emb = CandidateEmbeddingsV2(cv_id=2, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_summary=[1.0, 0.0], emb_experience=[1.0, 0.0])
        c2_emb = CandidateEmbeddingsV2(cv_id=1, emb_title=[1.0, 0.0], emb_skills=[1.0, 0.0], emb_summary=[1.0, 0.0], emb_experience=[1.0, 0.0])

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=equal_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[c1, c2]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={1: c2_emb, 2: c1_emb}):
            response = run_for_job(conn=object(), job_id=99, top_k=10, min_score=0.0)

        self.assertEqual([m.cv_id for m in response.matches], [1, 2])

    def test_cv_to_job_tie_break_deterministic_by_job_id(self):
        cv = self._cv(cv_id=77, certifications=())
        j1 = self._job(job_id=2, required_certifications=())
        j2 = self._job(job_id=1, required_certifications=())
        cv_emb = self._cv_emb(cv_id=77)
        equal_job_emb = self._job_emb(job_id=1)

        with patch("matching_v2.runner.load_candidate", return_value=cv), \
             patch("matching_v2.runner.load_candidate_embeddings", return_value=cv_emb), \
             patch("matching_v2.runner.load_all_jobs", return_value=[j1, j2]), \
             patch("matching_v2.runner.load_all_job_embeddings", return_value={1: equal_job_emb, 2: equal_job_emb}):
            response = run_for_cv(conn=object(), cv_id=77, top_k=10, min_score=0.0)

        self.assertEqual([m.job_id for m in response.matches], [1, 2])

    def test_top_k_caps_return_count(self):
        job = self._job(job_id=99, required_certifications=())
        candidates = [self._cv(cv_id=i, certifications=()) for i in range(1, 13)]
        embeddings = {cv.cv_id: self._cv_emb(cv_id=cv.cv_id) for cv in candidates}

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=self._job_emb(job_id=99)), \
             patch("matching_v2.runner.load_all_candidates", return_value=candidates), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value=embeddings):
            response = run_for_job(conn=object(), job_id=99, top_k=99, min_score=0.0)

        self.assertEqual(response.total_returned, 10)
        self.assertEqual(len(response.matches), 10)

    def test_min_score_filters_at_inclusive_threshold(self):
        job = self._job(job_id=99, skills=("python",), required_certifications=())
        cv = self._cv(cv_id=1, skills=("python",), certifications=())
        job_emb = self._job_emb(job_id=99)
        cv_emb = self._cv_emb(cv_id=1, emb_title=[0.0, 1.0], emb_skills=[0.0, 1.0])

        scores, _missing = _score_pair(job, job_emb, cv, cv_emb)
        threshold = round(scores["final_score"], 6)

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=job_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[cv]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={1: cv_emb}):
            included = run_for_job(conn=object(), job_id=99, top_k=10, min_score=threshold)

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=job_emb), \
             patch("matching_v2.runner.load_all_candidates", return_value=[cv]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={1: cv_emb}):
            excluded = run_for_job(conn=object(), job_id=99, top_k=10, min_score=threshold + 0.000001)

        self.assertEqual([m.cv_id for m in included.matches], [1])
        self.assertEqual(excluded.matches, [])

    def test_no_candidates_and_all_filtered_out_are_deterministic(self):
        job = self._job(job_id=99)

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=self._job_emb(job_id=99)), \
             patch("matching_v2.runner.load_all_candidates", return_value=[]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={}):
            no_candidates = run_for_job(conn=object(), job_id=99, top_k=10, min_score=0.0)

        with patch("matching_v2.runner.load_job", return_value=job), \
             patch("matching_v2.runner.load_job_embeddings", return_value=self._job_emb(job_id=99)), \
             patch("matching_v2.runner.load_all_candidates", return_value=[self._cv(location="tp_hcm")]), \
             patch("matching_v2.runner.load_all_candidate_embeddings", return_value={20: self._cv_emb()}):
            all_filtered = run_for_job(conn=object(), job_id=99, top_k=10, min_score=0.0)

        self.assertEqual(no_candidates.total_candidates, 0)
        self.assertEqual(no_candidates.total_after_filter, 0)
        self.assertEqual(no_candidates.matches, [])
        self.assertEqual(all_filtered.total_candidates, 1)
        self.assertEqual(all_filtered.total_after_filter, 0)
        self.assertEqual(all_filtered.matches, [])


if __name__ == "__main__":
    unittest.main()
