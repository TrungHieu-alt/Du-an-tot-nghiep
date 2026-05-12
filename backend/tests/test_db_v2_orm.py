"""Integration tests for Matching V2 ORM insert/read — Slice 6A.

These tests require a live PostgreSQL V2 instance (Docker Compose `postgres`
service).  They are skipped automatically when the database is unreachable so
that the unit-test suite can run in CI without a database.

Run against the compose stack:

    docker compose exec backend python -m pytest backend/tests/test_db_v2_orm.py -v

Or from the host (with postgres exposed on port 5433):

    python -m pytest backend/tests/test_db_v2_orm.py -v

Scope: ORM insert/read for job_posts_v2, candidate_profiles_v2,
       job_embeddings_v2, candidate_embeddings_v2.
       No match_results_v2. No runtime matching path touched.
"""

from __future__ import annotations

import os
import unittest

import numpy as np

# ---------------------------------------------------------------------------
# DB availability guard — skip if PostgreSQL V2 is unreachable
# ---------------------------------------------------------------------------

_DB_AVAILABLE = False
_SKIP_REASON = "PostgreSQL V2 unavailable (set POSTGRES_HOST / run via Docker Compose)"

try:
    from sqlalchemy import create_engine, text

    _host = os.getenv("POSTGRES_HOST", "localhost")
    _port = os.getenv("POSTGRES_PORT", "5433")
    _user = os.getenv("POSTGRES_USER", "jobmatcher")
    _pw = os.getenv("POSTGRES_PASSWORD", "jobmatcher")
    _db = os.getenv("POSTGRES_DB", "jobmatcher_v2")
    _probe_url = f"postgresql+psycopg://{_user}:{_pw}@{_host}:{_port}/{_db}"
    _probe_engine = create_engine(_probe_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})
    with _probe_engine.connect() as _c:
        _c.execute(text("SELECT 1"))
    _DB_AVAILABLE = True
    _probe_engine.dispose()
except Exception as _e:
    _SKIP_REASON = f"PostgreSQL V2 unreachable: {_e}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vec(value: float) -> list[float]:
    return np.full(384, value, dtype=np.float32).tolist()


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@unittest.skipUnless(_DB_AVAILABLE, _SKIP_REASON)
class TestDbV2Orm(unittest.TestCase):
    """ORM insert/read tests against PostgreSQL V2.

    Each test method operates inside a transaction that is rolled back at the
    end, so tests are fully isolated and leave no data in the database.
    Test IDs use the 9xxxx range to avoid colliding with canonical seed data
    (IDs 1001-1005 / 2001-2005).
    """

    _TEST_CV_ID = 90001
    _TEST_JOB_ID = 90002

    def setUp(self) -> None:
        from db_v2.session import get_v2_engine, make_session_factory

        self.engine = get_v2_engine()
        factory = make_session_factory(self.engine)
        self.session = factory()
        # Savepoint so we can roll back after each test without closing the connection
        self.session.begin_nested()

    def tearDown(self) -> None:
        self.session.rollback()
        self.session.close()
        self.engine.dispose()

    # -----------------------------------------------------------------------
    # job_posts_v2
    # -----------------------------------------------------------------------

    def test_insert_and_read_job_post(self) -> None:
        from db_v2.orm_models import JobPostV2Orm

        job = JobPostV2Orm(
            job_id=self._TEST_JOB_ID,
            title="ORM Test Job",
            skills=["python", "sqlalchemy"],
            requirement="Test requirement text.",
            location="ha_noi",
            job_type="fulltime",
            seniority="mid",
            education="dai_hoc",
            required_certifications=[],
        )
        self.session.add(job)
        self.session.flush()

        read_back = self.session.get(JobPostV2Orm, self._TEST_JOB_ID)
        self.assertIsNotNone(read_back)
        self.assertEqual(read_back.job_id, self._TEST_JOB_ID)
        self.assertEqual(read_back.title, "ORM Test Job")
        self.assertEqual(read_back.skills, ["python", "sqlalchemy"])
        self.assertEqual(read_back.requirement, "Test requirement text.")
        self.assertEqual(read_back.location, "ha_noi")
        self.assertEqual(read_back.job_type, "fulltime")
        self.assertEqual(read_back.seniority, "mid")
        self.assertEqual(read_back.education, "dai_hoc")
        self.assertEqual(read_back.required_certifications, [])

    def test_job_post_check_constraint_location(self) -> None:
        from sqlalchemy.exc import IntegrityError

        from db_v2.orm_models import JobPostV2Orm

        bad = JobPostV2Orm(
            job_id=self._TEST_JOB_ID + 100,
            title="Bad location",
            skills=[],
            requirement="",
            location="invalid_city",
            job_type="fulltime",
            seniority="mid",
            education="dai_hoc",
            required_certifications=[],
        )
        self.session.add(bad)
        with self.assertRaises(IntegrityError):
            self.session.flush()

    # -----------------------------------------------------------------------
    # candidate_profiles_v2
    # -----------------------------------------------------------------------

    def test_insert_and_read_candidate_profile(self) -> None:
        from db_v2.orm_models import CandidateProfileV2Orm

        cv = CandidateProfileV2Orm(
            cv_id=self._TEST_CV_ID,
            title="ORM Test Candidate",
            skills=["python", "postgres"],
            summary="Integration test candidate summary.",
            experience="3 years of ORM testing.",
            location="tp_hcm",
            job_type="remote",
            seniority="junior",
            education="dai_hoc",
            certifications=["aws_saa"],
        )
        self.session.add(cv)
        self.session.flush()

        read_back = self.session.get(CandidateProfileV2Orm, self._TEST_CV_ID)
        self.assertIsNotNone(read_back)
        self.assertEqual(read_back.cv_id, self._TEST_CV_ID)
        self.assertEqual(read_back.title, "ORM Test Candidate")
        self.assertEqual(read_back.skills, ["python", "postgres"])
        self.assertEqual(read_back.summary, "Integration test candidate summary.")
        self.assertEqual(read_back.experience, "3 years of ORM testing.")
        self.assertEqual(read_back.location, "tp_hcm")
        self.assertEqual(read_back.job_type, "remote")
        self.assertEqual(read_back.seniority, "junior")
        self.assertEqual(read_back.education, "dai_hoc")
        self.assertEqual(read_back.certifications, ["aws_saa"])

    def test_candidate_profile_check_constraint_education(self) -> None:
        from sqlalchemy.exc import IntegrityError

        from db_v2.orm_models import CandidateProfileV2Orm

        bad = CandidateProfileV2Orm(
            cv_id=self._TEST_CV_ID + 100,
            title="Bad education",
            skills=[],
            summary="",
            experience="",
            location="ha_noi",
            job_type="fulltime",
            seniority="mid",
            education="phd_invalid",
            certifications=[],
        )
        self.session.add(bad)
        with self.assertRaises(IntegrityError):
            self.session.flush()

    # -----------------------------------------------------------------------
    # job_embeddings_v2 — vector insert/read + dimension check
    # -----------------------------------------------------------------------

    def _insert_test_job(self) -> None:
        from db_v2.orm_models import JobPostV2Orm

        self.session.add(
            JobPostV2Orm(
                job_id=self._TEST_JOB_ID,
                title="Job for embedding test",
                skills=[],
                requirement="",
                location="ha_noi",
                job_type="fulltime",
                seniority="mid",
                education="dai_hoc",
                required_certifications=[],
            )
        )
        self.session.flush()

    def _insert_test_cv(self) -> None:
        from db_v2.orm_models import CandidateProfileV2Orm

        self.session.add(
            CandidateProfileV2Orm(
                cv_id=self._TEST_CV_ID,
                title="CV for embedding test",
                skills=[],
                summary="",
                experience="",
                location="ha_noi",
                job_type="fulltime",
                seniority="mid",
                education="dai_hoc",
                certifications=[],
            )
        )
        self.session.flush()

    def test_insert_and_read_job_embeddings(self) -> None:
        from db_v2.orm_models import JobEmbeddingsV2Orm

        self._insert_test_job()

        emb = JobEmbeddingsV2Orm(
            job_id=self._TEST_JOB_ID,
            emb_title=_vec(0.10),
            emb_skills=_vec(0.20),
            emb_requirement=_vec(0.30),
        )
        self.session.add(emb)
        self.session.flush()

        read_back = self.session.get(JobEmbeddingsV2Orm, self._TEST_JOB_ID)
        self.assertIsNotNone(read_back)
        self.assertEqual(read_back.job_id, self._TEST_JOB_ID)

        # Vector dimensions must be 384
        self.assertEqual(len(read_back.emb_title), 384)
        self.assertEqual(len(read_back.emb_skills), 384)
        self.assertEqual(len(read_back.emb_requirement), 384)

        # Values round-trip correctly (float32 tolerance)
        self.assertAlmostEqual(float(read_back.emb_title[0]), 0.10, places=5)
        self.assertAlmostEqual(float(read_back.emb_skills[0]), 0.20, places=5)
        self.assertAlmostEqual(float(read_back.emb_requirement[0]), 0.30, places=5)

    def test_job_embeddings_nullable_columns(self) -> None:
        """Per REQUIREMENTS.md §9, missing embeddings are allowed (score = 0)."""
        from db_v2.orm_models import JobEmbeddingsV2Orm

        self._insert_test_job()

        emb = JobEmbeddingsV2Orm(
            job_id=self._TEST_JOB_ID,
            emb_title=None,
            emb_skills=None,
            emb_requirement=None,
        )
        self.session.add(emb)
        self.session.flush()

        read_back = self.session.get(JobEmbeddingsV2Orm, self._TEST_JOB_ID)
        self.assertIsNone(read_back.emb_title)
        self.assertIsNone(read_back.emb_skills)
        self.assertIsNone(read_back.emb_requirement)

    # -----------------------------------------------------------------------
    # candidate_embeddings_v2 — vector insert/read + dimension check
    # -----------------------------------------------------------------------

    def test_insert_and_read_candidate_embeddings(self) -> None:
        from db_v2.orm_models import CandidateEmbeddingsV2Orm

        self._insert_test_cv()

        emb = CandidateEmbeddingsV2Orm(
            cv_id=self._TEST_CV_ID,
            emb_title=_vec(0.40),
            emb_skills=_vec(0.50),
            emb_summary=_vec(0.60),
            emb_experience=_vec(0.70),
        )
        self.session.add(emb)
        self.session.flush()

        read_back = self.session.get(CandidateEmbeddingsV2Orm, self._TEST_CV_ID)
        self.assertIsNotNone(read_back)
        self.assertEqual(read_back.cv_id, self._TEST_CV_ID)

        # Vector dimensions must be 384
        self.assertEqual(len(read_back.emb_title), 384)
        self.assertEqual(len(read_back.emb_skills), 384)
        self.assertEqual(len(read_back.emb_summary), 384)
        self.assertEqual(len(read_back.emb_experience), 384)

        # Values round-trip correctly (float32 tolerance)
        self.assertAlmostEqual(float(read_back.emb_title[0]), 0.40, places=5)
        self.assertAlmostEqual(float(read_back.emb_skills[0]), 0.50, places=5)
        self.assertAlmostEqual(float(read_back.emb_summary[0]), 0.60, places=5)
        self.assertAlmostEqual(float(read_back.emb_experience[0]), 0.70, places=5)

    def test_candidate_embeddings_nullable_columns(self) -> None:
        from db_v2.orm_models import CandidateEmbeddingsV2Orm

        self._insert_test_cv()

        emb = CandidateEmbeddingsV2Orm(
            cv_id=self._TEST_CV_ID,
            emb_title=None,
            emb_skills=None,
            emb_summary=None,
            emb_experience=None,
        )
        self.session.add(emb)
        self.session.flush()

        read_back = self.session.get(CandidateEmbeddingsV2Orm, self._TEST_CV_ID)
        self.assertIsNone(read_back.emb_title)
        self.assertIsNone(read_back.emb_skills)
        self.assertIsNone(read_back.emb_summary)
        self.assertIsNone(read_back.emb_experience)

    # -----------------------------------------------------------------------
    # Scope guard — match_results_v2 must not exist
    # -----------------------------------------------------------------------

    def test_match_results_v2_table_does_not_exist(self) -> None:
        result = self.session.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'match_results_v2'"
            )
        ).scalar()
        self.assertEqual(result, 0, "match_results_v2 must not exist in prototype schema")

    # -----------------------------------------------------------------------
    # Scope guard — only the 4 prototype tables plus additive app tables exist
    # -----------------------------------------------------------------------

    def test_only_four_prototype_tables_exist_with_additive_users_table(self) -> None:
        rows = self.session.execute(
            text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            )
        ).fetchall()
        tables = {r[0] for r in rows}
        prototype_tables = {
            "job_posts_v2",
            "candidate_profiles_v2",
            "job_embeddings_v2",
            "candidate_embeddings_v2",
        }
        allowed_tables = prototype_tables | {"users"}

        self.assertTrue(prototype_tables.issubset(tables))
        self.assertEqual(tables, allowed_tables, f"unexpected tables present: {tables - allowed_tables}")

    # -----------------------------------------------------------------------
    # ORM model import isolation — SQLAlchemy must not appear in runtime path
    # -----------------------------------------------------------------------

    def test_sqlalchemy_not_imported_in_runtime_matching_db(self) -> None:
        import importlib
        import sys

        # Remove cached module so we get a clean import check
        mod_name = "matching_v2.db"
        was_cached = mod_name in sys.modules
        cached = sys.modules.pop(mod_name, None)
        try:
            mod = importlib.import_module(mod_name)
            src = open(mod.__file__, encoding="utf-8").read()
            self.assertNotIn(
                "sqlalchemy",
                src,
                "matching_v2/db.py must not import sqlalchemy (runtime path isolation)",
            )
        finally:
            if was_cached and cached is not None:
                sys.modules[mod_name] = cached
            elif mod_name in sys.modules:
                del sys.modules[mod_name]

    def test_sqlalchemy_not_imported_in_runtime_matching_runner(self) -> None:
        import importlib
        import sys

        mod_name = "matching_v2.runner"
        was_cached = mod_name in sys.modules
        cached = sys.modules.pop(mod_name, None)
        try:
            mod = importlib.import_module(mod_name)
            src = open(mod.__file__, encoding="utf-8").read()
            self.assertNotIn(
                "sqlalchemy",
                src,
                "matching_v2/runner.py must not import sqlalchemy (runtime path isolation)",
            )
        finally:
            if was_cached and cached is not None:
                sys.modules[mod_name] = cached
            elif mod_name in sys.modules:
                del sys.modules[mod_name]

    def test_sqlalchemy_not_imported_in_match_v2_router(self) -> None:
        import importlib
        import sys

        mod_name = "routers.match_v2_router"
        was_cached = mod_name in sys.modules
        cached = sys.modules.pop(mod_name, None)
        try:
            mod = importlib.import_module(mod_name)
            src = open(mod.__file__, encoding="utf-8").read()
            self.assertNotIn(
                "sqlalchemy",
                src,
                "routers/match_v2_router.py must not import sqlalchemy (runtime path isolation)",
            )
        finally:
            if was_cached and cached is not None:
                sys.modules[mod_name] = cached
            elif mod_name in sys.modules:
                del sys.modules[mod_name]


if __name__ == "__main__":
    unittest.main()
