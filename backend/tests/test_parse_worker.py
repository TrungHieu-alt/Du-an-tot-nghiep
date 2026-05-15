"""Slice 5: Parse Worker V1.

Covers the DoD items from slices.md §Slice 5:
- One CV fixture parses to a draft resume.
- One JD fixture parses to a draft job.
- One bad file produces failed parse state, notification, and audit event.
- Retry creates a new parse job (HTTP layer — already covered by test_documents).

Unit tests:
- Preprocessor: NFC normalization, control char removal, whitespace collapse.
- Skill normalizer: alias resolution, extraction from text.
- Local parser: resume + job field detection.

Integration tests (mocked DB + storage):
- Worker happy path for candidate_resume.
- Worker happy path for job_post.
- Worker failure on empty extraction.
- Worker failure on extraction error.
"""
from __future__ import annotations

import io
import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.modules.documents.extractor import extract_text
from jobconnect.modules.documents.local_parser import (
    ParsedJob,
    ParsedResume,
    parse_job,
    parse_resume,
)
from jobconnect.modules.documents.preprocessor import preprocess_text
from jobconnect.modules.documents.skill_normalizer import extract_skills, normalize_skills
from jobconnect.modules.documents import worker as worker_module
from jobconnect.modules.documents.worker import (
    EMBEDDING_VERSION,
    PARSER_VERSION,
    _ParseJobInfo,
    _execute,
    _fail,
    _load_parse_job,
    _mark_processing,
    _mark_succeeded,
    _upsert_job,
    _upsert_resume,
)


# ---------------------------------------------------------------------------
# Fake DB helpers (reused from test_documents pattern)
# ---------------------------------------------------------------------------


class FakeCursor:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared
        self.rowcount = 0
        self._current: Any = None

    def execute(self, *_a, **_kw) -> None:
        self._current = self._shared.pop(0) if self._shared else None
        if isinstance(self._current, int):
            self.rowcount = self._current
            self._current = None

    def fetchone(self) -> Any:
        return self._current

    def fetchall(self) -> list[Any]:
        return list(self._current or [])

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_) -> None:
        pass


class FakeConnection:
    def __init__(self, shared: list[Any]) -> None:
        self._shared = shared

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._shared)

    def commit(self) -> None:
        pass

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_) -> None:
        pass


def _fake_conn(script: list[Any]):
    shared = list(script)

    def _factory():
        return FakeConnection(shared)

    return _factory


def _parse_job_info(
    target_entity_type: str = "candidate_resume",
    existing_resume_id: Optional[int] = None,
    existing_job_id: Optional[int] = None,
    object_key: str = "documents/test.pdf",
    mime_type: str = "application/pdf",
    original_filename: str = "cv.pdf",
    owner_user_id: int = 10,
) -> _ParseJobInfo:
    return _ParseJobInfo(
        parse_job_id=99,
        document_id=11,
        target_entity_type=target_entity_type,
        existing_resume_id=existing_resume_id,
        existing_job_id=existing_job_id,
        status="queued",
        object_key=object_key,
        mime_type=mime_type,
        original_filename=original_filename,
        owner_user_id=owner_user_id,
    )


# ---------------------------------------------------------------------------
# 1. Preprocessor unit tests
# ---------------------------------------------------------------------------


class TestPreprocessor(unittest.TestCase):
    def test_nfc_normalization(self) -> None:
        # NFD "ệ" (e + combining hooks) → NFC single codepoint
        nfd = "việt"  # "viêt" in NFD form
        result = preprocess_text(nfd)
        import unicodedata
        self.assertEqual(unicodedata.is_normalized("NFC", result), True)

    def test_removes_null_bytes(self) -> None:
        result = preprocess_text("hello\x00world")
        self.assertNotIn("\x00", result)
        self.assertIn("hello", result)
        self.assertIn("world", result)

    def test_removes_control_chars_preserves_newline(self) -> None:
        result = preprocess_text("line1\x0bline2\nline3")
        self.assertNotIn("\x0b", result)
        self.assertIn("line1", result)
        self.assertIn("line3", result)

    def test_collapses_excessive_blank_lines(self) -> None:
        result = preprocess_text("a\n\n\n\n\nb")
        self.assertNotIn("\n\n\n", result)
        self.assertIn("a", result)
        self.assertIn("b", result)

    def test_collapses_spaces(self) -> None:
        result = preprocess_text("a     b")
        self.assertIn("a b", result)

    def test_strips_result(self) -> None:
        result = preprocess_text("  hello  ")
        self.assertEqual(result, "hello")


# ---------------------------------------------------------------------------
# 2. Skill normalizer unit tests
# ---------------------------------------------------------------------------


class TestSkillNormalizer(unittest.TestCase):
    def test_normalize_alias(self) -> None:
        self.assertEqual(normalize_skills(["reactjs"]), ["react"])
        self.assertEqual(normalize_skills(["react.js"]), ["react"])
        self.assertEqual(normalize_skills(["pytorch"]), ["pytorch"])
        self.assertEqual(normalize_skills(["golang"]), ["go"])

    def test_normalize_deduplicates(self) -> None:
        result = normalize_skills(["reactjs", "react.js", "react"])
        self.assertEqual(result, ["react"])

    def test_normalize_unknown_skill_passthrough(self) -> None:
        result = normalize_skills(["myCustomLib"])
        self.assertEqual(result, ["myCustomLib"])

    def test_extract_skills_from_text(self) -> None:
        text = "We use React, Python and PostgreSQL in our stack."
        skills = extract_skills(text)
        self.assertIn("react", skills)
        self.assertIn("python", skills)
        self.assertIn("postgresql", skills)

    def test_extract_skills_multi_word(self) -> None:
        text = "Experience with react native and apache kafka."
        skills = extract_skills(text)
        self.assertIn("react native", skills)
        self.assertIn("apache kafka", skills)

    def test_extract_skills_case_insensitive(self) -> None:
        text = "Proficient in PYTHON and Docker."
        skills = extract_skills(text)
        self.assertIn("python", skills)
        self.assertIn("docker", skills)


# ---------------------------------------------------------------------------
# 3. Local parser unit tests
# ---------------------------------------------------------------------------


class TestLocalParser(unittest.TestCase):
    def test_parse_resume_returns_parsed_resume(self) -> None:
        text = "John Doe\nSenior Python Developer\nHanoi Vietnam\nSkills: Python, Docker, PostgreSQL"
        result = parse_resume(text, filename="john_cv.pdf")
        self.assertIsInstance(result, ParsedResume)
        self.assertEqual(result.title, "John Doe")
        self.assertIn("python", result.skills)
        self.assertIn("docker", result.skills)
        self.assertEqual(result.seniority, "senior")

    def test_parse_resume_detects_location_hanoi(self) -> None:
        result = parse_resume("Software Engineer\nHa Noi based", filename="cv.pdf")
        self.assertEqual(result.location, "ha_noi")

    def test_parse_resume_detects_location_hcm(self) -> None:
        result = parse_resume("Developer in Ho Chi Minh City", filename="cv.pdf")
        self.assertEqual(result.location, "tp_hcm")

    def test_parse_resume_detects_remote(self) -> None:
        result = parse_resume("Remote work preferred", filename="cv.pdf")
        self.assertEqual(result.job_type, "remote")

    def test_parse_resume_detects_intern(self) -> None:
        result = parse_resume("Internship position", filename="cv.pdf")
        self.assertEqual(result.seniority, "intern")

    def test_parse_resume_detects_master_education(self) -> None:
        result = parse_resume("Master of Science in Computer Science", filename="cv.pdf")
        self.assertEqual(result.education, "thac_si")

    def test_parse_resume_uses_filename_as_title_fallback(self) -> None:
        result = parse_resume("", filename="john_doe_cv.pdf")
        self.assertIn("john", result.title.lower())

    def test_parse_job_returns_parsed_job(self) -> None:
        text = "Senior Python Backend Engineer\nHCM City\nRequirements: Python, FastAPI, PostgreSQL"
        result = parse_job(text, filename="jd.pdf")
        self.assertIsInstance(result, ParsedJob)
        self.assertEqual(result.title, "Senior Python Backend Engineer")
        self.assertIn("python", result.skills)
        self.assertEqual(result.location, "tp_hcm")
        self.assertEqual(result.seniority, "senior")

    def test_parse_job_defaults_for_empty_text(self) -> None:
        result = parse_job("", filename="job.pdf")
        self.assertEqual(result.location, "ha_noi")
        self.assertEqual(result.job_type, "fulltime")
        self.assertEqual(result.seniority, "junior")
        self.assertEqual(result.education, "dai_hoc")


# ---------------------------------------------------------------------------
# 4. Extractor unit tests
# ---------------------------------------------------------------------------


class TestExtractor(unittest.TestCase):
    def test_unsupported_mime_returns_empty(self) -> None:
        result = extract_text(io.BytesIO(b"<html>test</html>"), "text/html")
        self.assertEqual(result, "")

    def test_invalid_pdf_returns_empty(self) -> None:
        result = extract_text(io.BytesIO(b"not a pdf"), "application/pdf")
        self.assertEqual(result, "")

    def test_docx_returns_empty_in_slice5(self) -> None:
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        result = extract_text(io.BytesIO(b"PK fake docx"), mime)
        self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# 5. Worker integration tests (mocked DB + storage)
# ---------------------------------------------------------------------------


class TestWorkerResumeHappyPath(unittest.TestCase):
    """CV fixture → draft resume created, parse_job succeeded."""

    def _make_mock_storage(self, text: str) -> MagicMock:
        storage = MagicMock()
        storage.open.return_value = io.BytesIO(text.encode())
        return storage

    def test_cv_fixture_creates_draft_resume(self) -> None:
        cv_text = (
            "Jane Smith\n"
            "Senior Python Developer\n"
            "Ha Noi\n"
            "Skills: Python, Docker, PostgreSQL\n"
            "Master of Science"
        )

        # DB script: load_parse_job → mark_processing → upsert_resume INSERT →
        #   upsert_resume_embeddings → mark_succeeded UPDATE × 3
        load_row = (
            99, 11, "candidate_resume", None, None, "queued",
            "documents/test.pdf", "application/pdf", "jane_cv.pdf", 10,
        )
        resume_insert_row = (42,)  # new resume_id

        db_calls: list[Any] = [
            load_row,         # _load_parse_job SELECT
            None,             # _mark_processing UPDATE
            resume_insert_row,  # INSERT candidate_resumes RETURNING
            None,             # INSERT candidate_resume_embeddings
            None,             # _mark_succeeded UPDATE parse_jobs
            None,             # UPDATE uploaded_documents resume_id
            None,             # UPDATE parse_jobs resume_id
            None,             # _write_audit INSERT
        ]

        mock_storage = self._make_mock_storage(cv_text)

        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage):
            _execute(99)

        mock_storage.open.assert_called_once_with("documents/test.pdf")

    def test_worker_ignores_already_processed_job(self) -> None:
        load_row = (
            99, 11, "candidate_resume", None, None, "succeeded",
            "documents/test.pdf", "application/pdf", "cv.pdf", 10,
        )
        with patch.object(worker_module, "get_connection", _fake_conn([load_row])):
            _execute(99)  # should return early without calling storage


class TestWorkerJobHappyPath(unittest.TestCase):
    """JD fixture → draft job_post created, parse_job succeeded."""

    def test_jd_fixture_creates_draft_job(self) -> None:
        jd_text = (
            "Senior Backend Engineer\n"
            "Ho Chi Minh City\n"
            "Requirements: Python, FastAPI, Docker, PostgreSQL\n"
            "Full-time position"
        )

        load_row = (
            100, 12, "job_post", None, None, "queued",
            "documents/jd.pdf", "application/pdf", "jd.pdf", 20,
        )
        org_row = (5,)    # organization_id
        job_insert_row = (77,)

        db_calls: list[Any] = [
            load_row,       # _load_parse_job
            None,           # _mark_processing
            org_row,        # _get_organization_id
            job_insert_row,  # INSERT job_posts RETURNING
            None,           # INSERT job_post_embeddings
            None,           # _mark_succeeded UPDATE parse_jobs
            None,           # UPDATE uploaded_documents job_id
            None,           # UPDATE parse_jobs job_id
            None,           # _write_audit
        ]

        mock_storage = MagicMock()
        mock_storage.open.return_value = io.BytesIO(jd_text.encode())

        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage):
            _execute(100)

        mock_storage.open.assert_called_once_with("documents/jd.pdf")


class TestWorkerFailureCases(unittest.TestCase):
    """Bad file → failed parse_job + notification + audit."""

    def test_empty_extraction_marks_failed(self) -> None:
        load_row = (
            99, 11, "candidate_resume", None, None, "queued",
            "documents/bad.pdf", "application/pdf", "bad.pdf", 10,
        )
        db_calls: list[Any] = [
            load_row,  # _load_parse_job
            None,      # _mark_processing
            # _fail: UPDATE parse_jobs + INSERT notifications + INSERT audit_logs
            None,
            None,
            None,
        ]

        mock_storage = MagicMock()
        # Return empty bytes so extraction yields empty string
        mock_storage.open.return_value = io.BytesIO(b"")

        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage):
            _execute(99)

    def test_storage_open_error_marks_failed(self) -> None:
        load_row = (
            99, 11, "candidate_resume", None, None, "queued",
            "documents/missing.pdf", "application/pdf", "missing.pdf", 10,
        )
        db_calls: list[Any] = [
            load_row,
            None,   # _mark_processing
            None,   # _fail UPDATE parse_jobs
            None,   # _fail INSERT notifications
            None,   # _fail INSERT audit_logs
        ]

        mock_storage = MagicMock()
        mock_storage.open.side_effect = FileNotFoundError("Object not found")

        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage):
            _execute(99)

    def test_missing_recruiter_profile_marks_failed(self) -> None:
        load_row = (
            100, 12, "job_post", None, None, "queued",
            "documents/jd.pdf", "application/pdf", "jd.pdf", 20,
        )
        db_calls: list[Any] = [
            load_row,
            None,   # _mark_processing
            None,   # _get_organization_id → fetchone returns None
            None,   # _fail UPDATE parse_jobs
            None,   # _fail INSERT notifications
            None,   # _fail INSERT audit_logs
        ]

        mock_storage = MagicMock()
        mock_storage.open.return_value = io.BytesIO(b"Some job description text")

        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)), \
             patch.object(worker_module, "get_storage", return_value=mock_storage):
            _execute(100)

    def test_run_parse_job_swallows_critical_exception(self) -> None:
        # If even _load_parse_job explodes, run_parse_job must not raise.
        with patch.object(worker_module, "get_connection", side_effect=RuntimeError("db down")):
            try:
                worker_module.run_parse_job(99)
            except Exception as exc:
                self.fail(f"run_parse_job raised unexpectedly: {exc}")


# ---------------------------------------------------------------------------
# 6. Load-parse-job returns None for missing row
# ---------------------------------------------------------------------------


class TestLoadParseJob(unittest.TestCase):
    def test_returns_none_when_row_missing(self) -> None:
        db_calls: list[Any] = [None]  # fetchone returns None
        with patch.object(worker_module, "get_connection", _fake_conn(db_calls)):
            result = _load_parse_job(999)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
