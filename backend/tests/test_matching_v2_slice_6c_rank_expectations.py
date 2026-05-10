from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from matching_v2.db import (
    get_connection,
    load_candidate,
    load_job,
)
from matching_v2.filters import passes_hard_filter
from matching_v2.runner import run_for_cv, run_for_job
from routers.match_v2_router import router


BACKEND_DIR = Path(__file__).resolve().parents[1]
EXPECTATIONS_PATH = (
    BACKEND_DIR
    / "db_v2"
    / "scenarios"
    / "matching_v2_slice_6c_rank_expectations.json"
)

REQUIRED_EXPECTATION_FIELDS = {
    "anchor_type",
    "anchor_id",
    "top_k",
    "min_score",
    "expected_top_id",
    "must_include",
    "must_exclude",
    "must_exclude_reason",
    "must_rank_above",
}

EXPECTATION_GROUPS = (
    "main_expectations",
    "cv_to_jd_expectations",
    "hard_filter_expectations",
    "min_score_expectations",
    "determinism_expectations",
)

EXPECTED_V2_PATHS = {
    "/api/v2/prototype/matching/job/{job_id}/run",
    "/api/v2/prototype/matching/cv/{cv_id}/run",
}


def _load_expectations() -> dict[str, Any]:
    return json.loads(EXPECTATIONS_PATH.read_text(encoding="utf-8"))


def _connect_or_skip() -> Any:
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return conn
    except Exception as exc:  # pragma: no cover - environment guard
        raise unittest.SkipTest(
            f"PostgreSQL V2 unavailable; run through Docker Compose: {exc}"
        ) from exc


def _target_id(match: Any, anchor_type: str) -> int:
    return match.cv_id if anchor_type == "job" else match.job_id


def _run(conn: Any, expectation: dict[str, Any]) -> Any:
    if expectation["anchor_type"] == "job":
        return run_for_job(
            conn=conn,
            job_id=expectation["anchor_id"],
            top_k=expectation["top_k"],
            min_score=expectation["min_score"],
        )
    return run_for_cv(
        conn=conn,
        cv_id=expectation["anchor_id"],
        top_k=expectation["top_k"],
        min_score=expectation["min_score"],
    )


class Slice6CRankExpectationJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _load_expectations()

    def test_expectation_json_uses_required_fields_everywhere(self) -> None:
        for group in EXPECTATION_GROUPS:
            self.assertIn(group, self.fixture)
            self.assertGreater(len(self.fixture[group]), 0, group)
            for expectation in self.fixture[group]:
                missing = REQUIRED_EXPECTATION_FIELDS - set(expectation)
                self.assertFalse(
                    missing,
                    f"{group}:{expectation.get('id')} missing fields {sorted(missing)}",
                )
                self.assertIn(expectation["anchor_type"], {"job", "cv"})
                self.assertGreaterEqual(expectation["top_k"], 1)
                self.assertLessEqual(expectation["top_k"], 10)
                self.assertGreaterEqual(expectation["min_score"], 0.0)
                self.assertLessEqual(expectation["min_score"], 1.0)
                self.assertIsInstance(expectation["must_include"], list)
                self.assertIsInstance(expectation["must_exclude"], list)
                self.assertIsInstance(expectation["must_exclude_reason"], dict)
                self.assertIsInstance(expectation["must_rank_above"], list)
                for excluded_id in expectation["must_exclude"]:
                    self.assertIn(
                        str(excluded_id),
                        expectation["must_exclude_reason"],
                        f"{expectation['id']} missing exclusion reason for {excluded_id}",
                    )

    def test_main_expectations_cover_8_to_12_representative_job_anchors(self) -> None:
        job_anchor_ids = {
            item["anchor_id"]
            for item in self.fixture["main_expectations"]
            if item["anchor_type"] == "job"
        }
        self.assertGreaterEqual(len(job_anchor_ids), 8)
        self.assertLessEqual(len(job_anchor_ids), 12)
        self.assertEqual(job_anchor_ids, set(range(2001, 2011)))

    def test_hard_filter_expectations_use_min_score_zero_or_filter_total(self) -> None:
        for expectation in self.fixture["hard_filter_expectations"]:
            proves_filter = (
                expectation["min_score"] == 0.0
                or "total_after_filter" in expectation
                or "total_after_filter_min" in expectation
            )
            self.assertTrue(proves_filter, expectation["id"])

    def test_openapi_check_scope_is_v2_prototype_namespace_only(self) -> None:
        self.assertEqual(set(self.fixture["v2_prototype_paths"]), EXPECTED_V2_PATHS)

        app = FastAPI()
        app.include_router(router, prefix="/api")
        schema = TestClient(app).get("/openapi.json").json()
        v2_paths = {
            path
            for path in schema["paths"]
            if path.startswith("/api/v2/prototype/matching/")
        }
        self.assertEqual(v2_paths, EXPECTED_V2_PATHS)


class Slice6CBroadDatasetE2ETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = _load_expectations()
        cls.conn = _connect_or_skip()

    @classmethod
    def tearDownClass(cls) -> None:
        conn = getattr(cls, "conn", None)
        if conn is not None:
            conn.close()

    def test_broad_sql_seed_counts_are_present(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM job_posts_v2")
            job_count = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM candidate_profiles_v2")
            cv_count = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM job_embeddings_v2")
            job_embedding_count = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM candidate_embeddings_v2")
            cv_embedding_count = int(cur.fetchone()[0])
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = 'match_results_v2'
                )
                """
            )
            has_match_results_v2 = bool(cur.fetchone()[0])

        self.assertEqual(job_count, 10)
        self.assertEqual(cv_count, 34)
        self.assertEqual(job_embedding_count, 10)
        self.assertEqual(cv_embedding_count, 33)
        self.assertFalse(has_match_results_v2)

    def test_jd_to_cv_main_ranking_expectations(self) -> None:
        for expectation in self.fixture["main_expectations"]:
            with self.subTest(expectation=expectation["id"]):
                response = _run(self.conn, expectation)
                self._assert_response_contract(response)
                self._assert_expectation(response, expectation)

    def test_cv_to_jd_ranking_expectations(self) -> None:
        for expectation in self.fixture["cv_to_jd_expectations"]:
            with self.subTest(expectation=expectation["id"]):
                response = _run(self.conn, expectation)
                self._assert_response_contract(response)
                self._assert_expectation(response, expectation)

    def test_hard_filter_exclusions_are_proven_with_min_score_zero(self) -> None:
        for expectation in self.fixture["hard_filter_expectations"]:
            with self.subTest(expectation=expectation["id"]):
                response = _run(self.conn, expectation)
                self._assert_response_contract(response)
                self._assert_expectation(response, expectation)
                self.assertEqual(
                    expectation["min_score"],
                    0.0,
                    "hard-filter proof expectations must not depend on min_score",
                )
                self._assert_excluded_ids_fail_hard_filter(expectation)

    def test_min_score_exclusion_is_separate_from_hard_filter_exclusion(self) -> None:
        for expectation in self.fixture["min_score_expectations"]:
            with self.subTest(expectation=expectation["id"]):
                thresholded = _run(self.conn, expectation)
                self._assert_response_contract(thresholded)
                self._assert_expectation(thresholded, expectation)

                low_threshold = dict(expectation)
                low_threshold["min_score"] = 0.0
                unthresholded = _run(self.conn, low_threshold)
                returned_low = self._ids(unthresholded, expectation["anchor_type"])

                for excluded_id in expectation["must_exclude"]:
                    self.assertIn(
                        excluded_id,
                        returned_low,
                        f"{expectation['id']} should return {excluded_id} when min_score=0",
                    )
                    self._assert_pair_passes_hard_filter(expectation, excluded_id)

    def test_deterministic_ranking_when_repeated_on_same_seed(self) -> None:
        for expectation in self.fixture["determinism_expectations"]:
            with self.subTest(expectation=expectation["id"]):
                first = _run(self.conn, expectation)
                second = _run(self.conn, expectation)
                self.assertEqual(
                    self._stable_snapshot(first, expectation["anchor_type"]),
                    self._stable_snapshot(second, expectation["anchor_type"]),
                )

    def _assert_response_contract(self, response: Any) -> None:
        data = asdict(response)
        response_fields = {
            "anchor_type",
            "anchor_id",
            "total_candidates",
            "total_after_filter",
            "total_returned",
            "runtime_ms_total",
            "runtime_ms_filter",
            "runtime_ms_scoring",
            "runtime_ms_sort",
            "matches",
        }
        match_fields = {
            "rank",
            "cv_id",
            "job_id",
            "final_score",
            "title_score",
            "skills_score",
            "req_exp_score",
            "req_summary_score",
            "reasoning",
        }
        self.assertTrue(response_fields.issubset(data))
        self.assertGreaterEqual(response.total_candidates, response.total_after_filter)
        self.assertEqual(response.total_returned, len(response.matches))
        for field in (
            "runtime_ms_total",
            "runtime_ms_filter",
            "runtime_ms_scoring",
            "runtime_ms_sort",
        ):
            value = data[field]
            self.assertIsInstance(value, (int, float))
            self.assertGreaterEqual(value, 0.0)

        for match in data["matches"]:
            self.assertTrue(match_fields.issubset(match))
            for score_field in (
                "final_score",
                "title_score",
                "skills_score",
                "req_exp_score",
                "req_summary_score",
            ):
                self.assertIsInstance(match[score_field], (int, float))
                self.assertGreaterEqual(match[score_field], 0.0)
                self.assertLessEqual(match[score_field], 1.0)
            self.assertIsInstance(match["reasoning"], str)
            self.assertTrue(match["reasoning"].strip())

    def _assert_expectation(self, response: Any, expectation: dict[str, Any]) -> None:
        anchor_type = expectation["anchor_type"]
        ids = self._ids(response, anchor_type)
        index = {entity_id: idx for idx, entity_id in enumerate(ids)}

        self.assertEqual(response.anchor_type, anchor_type)
        self.assertEqual(response.anchor_id, expectation["anchor_id"])
        if "total_after_filter" in expectation:
            self.assertEqual(response.total_after_filter, expectation["total_after_filter"])
        if "total_after_filter_min" in expectation:
            self.assertGreaterEqual(
                response.total_after_filter,
                expectation["total_after_filter_min"],
            )

        self.assertTrue(ids, expectation["id"])
        self.assertEqual(ids[0], expectation["expected_top_id"], expectation["id"])
        for entity_id in expectation["must_include"]:
            self.assertIn(entity_id, index, expectation["id"])
        for entity_id in expectation["must_exclude"]:
            self.assertNotIn(entity_id, index, expectation["id"])
        for higher, lower in expectation["must_rank_above"]:
            self.assertIn(higher, index, expectation["id"])
            self.assertIn(lower, index, expectation["id"])
            self.assertLess(index[higher], index[lower], expectation["id"])

    def _assert_excluded_ids_fail_hard_filter(self, expectation: dict[str, Any]) -> None:
        for excluded_id in expectation["must_exclude"]:
            self._assert_pair_fails_hard_filter(expectation, excluded_id)

    def _assert_pair_fails_hard_filter(
        self,
        expectation: dict[str, Any],
        excluded_id: int,
    ) -> None:
        if expectation["anchor_type"] == "job":
            job = load_job(self.conn, expectation["anchor_id"])
            cv = load_candidate(self.conn, excluded_id)
        else:
            job = load_job(self.conn, excluded_id)
            cv = load_candidate(self.conn, expectation["anchor_id"])
        self.assertIsNotNone(job)
        self.assertIsNotNone(cv)
        self.assertFalse(passes_hard_filter(job, cv))

    def _assert_pair_passes_hard_filter(
        self,
        expectation: dict[str, Any],
        target_id: int,
    ) -> None:
        if expectation["anchor_type"] == "job":
            job = load_job(self.conn, expectation["anchor_id"])
            cv = load_candidate(self.conn, target_id)
        else:
            job = load_job(self.conn, target_id)
            cv = load_candidate(self.conn, expectation["anchor_id"])
        self.assertIsNotNone(job)
        self.assertIsNotNone(cv)
        self.assertTrue(passes_hard_filter(job, cv))

    def _ids(self, response: Any, anchor_type: str) -> list[int]:
        return [_target_id(match, anchor_type) for match in response.matches]

    def _stable_snapshot(self, response: Any, anchor_type: str) -> list[tuple[Any, ...]]:
        return [
            (
                _target_id(match, anchor_type),
                match.final_score,
                match.title_score,
                match.skills_score,
                match.req_exp_score,
                match.req_summary_score,
                match.reasoning,
            )
            for match in response.matches
        ]


if __name__ == "__main__":
    unittest.main()
