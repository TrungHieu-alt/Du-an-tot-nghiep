import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from matching_v2.hybrid_models import (
    HybridBreakdown,
    MatchHybridItem,
    RunMatchingHybridResponse,
)
from matching_v2.hybrid_scoring import evaluate_pair_hybrid
from matching_v2.hybrid_utils import normalize_weights
from matching_v2.models import (
    CandidateEmbeddingsV2,
    CandidateProfileV2,
    JobEmbeddingsV2,
    JobPostV2,
)
from matching_v2.skill_normalizer import normalize_skills, skill_coverage
from routers.match_hybrid_router import router as hybrid_router


class HybridMatchingTests(unittest.TestCase):
    def _job(self, **overrides) -> JobPostV2:
        data = {
            "job_id": 10,
            "title": "Backend Engineer",
            "skills": ("python", "node.js", "postgresql"),
            "requirement": "Build backend APIs and operate PostgreSQL services",
            "location": "Hà Nội",
            "job_type": "fulltime",
            "seniority": "senior",
            "education": "bachelor",
            "required_certifications": (),
        }
        data.update(overrides)
        return JobPostV2(**data)

    def _cv(self, **overrides) -> CandidateProfileV2:
        data = {
            "cv_id": 20,
            "title": "Backend Engineer",
            "skills": ("python", "nodejs", "postgres"),
            "summary": "Backend engineer working with APIs",
            "experience": "Built backend APIs with PostgreSQL",
            "location": "Hà Nội",
            "job_type": "fulltime",
            "seniority": "senior",
            "education": "master",
            "certifications": (),
        }
        data.update(overrides)
        return CandidateProfileV2(**data)

    def _job_emb(self, **overrides) -> JobEmbeddingsV2:
        data = {
            "job_id": 10,
            "emb_title": [1.0, 0.0],
            "emb_skills": [1.0, 0.0],
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

    def test_both_fields_empty_skips_group_without_fake_score(self):
        result = evaluate_pair_hybrid(
            self._job(title="", seniority=""),
            self._job_emb(emb_title=None),
            self._cv(title="", seniority=""),
            self._cv_emb(emb_title=None),
        )

        self.assertIsNone(result.breakdown.title_score)
        self.assertIn(
            "title_score",
            {group.group for group in result.skipped_groups},
        )

    def test_weight_normalization_removes_skipped_weights(self):
        normalized = normalize_weights({"skills_score": 0.32, "title_score": 0.08})

        self.assertAlmostEqual(normalized["skills_score"], 0.8)
        self.assertAlmostEqual(normalized["title_score"], 0.2)

    def test_skill_alias_normalization(self):
        self.assertEqual(normalize_skills(["nodejs", "postgres", "js"]), ("node.js", "postgresql", "javascript"))
        coverage, matched = skill_coverage(
            ["node.js", "postgresql", "javascript"],
            ["nodejs", "postgres", "js"],
        )

        self.assertEqual(coverage, 1.0)
        self.assertEqual(matched, ["javascript", "node.js", "postgresql"])

    def test_remote_location_passes_and_explains(self):
        result = evaluate_pair_hybrid(
            self._job(job_type="remote", location="Hà Nội"),
            self._job_emb(),
            self._cv(job_type="remote", location="TP. Hồ Chí Minh"),
            self._cv_emb(),
        )

        self.assertEqual(result.breakdown.location_score, 100.0)
        self.assertIn("remote", result.explanations["location"].lower())

    def test_non_remote_location_mismatch_fails_when_strict(self):
        result = evaluate_pair_hybrid(
            self._job(job_type="fulltime", location="Hà Nội"),
            self._job_emb(),
            self._cv(job_type="fulltime", location="TP. Hồ Chí Minh"),
            self._cv_emb(),
            strict_filters=True,
        )

        self.assertFalse(result.passed)
        self.assertIn("location", {failure.field for failure in result.failed_filters})
        self.assertEqual(result.breakdown.location_score, 0.0)

    def test_seniority_scoring_and_overqualified_warning(self):
        equal = evaluate_pair_hybrid(self._job(seniority="senior"), self._job_emb(), self._cv(seniority="senior"), self._cv_emb())
        lower = evaluate_pair_hybrid(self._job(seniority="senior"), self._job_emb(), self._cv(seniority="mid"), self._cv_emb())
        higher = evaluate_pair_hybrid(self._job(seniority="junior"), self._job_emb(), self._cv(seniority="lead"), self._cv_emb())

        self.assertEqual(equal.breakdown.seniority_score, 100.0)
        self.assertEqual(lower.breakdown.seniority_score, 70.0)
        self.assertGreater(higher.breakdown.seniority_score, 80.0)
        self.assertIn("Candidate may be overqualified.", higher.warnings)

    def test_education_rank_pass_and_fail(self):
        passing = evaluate_pair_hybrid(self._job(education="bachelor"), self._job_emb(), self._cv(education="master"), self._cv_emb())
        failing = evaluate_pair_hybrid(self._job(education="bachelor"), self._job_emb(), self._cv(education="high_school"), self._cv_emb())

        self.assertEqual(passing.breakdown.education_score, 100.0)
        self.assertEqual(failing.breakdown.education_score, 0.0)
        self.assertIn("education", {failure.field for failure in failing.failed_filters})

    def test_certification_required_vs_empty_optional(self):
        optional = evaluate_pair_hybrid(
            self._job(required_certifications=()),
            self._job_emb(),
            self._cv(certifications=()),
            self._cv_emb(),
        )
        required = evaluate_pair_hybrid(
            self._job(required_certifications=("aws",)),
            self._job_emb(),
            self._cv(certifications=()),
            self._cv_emb(),
        )

        self.assertIsNone(optional.breakdown.certification_score)
        self.assertIn("certification_score", {group.group for group in optional.skipped_groups})
        self.assertFalse(required.passed)
        self.assertIn("certification", {failure.field for failure in required.failed_filters})

    def test_missing_schema_groups_are_skipped(self):
        result = evaluate_pair_hybrid(self._job(), self._job_emb(), self._cv(), self._cv_emb())
        skipped = {group.group: group.reason for group in result.skipped_groups}

        self.assertIn("project_score", skipped)
        self.assertIn("language_score", skipped)
        self.assertIn("salary_score", skipped)
        self.assertIsNone(result.breakdown.project_score)
        self.assertIsNone(result.breakdown.language_score)
        self.assertIsNone(result.breakdown.salary_score)

    def test_missing_minilm_embeddings_fall_back_to_text_similarity_with_warning(self):
        result = evaluate_pair_hybrid(self._job(), None, self._cv(), None)

        self.assertGreater(result.breakdown.title_score, 0.0)
        self.assertTrue(
            any("deterministic text similarity" in warning for warning in result.warnings)
        )

    def test_hybrid_endpoint_response_shape(self):
        app = FastAPI()
        app.include_router(hybrid_router, prefix="/api")
        client = TestClient(app)
        payload = RunMatchingHybridResponse(
            anchor_type="job",
            anchor_id=10,
            total_candidates=1,
            total_after_filter=1,
            total_returned=1,
            runtime_ms_total=1.0,
            runtime_ms_filter=0.1,
            runtime_ms_scoring=0.7,
            runtime_ms_sort=0.2,
            matches=[
                MatchHybridItem(
                    rank=1,
                    job_id=10,
                    cv_id=20,
                    final_score=87.5,
                    passed=True,
                    breakdown=HybridBreakdown(skills_score=90.0),
                    skipped_groups=[],
                    failed_filters=[],
                    warnings=[],
                    explanations={"skills": "ok"},
                )
            ],
        )

        with patch("routers.match_hybrid_router.get_connection", return_value=Mock()), \
             patch("routers.match_hybrid_router.run_hybrid_for_job", return_value=payload):
            res = client.post("/api/v2/prototype/matching-hybrid/job/10/run")

        self.assertEqual(res.status_code, 200)
        data = res.json()
        match = data["matches"][0]
        self.assertEqual(match["final_score"], 87.5)
        self.assertTrue(match["passed"])
        self.assertIn("breakdown", match)
        self.assertIn("skipped_groups", match)
        self.assertIn("failed_filters", match)
        self.assertIn("warnings", match)
        self.assertIn("explanations", match)

    def test_hybrid_endpoint_validation_error(self):
        app = FastAPI()
        app.include_router(hybrid_router, prefix="/api")
        client = TestClient(app)

        res = client.post(
            "/api/v2/prototype/matching-hybrid/job/10/run",
            json={"top_k": 0},
        )

        self.assertEqual(res.status_code, 422)

    def test_old_openapi_match_item_contract_is_unchanged(self):
        from main import app

        schema = TestClient(app).get("/openapi.json").json()
        old_props = schema["components"]["schemas"]["MatchItemV2Response"]["properties"]
        hybrid_props = schema["components"]["schemas"]["MatchHybridItem"]["properties"]

        for field in (
            "final_score",
            "title_score",
            "skills_score",
            "req_exp_score",
            "req_summary_score",
            "reasoning",
        ):
            self.assertIn(field, old_props)
        self.assertNotIn("breakdown", old_props)
        self.assertIn("breakdown", hybrid_props)
        self.assertIn("/api/v2/prototype/matching/job/{job_id}/run", schema["paths"])
        self.assertIn("/api/v2/prototype/matching-hybrid/job/{job_id}/run", schema["paths"])


if __name__ == "__main__":
    unittest.main()
