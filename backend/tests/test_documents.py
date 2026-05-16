"""Slice 4: Document Upload Foundation.

Covers:
- Multipart upload happy path returns {document, parse_job} and persists via Storage.
- Unsupported MIME types return 415.
- Files exceeding 10 MiB return 413.
- GET /documents/{id}/download-url returns {download_url, expires_at}.
- GET /documents/{id} detail includes parse_jobs list.
- POST /documents/{id}/parse-jobs writes an audit row on retry.
- OpenAPI exposes the new schemas and form-based upload contract.
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from jobconnect.integrations import storage as storage_module
from jobconnect.integrations.storage import LocalFilesystemStorage
from jobconnect.main import app
from jobconnect.modules.api import router as api_router


# ---------------------------------------------------------------------
# Shared fake DB ------------------------------------------------------
# ---------------------------------------------------------------------


class FakeCursor:
    def __init__(self, shared_script: list[Any], executed: Optional[list[tuple[Any, Any]]] = None):
        self._script = shared_script
        self._current: Any = None
        self.rowcount: int = 0
        self._executed = executed

    def execute(self, *args, **_kwargs) -> None:
        if self._executed is not None:
            sql = args[0] if args else None
            params = args[1] if len(args) > 1 else None
            self._executed.append((sql, params))
        self._current = self._script.pop(0) if self._script else None
        if isinstance(self._current, int):
            self.rowcount = self._current
            self._current = None

    def fetchone(self) -> Any:
        return self._current

    def fetchall(self) -> list[Any]:
        return list(self._current or [])

    def __enter__(self) -> "FakeCursor":
        return self

    def __exit__(self, *_exc) -> None:
        return None


class FakeConnection:
    def __init__(self, shared_script: list[Any], executed: Optional[list[tuple[Any, Any]]] = None):
        self._shared = shared_script
        self._executed = executed

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._shared, self._executed)

    def commit(self) -> None:
        return None

    def __enter__(self) -> "FakeConnection":
        return self

    def __exit__(self, *_exc) -> None:
        return None


def _fake_get_connection(script: Iterable[Any], executed: Optional[list[tuple[Any, Any]]] = None):
    shared = list(script)

    def _factory():
        return FakeConnection(shared, executed)

    return _factory


def _token(user_id: int, role: str) -> str:
    token, _ = api_router.create_access_token(user_id, role)
    return token


def _document_row(
    document_id: int = 11,
    owner_user_id: int = 10,
    object_key: str = "documents/abc.pdf",
    mime_type: str = "application/pdf",
    file_size_bytes: int = 1024,
) -> tuple:
    return (
        document_id,
        owner_user_id,
        "candidate_resume",
        object_key,
        None,                # file_url
        "resume.pdf",
        mime_type,
        file_size_bytes,
        None,                # resume_id
        None,                # job_id
        datetime(2026, 5, 16, 0, 0, 0),  # created_at
    )


def _parse_job_row(parse_job_id: int = 21, document_id: int = 11) -> tuple:
    return (
        parse_job_id,
        document_id,
        "candidate_resume",
        None,
        None,
        "queued",
        None,
        None,
        datetime(2026, 5, 16, 0, 0, 0),
        datetime(2026, 5, 16, 0, 0, 0),
    )


# ---------------------------------------------------------------------
# Storage adapter unit tests ------------------------------------------
# ---------------------------------------------------------------------


class LocalStorageUnitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.storage = LocalFilesystemStorage(root=self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_save_writes_file_and_returns_size(self) -> None:
        stored = self.storage.save(
            io.BytesIO(b"hello"),
            key_hint="cv.pdf",
            content_type="application/pdf",
            max_bytes=1024,
        )
        self.assertEqual(stored.size_bytes, 5)
        self.assertTrue(stored.object_key.startswith("documents/"))
        self.assertTrue(stored.object_key.endswith(".pdf"))
        self.assertTrue(self.storage.exists(stored.object_key))

    def test_save_rejects_oversize(self) -> None:
        with self.assertRaises(ValueError):
            self.storage.save(
                io.BytesIO(b"x" * 100),
                key_hint="cv.pdf",
                content_type="application/pdf",
                max_bytes=10,
            )

    def test_download_url_returns_iso_expires_at(self) -> None:
        link = self.storage.download_url("documents/abc.pdf", ttl_seconds=60)
        self.assertTrue(link.download_url.startswith("local://"))
        # ISO 8601 with timezone — parseable by fromisoformat.
        parsed = datetime.fromisoformat(link.expires_at)
        self.assertIsNotNone(parsed.tzinfo)


# ---------------------------------------------------------------------
# HTTP-level upload tests ---------------------------------------------
# ---------------------------------------------------------------------


class DocumentUploadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)
        self.tmpdir = tempfile.TemporaryDirectory()
        self._patch = patch.object(
            api_router,
            "get_storage",
            return_value=LocalFilesystemStorage(root=self.tmpdir.name),
        )
        self._patch.start()
        storage_module.reset_storage_cache()

    def tearDown(self) -> None:
        self._patch.stop()
        self.tmpdir.cleanup()
        storage_module.reset_storage_cache()

    def test_happy_path_returns_document_and_parse_job(self) -> None:
        token = _token(10, "candidate")
        executed: list[tuple[Any, Any]] = []
        script = [
            (10, "c@example.com", "candidate", "active"),  # current_user
            _document_row(),                                # INSERT uploaded_documents RETURNING
            _parse_job_row(),                               # INSERT parse_jobs RETURNING
            None,                                           # _audit insert
        ]
        parser = type("Parser", (), {"parser_version": "parser-test-v1"})()
        provider = type("Provider", (), {"embedding_version": "embedding-test-v9"})()
        with patch.object(api_router, "get_connection", _fake_get_connection(script, executed)), \
             patch.object(api_router, "get_parser", return_value=parser), \
             patch.object(api_router, "get_embedding_provider", return_value=provider):
            resp = self.client.post(
                "/api/documents",
                headers={"Authorization": f"Bearer {token}"},
                data={"document_type": "candidate_resume"},
                files={"file": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        body = resp.json()
        self.assertIn("document", body)
        self.assertIn("parse_job", body)
        self.assertEqual(body["document"]["document_id"], 11)
        self.assertEqual(body["parse_job"]["parse_job_id"], 21)
        self.assertEqual(body["parse_job"]["status"], "queued")
        parse_insert = next(
            params for sql, params in executed
            if isinstance(sql, str) and "INSERT INTO parse_jobs" in sql
        )
        self.assertEqual(parse_insert[-2:], ("parser-test-v1", "embedding-test-v9"))

    def test_unsupported_mime_returns_415(self) -> None:
        token = _token(10, "candidate")
        script = [(10, "c@example.com", "candidate", "active")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.post(
                "/api/documents",
                headers={"Authorization": f"Bearer {token}"},
                data={"document_type": "candidate_resume"},
                files={"file": ("cv.txt", b"plain text", "text/plain")},
            )
        self.assertEqual(resp.status_code, 415, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "unsupported_mime_type")

    def test_oversize_file_returns_413(self) -> None:
        token = _token(10, "candidate")
        script = [(10, "c@example.com", "candidate", "active")]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)), \
             patch.object(api_router, "MAX_DOCUMENT_BYTES", 10):
            resp = self.client.post(
                "/api/documents",
                headers={"Authorization": f"Bearer {token}"},
                data={"document_type": "candidate_resume"},
                files={"file": ("cv.pdf", b"x" * 100, "application/pdf")},
            )
        self.assertEqual(resp.status_code, 413, resp.text)
        self.assertEqual(resp.json()["error"]["code"], "file_too_large")


# ---------------------------------------------------------------------
# Download URL + detail tests -----------------------------------------
# ---------------------------------------------------------------------


class DocumentReadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, raise_server_exceptions=False)

    def test_download_url_returns_expires_at_iso(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),
            _document_row(),
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get(
                "/api/documents/11/download-url",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertIn("download_url", body)
        self.assertIn("expires_at", body)
        self.assertNotIn("expires_in_seconds", body)
        # expires_at must parse as ISO.
        parsed = datetime.fromisoformat(body["expires_at"])
        self.assertIsNotNone(parsed.tzinfo)

    def test_document_detail_includes_parse_jobs(self) -> None:
        token = _token(10, "candidate")
        script = [
            (10, "c@example.com", "candidate", "active"),  # current_user
            _document_row(),                                # _get_document_row
            [_parse_job_row()],                             # SELECT parse_jobs (fetchall)
        ]
        with patch.object(api_router, "get_connection", _fake_get_connection(script)):
            resp = self.client.get(
                "/api/documents/11",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 200, resp.text)
        body = resp.json()
        self.assertIn("parse_jobs", body)
        self.assertEqual(len(body["parse_jobs"]), 1)
        self.assertEqual(body["parse_jobs"][0]["parse_job_id"], 21)

    def test_parse_jobs_retry_returns_parse_job_detail(self) -> None:
        token = _token(10, "candidate")
        executed: list[tuple[Any, Any]] = []
        script = [
            (10, "c@example.com", "candidate", "active"),
            _document_row(),
            _parse_job_row(parse_job_id=22),
            None,  # audit insert
        ]
        parser = type("Parser", (), {"parser_version": "parser-test-v1"})()
        provider = type("Provider", (), {"embedding_version": "embedding-test-v9"})()
        with patch.object(api_router, "get_connection", _fake_get_connection(script, executed)), \
             patch.object(api_router, "get_parser", return_value=parser), \
             patch.object(api_router, "get_embedding_provider", return_value=provider):
            resp = self.client.post(
                "/api/documents/11/parse-jobs",
                headers={"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(resp.status_code, 201, resp.text)
        self.assertEqual(resp.json()["parse_job_id"], 22)
        parse_insert = next(
            params for sql, params in executed
            if isinstance(sql, str) and "INSERT INTO parse_jobs" in sql
        )
        self.assertEqual(parse_insert[-2:], ("parser-test-v1", "embedding-test-v9"))


# ---------------------------------------------------------------------
# OpenAPI shape tests --------------------------------------------------
# ---------------------------------------------------------------------


class OpenAPIDocumentShapeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_components_include_new_schemas(self) -> None:
        schema = self.client.get("/openapi.json").json()
        components = schema["components"]["schemas"]
        for name in (
            "DocumentDetail",
            "DocumentUploadResponse",
            "DocumentDownloadUrlResponse",
            "ParseJobDetail",
        ):
            self.assertIn(name, components, f"{name} missing from OpenAPI")
        # DocumentDetail must carry parse_jobs.
        self.assertIn("parse_jobs", components["DocumentDetail"]["properties"])
        # DocumentDownloadUrlResponse must use expires_at.
        download_props = components["DocumentDownloadUrlResponse"]["properties"]
        self.assertIn("expires_at", download_props)
        self.assertNotIn("expires_in_seconds", download_props)

    def test_post_documents_is_multipart(self) -> None:
        schema = self.client.get("/openapi.json").json()
        post_doc = schema["paths"]["/api/documents"]["post"]
        content_types = list(post_doc["requestBody"]["content"].keys())
        self.assertIn("multipart/form-data", content_types)
        self.assertNotIn("application/json", content_types)


if __name__ == "__main__":
    unittest.main()
