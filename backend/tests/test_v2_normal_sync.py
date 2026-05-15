import os
import sys
import types
import unittest
from importlib.util import find_spec
from unittest.mock import patch

from core.v2_text_builder import build_candidate_profile_text, build_job_post_text
from core.v2_translation import detect_text_language, translate_text_to_english_if_needed


USER_ID = "11111111-1111-1111-1111-111111111111"
CV_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
JOB_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"


class _Cursor:
    def __init__(self, responses):
        self.responses = list(responses)
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, tuple(params)))

    def fetchone(self):
        return self.responses.pop(0)


class _Connection:
    def __init__(self, responses):
        self.cursor_obj = _Cursor(responses)
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def _vector(text):
    if not text:
        return None
    return [0.01] * 384


def _cv_payload(**overrides):
    data = {
        "id": CV_ID,
        "created_by": USER_ID,
        "email": "private@example.com",
        "phone": "0900000000",
        "file": {"path": "/tmp/private-cv.pdf"},
        "headline": "Lập trình viên Backend Python\x00",
        "summary": "Có kinh nghiệm xây dựng API với FastAPI\ufffd và PostgreSQL.",
        "target_role": "Backend Developer",
        "industry": "information_technology",
        "occupation_group": "software_engineering",
        "career_level": "middle",
        "years_of_experience": 3,
        "employment_type": ["fulltime"],
        "location": {"city": "Hà Nội", "country": "Việt Nam", "remote_type": "hybrid"},
        "skills": [
            {"name": "Python", "normalized_name": "python", "level": "advanced", "category": "technical", "years": 3},
            {"name": "FastAPI", "normalized_name": "fastapi", "level": "intermediate", "category": "technical", "years": 2},
        ],
        "tools_and_technologies": ["Docker", "PostgreSQL"],
        "domain_knowledge": ["recruitment"],
        "experiences": [
            {
                "title": "Backend Developer",
                "responsibilities": ["Built APIs with FastAPI"],
                "achievements": ["Improved API response time"],
                "skills_used": ["Python"],
                "tools_used": ["Docker"],
            }
        ],
        "projects": [
            {
                "name": "Recruitment Matching System",
                "description": "Built candidate search",
                "role": "Backend Developer",
                "tools": ["FastAPI"],
                "skills_used": ["Python"],
                "outcomes": ["Reduced manual screening time"],
            }
        ],
        "certifications": [{"name": "AWS"}],
    }
    data.update(overrides)
    return data


def _job_payload(**overrides):
    data = {
        "id": JOB_ID,
        "created_by": USER_ID,
        "title": "Lập trình viên Backend Python\x00",
        "description": "Phát triển hệ thống tuyển dụng với FastAPI\ufffd.",
        "responsibilities": ["Xây dựng API bằng FastAPI"],
        "requirements": ["Có kinh nghiệm với PostgreSQL"],
        "nice_to_have": ["Biết Docker"],
        "industry": "information_technology",
        "occupation_group": "software_engineering",
        "seniority": "middle",
        "experience_years": 3,
        "employment_type": ["fulltime"],
        "location": {"city": "Hà Nội", "country": "Việt Nam", "remote_type": "hybrid"},
        "skills": [{"name": "Python", "normalized_name": "python", "level": "advanced", "category": "technical"}],
        "must_have_skills": [{"name": "FastAPI", "normalized_name": "fastapi", "level": "intermediate", "weight": 10}],
        "nice_to_have_skills": [{"name": "Docker", "normalized_name": "docker", "level": "beginner", "weight": 5}],
        "tools_and_technologies": ["Docker", "Git"],
        "domain_knowledge": ["recruitment system"],
        "required_education": {"level": "bachelor", "major": "Công nghệ thông tin"},
        "required_certifications": ["AWS"],
        "apply_email": "private-jobs@example.com",
        "apply_url": "https://private.example/jobs",
        "recruiter": {"email": "hr@example.com", "phone": "0900000001"},
        "applications_count": 99,
    }
    data.update(overrides)
    return data


class V2TextPreparationTests(unittest.TestCase):
    def test_candidate_text_uses_selected_fields_and_excludes_private_fields(self):
        text = build_candidate_profile_text(_cv_payload())

        self.assertIn("Candidate Profile:", text)
        self.assertIn("Lập trình viên Backend Python", text)
        self.assertIn("FastAPI fastapi intermediate technical 2 years", text)
        self.assertIn("Built APIs with FastAPI", text)
        self.assertIn("Reduced manual screening time", text)
        self.assertNotIn("private@example.com", text)
        self.assertNotIn("0900000000", text)
        self.assertNotIn("/tmp/private-cv.pdf", text)
        self.assertNotIn("\x00", text)
        self.assertNotIn("\ufffd", text)

    def test_job_text_uses_selected_fields_and_excludes_private_fields(self):
        text = build_job_post_text(_job_payload())

        self.assertIn("Job Post:", text)
        self.assertIn("Lập trình viên Backend Python", text)
        self.assertIn("Xây dựng API bằng FastAPI", text)
        self.assertIn("FastAPI fastapi intermediate weight 10", text)
        self.assertNotIn("private-jobs@example.com", text)
        self.assertNotIn("hr@example.com", text)
        self.assertNotIn("0900000001", text)
        self.assertNotIn("applications_count", text)
        self.assertNotIn("\x00", text)
        self.assertNotIn("\ufffd", text)

    def test_vietnamese_detection_and_translation_disabled_fallback(self):
        old_value = os.environ.get("V2_TRANSLATION_ENABLED")
        os.environ["V2_TRANSLATION_ENABLED"] = "false"
        try:
            text = "Ứng viên có kinh nghiệm xây dựng API với FastAPI."
            result = translate_text_to_english_if_needed(text)
        finally:
            if old_value is None:
                os.environ.pop("V2_TRANSLATION_ENABLED", None)
            else:
                os.environ["V2_TRANSLATION_ENABLED"] = old_value

        self.assertEqual(detect_text_language(text), "vi")
        self.assertEqual(result.text, text)
        self.assertEqual(result.source_language, "vi")
        self.assertIn("translation_disabled", result.warnings)

    def test_translation_enabled_failure_falls_back_without_crashing(self):
        fake_module = types.SimpleNamespace(
            GoogleTranslator=lambda source, target: types.SimpleNamespace(
                translate=lambda text: (_ for _ in ()).throw(RuntimeError("network down"))
            )
        )
        with patch.dict(os.environ, {"V2_TRANSLATION_ENABLED": "true"}), patch.dict(
            sys.modules, {"deep_translator": fake_module}
        ):
            result = translate_text_to_english_if_needed("Ứng viên có kinh nghiệm Backend.")

        self.assertEqual(result.text, "Ứng viên có kinh nghiệm Backend.")
        self.assertIn("translation_failed", result.warnings)


class V2SyncServiceTests(unittest.TestCase):
    @unittest.skipUnless(find_spec("psycopg"), "psycopg is required for V2 sync service SQL tests")
    def test_candidate_sync_upserts_linked_v2_row_and_embeddings(self):
        from services import v2_sync_service

        conn = _Connection([(1000000000,)])

        with patch.dict(os.environ, {"V2_TRANSLATION_ENABLED": "false"}), patch(
            "services.v2_sync_service.embed_text_minilm", side_effect=_vector
        ):
            result = v2_sync_service.sync_candidate_profile_v2(_cv_payload(), conn)

        self.assertTrue(result["synced"])
        self.assertEqual(result["profileId"], 1000000000)
        self.assertTrue(conn.committed)
        statements = "\n".join(sql for sql, _ in conn.cursor_obj.executed)
        self.assertIn("INSERT INTO candidate_profiles_v2", statements)
        self.assertIn("normal_cv_id", statements)
        self.assertIn("ON CONFLICT (normal_cv_id)", statements)
        self.assertIn("INSERT INTO candidate_embeddings_v2", statements)
        profile_params = conn.cursor_obj.executed[0][1]
        self.assertEqual(profile_params[0], CV_ID)
        self.assertEqual(profile_params[1], USER_ID)
        self.assertEqual(profile_params[6], "Hà Nội")
        self.assertEqual(profile_params[9], "high_school")

    @unittest.skipUnless(find_spec("psycopg"), "psycopg is required for V2 sync service SQL tests")
    def test_job_sync_upserts_linked_v2_row_and_embeddings(self):
        from services import v2_sync_service

        conn = _Connection([(1000000001,)])

        with patch.dict(os.environ, {"V2_TRANSLATION_ENABLED": "false"}), patch(
            "services.v2_sync_service.embed_text_minilm", side_effect=_vector
        ):
            result = v2_sync_service.sync_job_post_v2(_job_payload(), conn)

        self.assertTrue(result["synced"])
        self.assertEqual(result["jobPostId"], 1000000001)
        self.assertTrue(conn.committed)
        statements = "\n".join(sql for sql, _ in conn.cursor_obj.executed)
        self.assertIn("INSERT INTO job_posts_v2", statements)
        self.assertIn("normal_job_id", statements)
        self.assertIn("ON CONFLICT (normal_job_id)", statements)
        self.assertIn("INSERT INTO job_embeddings_v2", statements)
        job_params = conn.cursor_obj.executed[0][1]
        self.assertEqual(job_params[0], JOB_ID)
        self.assertEqual(job_params[1], USER_ID)
        self.assertEqual(job_params[5], "Hà Nội")
        self.assertEqual(job_params[8], "bachelor")

    @unittest.skipUnless(find_spec("psycopg"), "psycopg is required for V2 sync service SQL tests")
    def test_embedding_unavailable_does_not_fail_sync(self):
        from services import v2_sync_service

        conn = _Connection([(1000000002,)])

        with patch.dict(os.environ, {"V2_TRANSLATION_ENABLED": "false"}), patch(
            "services.v2_sync_service.embed_text_minilm",
            side_effect=v2_sync_service.MiniLMUnavailableError("missing model"),
        ):
            result = v2_sync_service.sync_candidate_profile_v2(_cv_payload(), conn)

        self.assertTrue(result["synced"])
        self.assertIn("embedding_unavailable", result["warnings"])
        statements = "\n".join(sql for sql, _ in conn.cursor_obj.executed)
        self.assertIn("DELETE FROM candidate_embeddings_v2", statements)


if __name__ == "__main__":
    unittest.main()
