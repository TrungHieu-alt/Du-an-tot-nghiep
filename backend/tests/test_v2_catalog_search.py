"""Unit tests for the semantic search endpoints in v2_catalog_router.

Stub the psycopg surface (same approach as test_v2_catalog_router.py) so the
suite runs without a live PostgreSQL. Live integration is verified
separately via curl smoke in Phase A.4.

Coverage:
  * Empty / whitespace-only `q` short-circuits with no DB call.
  * Valid `q` issues the search SQL with the embedded vector literal,
    blend, blend, top_k bound in that order.
  * Negative scores from the cosine math are clamped to 0.
  * Scores above 1 are clamped to 1.
  * 422 for invalid body fields (top_k=0, blend_skills>1, q="").
  * cvs/search mirrors jobs/search.
  * OpenAPI advertises the two new paths.
"""

import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.v2_catalog_router import router
from v2_search.minilm import MiniLMUnavailableError


# ---------------------------------------------------------------------------
# Stub cursor / connection (same shape as test_v2_catalog_router.py)
# ---------------------------------------------------------------------------

class _StubCursor:
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
    def __init__(self, cursor):
        self._cursor = cursor
        self.closed = False

    def cursor(self):
        return self._cursor

    def close(self):
        self.closed = True


def _make_conn(responses):
    cur = _StubCursor(responses)
    return _StubConnection(cur), cur


class CatalogSearchTests(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(router, prefix="/api")
        self.client = TestClient(app)
        self.embed_patcher = patch(
            "routers.v2_catalog_router.embed_query",
            return_value=[0.01] * 384,
        )
        self.mock_embed_query = self.embed_patcher.start()
        self.addCleanup(self.embed_patcher.stop)

    # ---------------- jobs/search ----------------

    def test_empty_query_short_circuits_without_db(self):
        # No conn patch on purpose: if the endpoint hits the DB the test fails.
        with patch("routers.v2_catalog_router.get_connection") as mock_conn:
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "   ", "top_k": 10},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"items": [], "total": 0})
        mock_conn.assert_not_called()
        self.mock_embed_query.assert_not_called()

    def test_valid_query_executes_search_sql_with_bound_params(self):
        rows = [
            (4001, "Senior Backend", "Hà Nội", "remote", "senior", ["python"], 0.93),
            (4002, "Lead Frontend", "Hà Nội", "fulltime", "lead", ["react"], 0.71),
        ]
        conn, cur = _make_conn(responses=[rows])

        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend python", "top_k": 5, "blend_skills": 0.4},
            )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["total"], 2)
        self.assertEqual(len(body["items"]), 2)
        self.assertEqual(body["items"][0]["job_id"], 4001)
        self.assertAlmostEqual(body["items"][0]["score"], 0.93, places=5)
        self.assertEqual(body["items"][0]["skills"], ["python"])
        self.assertTrue(conn.closed)

        # Inspect bound params: vector, vector, blend, blend, top_k
        self.assertEqual(len(cur.executed), 1)
        sql, params = cur.executed[0]
        self.assertIn("emb_title <=>", sql)
        self.assertIn("emb_skills <=>", sql)
        self.assertEqual(len(params), 5)
        # Vector literals: pgvector format '[...]'
        self.assertTrue(params[0].startswith("[") and params[0].endswith("]"))
        self.assertEqual(params[0], params[1])  # same vector for both columns
        self.assertEqual(params[2], 0.4)        # blend
        self.assertEqual(params[3], 0.4)        # blend (used twice in expression)
        self.assertEqual(params[4], 5)          # top_k

    def test_negative_score_is_clamped_to_zero(self):
        rows = [
            (4001, "X", "Hà Nội", "remote", "junior", [], -0.05),
        ]
        conn, _ = _make_conn(responses=[rows])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"][0]["score"], 0.0)

    def test_score_above_one_is_clamped_to_one(self):
        rows = [
            (4001, "X", "Hà Nội", "remote", "junior", [], 1.2),
        ]
        conn, _ = _make_conn(responses=[rows])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"][0]["score"], 1.0)

    def test_default_top_k_is_20_and_default_blend_is_03(self):
        conn, cur = _make_conn(responses=[[]])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "anything"},
            )
        self.assertEqual(res.status_code, 200)
        _, params = cur.executed[0]
        self.assertAlmostEqual(params[2], 0.3, places=6)
        self.assertEqual(params[4], 20)

    def test_handles_null_skills_array_in_row(self):
        rows = [
            (4001, "X", "Hà Nội", "remote", "junior", None, 0.5),
        ]
        conn, _ = _make_conn(responses=[rows])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "anything"},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["items"][0]["skills"], [])

    def test_local_minilm_unavailable_returns_503_without_remote_fallback(self):
        with patch(
            "routers.v2_catalog_router.embed_query",
            side_effect=MiniLMUnavailableError("missing local model"),
        ), patch("routers.v2_catalog_router.get_connection") as mock_conn:
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend"},
            )

        self.assertEqual(res.status_code, 503)
        self.assertIn("Local MiniLM", res.json()["detail"])
        mock_conn.assert_not_called()

    # ---------------- validation (422) ----------------

    def test_empty_string_query_rejected_at_schema(self):
        # Pydantic min_length=1 → 422 before endpoint logic runs.
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": ""},
        )
        self.assertEqual(res.status_code, 422)

    def test_top_k_zero_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "top_k": 0},
        )
        self.assertEqual(res.status_code, 422)

    def test_top_k_above_50_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "top_k": 51},
        )
        self.assertEqual(res.status_code, 422)

    def test_blend_skills_above_one_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "blend_skills": 1.2},
        )
        self.assertEqual(res.status_code, 422)

    def test_query_too_long_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "a" * 201},
        )
        self.assertEqual(res.status_code, 422)

    # ---------------- cvs/search mirrors jobs/search ----------------

    def test_cvs_search_executes_with_correct_table(self):
        rows = [
            (3001, "Senior Backend", "Hà Nội", "remote", "senior", ["python"], 0.88),
        ]
        conn, cur = _make_conn(responses=[rows])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/cvs/search",
                json={"q": "backend"},
            )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["items"][0]["cv_id"], 3001)
        self.assertAlmostEqual(body["items"][0]["score"], 0.88, places=5)

        sql, _ = cur.executed[0]
        self.assertIn("candidate_profiles_v2", sql)
        self.assertIn("candidate_embeddings_v2", sql)

    def test_cvs_search_empty_query_short_circuits(self):
        with patch("routers.v2_catalog_router.get_connection") as mock_conn:
            res = self.client.post(
                "/api/v2/prototype/catalog/cvs/search",
                json={"q": "   "},
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"items": [], "total": 0})
        mock_conn.assert_not_called()

    # ---------------- Filters ----------------

    def test_search_jobs_with_location_filter(self):
        conn, cur = _make_conn(responses=[[]])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend", "location": "Hà Nội"},
            )
        self.assertEqual(res.status_code, 200)
        sql, params = cur.executed[0]
        # SQL must contain alias-prefixed condition
        self.assertIn("AND j.location = %s", sql)
        # Params: (q_vec, q_vec, 'Hà Nội', blend, blend, top_k)
        self.assertEqual(len(params), 6)
        self.assertEqual(params[2], "Hà Nội")
        self.assertAlmostEqual(params[3], 0.3, places=6)  # default blend
        self.assertEqual(params[5], 20)                   # default top_k

    def test_search_jobs_with_all_three_filters(self):
        conn, cur = _make_conn(responses=[[]])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={
                    "q": "backend",
                    "location": "Hà Nội",
                    "job_type": "remote",
                    "seniority": "senior",
                    "blend_skills": 0.4,
                    "top_k": 10,
                },
            )
        self.assertEqual(res.status_code, 200)
        sql, params = cur.executed[0]
        self.assertIn("AND j.location = %s", sql)
        self.assertIn("AND j.job_type = %s", sql)
        self.assertIn("AND j.seniority = %s", sql)
        # Params order: q_vec, q_vec, location, job_type, seniority, blend, blend, top_k
        self.assertEqual(len(params), 8)
        self.assertEqual(params[2], "Hà Nội")
        self.assertEqual(params[3], "remote")
        self.assertEqual(params[4], "senior")
        self.assertAlmostEqual(params[5], 0.4, places=6)
        self.assertAlmostEqual(params[6], 0.4, places=6)
        self.assertEqual(params[7], 10)

    def test_search_jobs_no_filters_emits_no_extra_where(self):
        conn, cur = _make_conn(responses=[[]])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/jobs/search",
                json={"q": "backend"},
            )
        self.assertEqual(res.status_code, 200)
        sql, params = cur.executed[0]
        self.assertNotIn("AND j.location", sql)
        self.assertNotIn("AND j.job_type", sql)
        self.assertNotIn("AND j.seniority", sql)
        self.assertEqual(len(params), 5)  # unchanged from no-filter contract

    def test_search_cvs_with_filters_uses_c_alias(self):
        conn, cur = _make_conn(responses=[[]])
        with patch("routers.v2_catalog_router.get_connection", return_value=conn):
            res = self.client.post(
                "/api/v2/prototype/catalog/cvs/search",
                json={"q": "python", "seniority": "mid", "job_type": "fulltime"},
            )
        self.assertEqual(res.status_code, 200)
        sql, params = cur.executed[0]
        # CV table aliased as `c`, not `j`
        self.assertIn("AND c.job_type = %s", sql)
        self.assertIn("AND c.seniority = %s", sql)
        self.assertNotIn(" j.location", sql)  # belt-and-braces
        # Order matches helper: location absent → skipped; job_type before seniority
        self.assertEqual(params[2], "fulltime")
        self.assertEqual(params[3], "mid")

    def test_invalid_location_enum_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "location": "saigon"},
        )
        self.assertEqual(res.status_code, 422)

    def test_invalid_job_type_enum_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "job_type": "contract"},
        )
        self.assertEqual(res.status_code, 422)

    def test_invalid_seniority_enum_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/jobs/search",
            json={"q": "x", "seniority": "principal"},
        )
        self.assertEqual(res.status_code, 422)

    def test_cv_search_invalid_location_rejected(self):
        res = self.client.post(
            "/api/v2/prototype/catalog/cvs/search",
            json={"q": "x", "location": "hanoi"},  # missing underscore
        )
        self.assertEqual(res.status_code, 422)

    # ---------------- OpenAPI ----------------

    def test_openapi_advertises_search_paths(self):
        schema = self.client.get("/openapi.json").json()
        catalog_search_paths = {
            path
            for path in schema["paths"]
            if path.startswith("/api/v2/prototype/catalog/")
            and path.endswith("/search")
        }
        self.assertEqual(
            catalog_search_paths,
            {
                "/api/v2/prototype/catalog/jobs/search",
                "/api/v2/prototype/catalog/cvs/search",
            },
        )
        # Pydantic constraints surface in the request schema
        req = schema["components"]["schemas"]["CatalogSearchRequest"]
        self.assertEqual(req["properties"]["top_k"]["minimum"], 1)
        self.assertEqual(req["properties"]["top_k"]["maximum"], 50)
        self.assertEqual(req["properties"]["blend_skills"]["minimum"], 0.0)
        self.assertEqual(req["properties"]["blend_skills"]["maximum"], 1.0)
        self.assertEqual(req["properties"]["q"]["minLength"], 1)
        self.assertEqual(req["properties"]["q"]["maxLength"], 200)


if __name__ == "__main__":
    unittest.main()
