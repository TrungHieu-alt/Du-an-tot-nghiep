from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.embedding import EmbeddingError
from jobconnect.integrations.rerank import RerankError
from jobconnect.modules.api.shared import CurrentUser
from jobconnect.modules.jobs import service as jobs_service
from jobconnect.modules.matching import service as matching_service
from jobconnect.modules.matching.models import CandidateProfileMatch, JobPostMatch
from jobconnect.modules.matching.schemas import MatchingRequest, SemanticSearchRequest
from jobconnect.modules.resumes import service as resumes_service


class _FakeCursor:
    def execute(self, *_args, **_kwargs) -> None:
        return None

    def fetchall(self):
        return [(101,), (102,)]

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None


class _FakeConn:
    def cursor(self):
        return _FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None


class MatchingSlice8Tests(unittest.TestCase):
    def _anchor(self):
        return {
            "row": (201, 1, 10, "Backend", "Build APIs", ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], "published", None, None),
            "model": JobPostMatch(
                job_id=201,
                title="Backend",
                skills=("python",),
                requirement="Build APIs",
                location="ha_noi",
                job_type="remote",
                seniority="mid",
                education="dai_hoc",
                required_certifications=(),
            ),
            "summary": {
                "job_id": 201,
                "title": "Backend",
                "location": "ha_noi",
                "job_type": "remote",
                "seniority": "mid",
                "education": "dai_hoc",
                "skills": ["python"],
                "required_certifications": [],
                "status": "published",
                "published_at": None,
            },
            "status": "published",
            "emb": None,
        }

    def _candidate(self, resume_id: int, title: str):
        return {
            "row": (resume_id, 77, title, "summary", "experience", ["python"], "ha_noi", "remote", "mid", "dai_hoc", [], False, "active"),
            "model": CandidateProfileMatch(
                cv_id=resume_id,
                title=title,
                skills=("python",),
                summary="summary",
                experience="experience",
                location="ha_noi",
                job_type="remote",
                seniority="mid",
                education="dai_hoc",
                certifications=(),
            ),
            "summary": {
                "resume_id": resume_id,
                "title": title,
                "location": "ha_noi",
                "job_type": "remote",
                "seniority": "mid",
                "education": "dai_hoc",
                "skills": ["python"],
                "certifications": [],
                "status": "active",
            },
            "status": "active",
            "emb": None,
        }

    def test_matching_defaults_follow_requirements(self):
        req = MatchingRequest()
        self.assertEqual(req.top_k, 10)
        self.assertAlmostEqual(req.min_score, 0.7)

    def test_always_attempts_rerank_even_when_request_rerank_false(self):
        candidates = {
            101: self._candidate(101, "Candidate A"),
            102: self._candidate(102, "Candidate B"),
        }

        def _load_resume_side_effect(resume_id: int):
            return candidates[resume_id]

        def _score_pair_side_effect(*_args, **_kwargs):
            # Candidate 101 starts higher deterministic; rerank should flip.
            cv_id = _args[2].cv_id
            if cv_id == 101:
                det = 0.9
            else:
                det = 0.7
            return (
                {
                    "title_sim": 0.5,
                    "skills_sim": 0.5,
                    "req_exp_sim": 0.5,
                    "req_summary_sim": 0.5,
                    "exact": 1.0,
                    "bonus_exact_skill": 0.0,
                    "penalty_missing_required": 0.0,
                    "deterministic_score": det,
                },
                [],
            )

        fake_api = SimpleNamespace(get_connection=lambda: _FakeConn())
        fake_rerank = SimpleNamespace(score=lambda _q, _docs: [0.1, 0.95])

        with patch.object(matching_service, "_api", return_value=fake_api), \
             patch.object(matching_service, "_load_job", return_value=self._anchor()), \
             patch.object(matching_service, "_load_resume", side_effect=_load_resume_side_effect), \
             patch.object(matching_service, "passes_hard_filter", return_value=True), \
             patch.object(matching_service, "_score_pair", side_effect=_score_pair_side_effect), \
             patch.object(matching_service, "get_rerank_provider", return_value=fake_rerank):
            response = matching_service._run_matching("job", 201, MatchingRequest(rerank=False, top_k=10, min_score=0.0))

        self.assertTrue(response.runtime.rerank_applied)
        self.assertEqual(response.items[0].resume.resume_id, 102)
        self.assertEqual(response.runtime.candidates_total, 2)
        self.assertEqual(response.runtime.candidates_after_filter, 2)

    def test_rerank_failure_falls_back_with_warning(self):
        fake_api = SimpleNamespace(get_connection=lambda: _FakeConn())
        fake_rerank = SimpleNamespace(score=lambda _q, _docs: (_ for _ in ()).throw(RerankError("model_down")))

        with patch.object(matching_service, "_api", return_value=fake_api), \
             patch.object(matching_service, "_load_job", return_value=self._anchor()), \
             patch.object(matching_service, "_load_resume", side_effect=lambda rid: self._candidate(rid, f"C{rid}")), \
             patch.object(matching_service, "passes_hard_filter", return_value=True), \
             patch.object(
                 matching_service,
                 "_score_pair",
                 return_value=(
                     {
                         "title_sim": 0.5,
                         "skills_sim": 0.5,
                         "req_exp_sim": 0.5,
                         "req_summary_sim": 0.5,
                         "exact": 1.0,
                         "bonus_exact_skill": 0.0,
                         "penalty_missing_required": 0.0,
                         "deterministic_score": 0.8,
                     },
                     [],
                 ),
             ), \
             patch.object(matching_service, "get_rerank_provider", return_value=fake_rerank):
            response = matching_service._run_matching("job", 201, MatchingRequest(top_k=10, min_score=0.0))

        self.assertFalse(response.runtime.rerank_applied)
        self.assertTrue(any("rerank_fallback" in warning for warning in response.runtime.warnings))
        self.assertEqual(len(response.items), 2)


class SemanticSearchHardeningTests(unittest.TestCase):
    def test_job_semantic_search_returns_503_when_embedding_unavailable(self):
        user = CurrentUser(user_id=1, email="a@example.com", role="admin", status="active")
        with patch.object(jobs_service, "_vec", side_effect=EmbeddingError("down")):
            with self.assertRaises(Exception) as ctx:
                jobs_service.semantic_search_jobs(
                    request=SemanticSearchRequest(query="python", top_k=5, filters={}),
                    user=user,
                )
        self.assertEqual(getattr(ctx.exception, "status_code", None), 503)

    def test_resume_semantic_search_returns_503_when_embedding_unavailable(self):
        with patch.object(resumes_service, "_vec", side_effect=EmbeddingError("down")):
            with self.assertRaises(Exception) as ctx:
                resumes_service.semantic_search_resumes(
                    SemanticSearchRequest(query="python", top_k=5, filters={})
                )
        self.assertEqual(getattr(ctx.exception, "status_code", None), 503)


if __name__ == "__main__":
    unittest.main()
