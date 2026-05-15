"""Unit tests for routers/v2_catalog_router.py.

These tests stub psycopg at the connection/cursor level so they run without a
live PostgreSQL instance, matching the style of test_match_v2_router.py.
Coverage:
  * list endpoints return items + total and respect limit/offset
  * detail endpoints return 200 with full row
  * detail endpoints return 404 when row is absent
  * OpenAPI surface matches the four expected paths
"""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.v2_catalog_router import router


# ---------------------------------------------------------------------------
# Stub cursor / connection — minimal psycopg surface used by the router
# ---------------------------------------------------------------------------

class _StubCursor:
    """Mimics psycopg cursor used as a context manager.

    Caller seeds `responses` as an ordered list of objects:
      * tuple → returned by next fetchone()
      * list[tuple] → returned by next fetchall()
      * None → returned by fetchone() (simulates "row not found")
    """

    def __init__(self, responses):
        self._responses = list(responses)
        self.executed: list[tuple[str, tuple]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._responses.pop(0)

    def fetchall(self):
        return self._responses.pop(0)


class _StubConnection:
    def __init__(self, cursor: _StubCursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


def _make_conn(responses):
    cur = _StubCursor(responses)
    return _StubConnection(cur), cur


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class V2CatalogRouterTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)

    # ---------------- jobs/list ----------------

    def test_list_jobs_returns_items_and_total(self):
        rows = [
            (101, "Backend Engineer", "Hà Nội", "fulltime", "junior", ["python", "sql"]),
            (102, "Data Engineer", "TP. Hồ Chí Minh", "remote", "mid", ["python", "spark"]),
        ]
        conn, cur = _make_conn(responses=[(2,), rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/jobs")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["items"][0]["job_id"], 101)
        self.assertEqual(body["items"][0]["title"], "Backend Engineer")
        self.assertEqual(body["items"][0]["skills"], ["python", "sql"])
        self.assertTrue(conn.closed)

        # Default pagination values reach the SQL layer
        list_sql, list_params = cur.executed[1]
        self.assertIn("LIMIT", list_sql)
        self.assertIn("OFFSET", list_sql)
        self.assertEqual(list_params, (50, 0))

    def test_list_jobs_respects_pagination(self):
        rows = [(201, "QA", "Đà Nẵng", "parttime", "fresher", [])]
        conn, cur = _make_conn(responses=[(99,), rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get(
                "/api/v2/prototype/catalog/jobs",
                params={"limit": 5, "offset": 10},
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 99)
        self.assertEqual(len(body["items"]), 1)
        # Verify limit/offset propagated to SQL
        _, list_params = cur.executed[1]
        self.assertEqual(list_params, (5, 10))

    def test_list_jobs_rejects_invalid_pagination(self):
        # limit=0 violates ge=1
        res = self.client.get(
            "/api/v2/prototype/catalog/jobs",
            params={"limit": 0, "offset": 0},
        )
        self.assertEqual(res.status_code, 422)

        # offset=-1 violates ge=0
        res = self.client.get(
            "/api/v2/prototype/catalog/jobs",
            params={"limit": 10, "offset": -1},
        )
        self.assertEqual(res.status_code, 422)

    # ---------------- jobs/detail ----------------

    def test_get_job_detail_returns_full_row(self):
        row = (
            101,
            "Backend Engineer",
            ["python", "sql"],
            "3+ năm kinh nghiệm",
            "Hà Nội",
            "fulltime",
            "junior",
            "bachelor",
            ["aws_saa"],
        )
        conn, _ = _make_conn(responses=[row])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/jobs/101")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["job_id"], 101)
        self.assertEqual(body["title"], "Backend Engineer")
        self.assertEqual(body["skills"], ["python", "sql"])
        self.assertEqual(body["requirement"], "3+ năm kinh nghiệm")
        self.assertEqual(body["location"], "Hà Nội")
        self.assertEqual(body["job_type"], "fulltime")
        self.assertEqual(body["seniority"], "junior")
        self.assertEqual(body["education"], "bachelor")
        self.assertEqual(body["required_certifications"], ["aws_saa"])
        self.assertTrue(conn.closed)

    def test_get_job_detail_returns_404_when_missing(self):
        conn, _ = _make_conn(responses=[None])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/jobs/9999")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {"detail": "job not found"})
        self.assertTrue(conn.closed)

    # ---------------- cvs/list ----------------

    def test_list_cvs_returns_items_and_total(self):
        rows = [
            (1001, "Junior Backend", "Hà Nội", "fulltime", "junior", ["python"]),
            (1002, "Data Analyst", "TP. Hồ Chí Minh", "remote", "mid", ["sql", "python"]),
        ]
        conn, cur = _make_conn(responses=[(2,), rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/cvs")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["items"][0]["cv_id"], 1001)
        self.assertEqual(body["items"][1]["skills"], ["sql", "python"])

        _, list_params = cur.executed[1]
        self.assertEqual(list_params, (50, 0))

    def test_list_cvs_respects_pagination(self):
        rows = [(1500, "DevOps", "Hà Nội", "fulltime", "senior", ["k8s"])]
        conn, cur = _make_conn(responses=[(42,), rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get(
                "/api/v2/prototype/catalog/cvs",
                params={"limit": 1, "offset": 7},
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 42)
        self.assertEqual(len(body["items"]), 1)
        _, list_params = cur.executed[1]
        self.assertEqual(list_params, (1, 7))

    # ---------------- cvs/detail ----------------

    def test_get_cv_detail_returns_full_row(self):
        row = (
            1001,
            "Junior Backend",
            ["python", "fastapi"],
            "Tóm tắt ngắn",
            "2 năm làm backend",
            "Hà Nội",
            "fulltime",
            "junior",
            "bachelor",
            ["aws_ccp"],
        )
        conn, _ = _make_conn(responses=[row])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/cvs/1001")

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["cv_id"], 1001)
        self.assertEqual(body["title"], "Junior Backend")
        self.assertEqual(body["skills"], ["python", "fastapi"])
        self.assertEqual(body["summary"], "Tóm tắt ngắn")
        self.assertEqual(body["experience"], "2 năm làm backend")
        self.assertEqual(body["certifications"], ["aws_ccp"])

    def test_get_cv_detail_returns_404_when_missing(self):
        conn, _ = _make_conn(responses=[None])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/cvs/9999")

        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json(), {"detail": "cv not found"})

    # ---------------- list returns empty cleanly ----------------

    def test_list_jobs_empty(self):
        conn, _ = _make_conn(responses=[(0,), []])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/jobs")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"items": [], "total": 0})

    def test_list_cvs_handles_null_skills_array(self):
        # Defensive: psycopg returns None for SQL NULL on array columns.
        # Router should normalize to [].
        rows = [(2001, "Edge Case", "Hà Nội", "fulltime", "junior", None)]
        conn, _ = _make_conn(responses=[(1,), rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.get("/api/v2/prototype/catalog/cvs")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"][0]["skills"], [])

    # ---------------- OpenAPI contract ----------------

    def test_openapi_contract(self):
        schema = self.client.get("/openapi.json").json()
        catalog_paths = {
            path
            for path in schema["paths"]
            if path.startswith("/api/v2/prototype/catalog/")
        }
        # Browse + detail endpoints must always be present. Search endpoints
        # are validated separately in test_v2_catalog_search.py — assert the
        # browse/detail surface as a subset so adding new endpoints (search,
        # future facets, etc.) doesn't break this contract test.
        self.assertTrue(
            {
                "/api/v2/prototype/catalog/jobs",
                "/api/v2/prototype/catalog/jobs/{job_id}",
                "/api/v2/prototype/catalog/cvs",
                "/api/v2/prototype/catalog/cvs/{cv_id}",
            }.issubset(catalog_paths)
        )
        # 404 documented on detail endpoints
        for detail_path in (
            "/api/v2/prototype/catalog/jobs/{job_id}",
            "/api/v2/prototype/catalog/cvs/{cv_id}",
        ):
            responses = schema["paths"][detail_path]["get"]["responses"]
            self.assertIn("404", responses)


if __name__ == "__main__":
    unittest.main()
