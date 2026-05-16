"""Slice 6: LLM Parser Adapter.

Covers DoD per slices.md §6:
- Vietnamese, English, mixed-language fixtures map into canonical enums.
- Unsupported/invalid LLM output fails safely (per-field sanitization).
- Raw unsupported enum values are NOT persisted.
- Parser version is reported via the adapter.
- Network/HTTP failures raise ParserError (worker marks parse job failed).
- get_parser() factory falls back to local when OPENAI_API_KEY missing.
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations.llm import (
    LocalDeterministicParser,
    OpenAIParser,
    ParserError,
    get_parser,
    reset_parser_cache,
)
from jobconnect.modules.documents.local_parser import (
    EDUCATION_VALUES,
    JOB_TYPE_VALUES,
    LOCATION_VALUES,
    SENIORITY_VALUES,
    validate_enum,
)


# ---------------------------------------------------------------------------
# 1. Enum validator unit tests
# ---------------------------------------------------------------------------


class TestValidateEnum(unittest.TestCase):
    def test_valid_value_returned(self) -> None:
        self.assertEqual(validate_enum("senior", SENIORITY_VALUES, "junior"), "senior")

    def test_invalid_value_returns_default(self) -> None:
        self.assertEqual(validate_enum("god_mode", SENIORITY_VALUES, "junior"), "junior")

    def test_non_string_returns_default(self) -> None:
        self.assertEqual(validate_enum(None, LOCATION_VALUES, "ha_noi"), "ha_noi")
        self.assertEqual(validate_enum(42, LOCATION_VALUES, "ha_noi"), "ha_noi")


# ---------------------------------------------------------------------------
# 2. Local adapter (parser_version, fixture parsing in EN/VN/mixed)
# ---------------------------------------------------------------------------


class TestLocalAdapter(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = LocalDeterministicParser()

    def test_parser_version_is_local_v1(self) -> None:
        self.assertEqual(self.parser.parser_version, "local-v1")

    def test_english_cv_canonical_enums(self) -> None:
        cv = "Senior Backend Engineer\nHo Chi Minh City\nMaster of Science\nSkills: Python, Docker"
        result = self.parser.parse_resume(cv, "cv.pdf")
        self.assertIn(result.location, LOCATION_VALUES)
        self.assertIn(result.job_type, JOB_TYPE_VALUES)
        self.assertIn(result.seniority, SENIORITY_VALUES)
        self.assertIn(result.education, EDUCATION_VALUES)
        self.assertEqual(result.location, "tp_hcm")
        self.assertEqual(result.seniority, "senior")
        self.assertEqual(result.education, "thac_si")

    def test_vietnamese_cv_canonical_enums(self) -> None:
        cv = "Lập trình viên Backend\nHà Nội\nThạc sĩ Khoa học máy tính\nKỹ năng: Python, Docker"
        result = self.parser.parse_resume(cv, "cv.pdf")
        self.assertEqual(result.location, "ha_noi")
        self.assertEqual(result.education, "thac_si")
        # Enums always canonical
        self.assertIn(result.seniority, SENIORITY_VALUES)
        self.assertIn(result.job_type, JOB_TYPE_VALUES)

    def test_mixed_language_jd_canonical_enums(self) -> None:
        jd = (
            "Senior Python Developer\n"
            "Đà Nẵng / remote work available\n"
            "Yêu cầu: 3+ years experience with Django and PostgreSQL\n"
            "Bachelor degree"
        )
        result = self.parser.parse_job(jd, "jd.pdf")
        self.assertEqual(result.location, "da_nang")
        self.assertEqual(result.job_type, "remote")
        self.assertEqual(result.seniority, "senior")
        self.assertEqual(result.education, "dai_hoc")

    def test_empty_text_defaults_within_canonical_sets(self) -> None:
        result = self.parser.parse_resume("", filename="cv.pdf")
        self.assertIn(result.location, LOCATION_VALUES)
        self.assertIn(result.job_type, JOB_TYPE_VALUES)
        self.assertIn(result.seniority, SENIORITY_VALUES)
        self.assertIn(result.education, EDUCATION_VALUES)


# ---------------------------------------------------------------------------
# 3. OpenAI adapter (mocked HTTP)
# ---------------------------------------------------------------------------


def _make_chat_response(content: dict[str, Any], status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(content)}}]
    }
    resp.text = json.dumps(content)
    return resp


class TestOpenAIAdapterHappyPath(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")

    def test_parser_version_includes_model(self) -> None:
        self.assertEqual(self.parser.parser_version, "openai-gpt-4o-mini-v1")

    def test_parse_resume_valid_payload(self) -> None:
        payload = {
            "title": "Backend Engineer",
            "summary": "5 years of Python",
            "experience": "Worked at FooCorp",
            "skills": ["python", "Docker", "PostgreSQL"],
            "location": "ha_noi",
            "job_type": "fulltime",
            "seniority": "senior",
            "education": "thac_si",
            "certifications": ["AWS Certified Solutions Architect"],
        }
        with patch("jobconnect.integrations.llm.openai.httpx.post",
                   return_value=_make_chat_response(payload)):
            result = self.parser.parse_resume("some text", filename="cv.pdf")
        self.assertEqual(result.title, "Backend Engineer")
        self.assertEqual(result.location, "ha_noi")
        self.assertEqual(result.seniority, "senior")
        # Skill list normalized: "Docker" → "docker"
        self.assertIn("docker", result.skills)
        self.assertIn("python", result.skills)
        self.assertIn("postgresql", result.skills)


class TestOpenAIAdapterSanitizesEnums(unittest.TestCase):
    """Raw unsupported enum values must NOT reach the caller."""

    def test_invalid_enum_values_replaced_with_defaults(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        payload = {
            "title": "Engineer",
            "location": "moon_base",        # invalid → ha_noi
            "job_type": "underwater",       # invalid → fulltime
            "seniority": "supreme",         # invalid → junior
            "education": "phd_galactic",    # invalid → dai_hoc
            "skills": ["python"],
        }
        with patch("jobconnect.integrations.llm.openai.httpx.post",
                   return_value=_make_chat_response(payload)):
            result = parser.parse_resume("text", filename="cv.pdf")
        self.assertEqual(result.location, "ha_noi")
        self.assertEqual(result.job_type, "fulltime")
        self.assertEqual(result.seniority, "junior")
        self.assertEqual(result.education, "dai_hoc")
        # No raw invalid values leaked
        for raw in ("moon_base", "underwater", "supreme", "phd_galactic"):
            self.assertNotIn(raw, (result.location, result.job_type, result.seniority, result.education))

    def test_missing_enum_fields_use_defaults(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        payload = {"title": "Eng", "skills": []}  # all enum keys absent
        with patch("jobconnect.integrations.llm.openai.httpx.post",
                   return_value=_make_chat_response(payload)):
            result = parser.parse_job("text", filename="jd.pdf")
        self.assertIn(result.location, LOCATION_VALUES)
        self.assertIn(result.job_type, JOB_TYPE_VALUES)
        self.assertIn(result.seniority, SENIORITY_VALUES)
        self.assertIn(result.education, EDUCATION_VALUES)

    def test_non_list_skills_becomes_empty(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        payload = {"title": "Eng", "skills": "python, docker"}  # wrong type
        with patch("jobconnect.integrations.llm.openai.httpx.post",
                   return_value=_make_chat_response(payload)):
            result = parser.parse_resume("text", filename="cv.pdf")
        self.assertEqual(result.skills, [])


class TestOpenAIAdapterFailures(unittest.TestCase):
    def test_http_error_raises_parser_error(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        import httpx
        with patch("jobconnect.integrations.llm.openai.httpx.post",
                   side_effect=httpx.HTTPError("boom")):
            with self.assertRaises(ParserError) as ctx:
                parser.parse_resume("text")
        self.assertIn("LLM request failed", str(ctx.exception))

    def test_non_200_raises_parser_error(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        bad = MagicMock()
        bad.status_code = 500
        bad.text = "internal error"
        with patch("jobconnect.integrations.llm.openai.httpx.post", return_value=bad):
            with self.assertRaises(ParserError) as ctx:
                parser.parse_resume("text")
        self.assertIn("500", str(ctx.exception))

    def test_invalid_json_raises_parser_error(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"choices": [{"message": {"content": "not json"}}]}
        resp.text = "..."
        with patch("jobconnect.integrations.llm.openai.httpx.post", return_value=resp):
            with self.assertRaises(ParserError):
                parser.parse_resume("text")

    def test_payload_not_object_raises_parser_error(self) -> None:
        parser = OpenAIParser(api_key="sk-test", model="gpt-4o-mini")
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"choices": [{"message": {"content": "[1,2,3]"}}]}
        resp.text = "..."
        with patch("jobconnect.integrations.llm.openai.httpx.post", return_value=resp):
            with self.assertRaises(ParserError):
                parser.parse_resume("text")


# ---------------------------------------------------------------------------
# 4. get_parser() factory: env-driven fallback to local
# ---------------------------------------------------------------------------


class TestGetParserFactory(unittest.TestCase):
    def setUp(self) -> None:
        reset_parser_cache()
        self._env_snapshot = dict(os.environ)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._env_snapshot)
        reset_parser_cache()

    def test_default_is_local(self) -> None:
        os.environ.pop("LLM_PROVIDER", None)
        parser = get_parser()
        self.assertIsInstance(parser, LocalDeterministicParser)

    def test_openai_without_api_key_falls_back_to_local(self) -> None:
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ.pop("OPENAI_API_KEY", None)
        parser = get_parser()
        self.assertIsInstance(parser, LocalDeterministicParser)

    def test_openai_with_api_key_returns_openai(self) -> None:
        os.environ["LLM_PROVIDER"] = "openai"
        os.environ["OPENAI_API_KEY"] = "sk-test"
        parser = get_parser()
        self.assertIsInstance(parser, OpenAIParser)

    def test_unknown_provider_falls_back_to_local(self) -> None:
        os.environ["LLM_PROVIDER"] = "mystery"
        parser = get_parser()
        self.assertIsInstance(parser, LocalDeterministicParser)


# ---------------------------------------------------------------------------
# 5. Worker integration: parser_version flows through to parse_jobs UPDATE
# ---------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared
        self.executed: list[tuple[str, Any]] = []
        self._current: Any = None
        self.rowcount = 0

    def execute(self, sql: str, params: Any = None) -> None:
        self.executed.append((sql, params))
        self._current = self._shared.pop(0) if self._shared else None
        if isinstance(self._current, int):
            self.rowcount = self._current
            self._current = None

    def fetchone(self) -> Any:
        return self._current

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_) -> None:
        return None


class FakeConnection:
    def __init__(self, shared: list[Any], log: list[FakeCursor]) -> None:
        self._shared = shared
        self._log = log

    def cursor(self) -> FakeCursor:
        c = FakeCursor(self._shared)
        self._log.append(c)
        return c

    def commit(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_) -> None:
        return None


class TestWorkerUsesAdapterVersion(unittest.TestCase):
    """parser_version persisted on parse_jobs must come from the active adapter."""

    def test_worker_persists_local_parser_version(self) -> None:
        import io
        from unittest.mock import patch as _patch
        from jobconnect.modules.documents import worker as worker_module

        load_row = (
            99, 11, "candidate_resume", None, None, "queued",
            "documents/test.pdf", "application/pdf", "cv.pdf", 10,
        )
        resume_insert_row = (42,)
        shared: list[Any] = [
            load_row,             # _load_parse_job SELECT
            None,                 # _mark_processing UPDATE
            resume_insert_row,    # INSERT candidate_resumes RETURNING
            None,                 # INSERT candidate_resume_embeddings
            None,                 # UPDATE parse_jobs SET status='succeeded', parser_version=...
            None,                 # UPDATE uploaded_documents resume_id
            None,                 # UPDATE parse_jobs resume_id
            None,                 # _write_audit INSERT
        ]
        cursors: list[FakeCursor] = []

        def _conn():
            return FakeConnection(shared, cursors)

        mock_storage = MagicMock()
        mock_storage.open.return_value = io.BytesIO(b"Senior Python Engineer\nHa Noi")

        reset_parser_cache()  # ensure local adapter
        with _patch.object(worker_module, "get_connection", _conn), \
             _patch.object(worker_module, "get_storage", return_value=mock_storage), \
             _patch.object(worker_module, "extract_text",
                           return_value="Senior Python Engineer\nHa Noi"):
            worker_module._execute(99)

        # Find the UPDATE parse_jobs ... status='succeeded' statement
        success_update = None
        for c in cursors:
            for sql, params in c.executed:
                if "status = 'succeeded'" in sql and params is not None:
                    success_update = params
                    break
            if success_update is not None:
                break
        self.assertIsNotNone(success_update, "succeeded UPDATE not executed")
        # params order: (extracted_text, parser_version, embedding_version, parse_job_id)
        self.assertEqual(success_update[1], "local-v1")
        self.assertEqual(success_update[2], "hash-v1")


if __name__ == "__main__":
    unittest.main()
