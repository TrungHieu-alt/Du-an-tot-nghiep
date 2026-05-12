#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
EXPECTATIONS_PATH="${EXPECTATIONS_PATH:-backend/db_v2/scenarios/matching_v2_slice_6c_rank_expectations.json}"

echo "[live-smoke] starting postgres and backend"
docker compose up -d postgres backend

echo "[live-smoke] resetting and seeding PostgreSQL from backend container"
docker compose exec backend python db_v2/reset.py

echo "[live-smoke] waiting for OpenAPI at ${API_BASE_URL}/openapi.json"
for _ in $(seq 1 60); do
  if curl -fsS "${API_BASE_URL}/openapi.json" >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS "${API_BASE_URL}/openapi.json" >/dev/null

python3 - <<'PY'
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
expectations_path = Path(os.getenv("EXPECTATIONS_PATH", "backend/db_v2/scenarios/matching_v2_slice_6c_rank_expectations.json"))
fixture = json.loads(expectations_path.read_text(encoding="utf-8"))

required_response_fields = {
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
required_match_fields = {
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
runtime_fields = {
    "runtime_ms_total",
    "runtime_ms_filter",
    "runtime_ms_scoring",
    "runtime_ms_sort",
}
score_fields = {
    "final_score",
    "title_score",
    "skills_score",
    "req_exp_score",
    "req_summary_score",
}


def post_json(path: str, *, top_k: int, min_score: float) -> dict:
    payload = json.dumps({"top_k": top_k, "min_score": min_score}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}{path}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            assert res.status == 200, f"{path}: expected 200, got {res.status}"
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{path}: expected 200, got {exc.code}: {body}") from exc


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{base_url}{path}", timeout=20) as res:
        assert res.status == 200, f"{path}: expected 200, got {res.status}"
        return json.loads(res.read().decode("utf-8"))


def assert_contract(data: dict, expectation: dict) -> dict:
    anchor_type = expectation["anchor_type"]
    anchor_id = expectation["anchor_id"]
    missing = required_response_fields - set(data)
    assert not missing, f"{anchor_type}: missing response fields {sorted(missing)}"
    assert data["anchor_type"] == anchor_type, data
    assert data["anchor_id"] == anchor_id, data
    assert data["total_candidates"] == (34 if anchor_type == "job" else 10), data
    if "total_after_filter" in expectation:
        assert data["total_after_filter"] == expectation["total_after_filter"], data
    assert data["total_after_filter"] >= 1, data
    assert data["total_returned"] >= 1, data
    for field in runtime_fields:
        assert isinstance(data[field], (int, float)), f"{field} must be numeric"
        assert data[field] >= 0, f"{field} must be >= 0"

    first = data["matches"][0]
    missing_match = required_match_fields - set(first)
    assert not missing_match, f"{anchor_type}: missing match fields {sorted(missing_match)}"
    assert first["rank"] == 1, first
    for field in score_fields:
        assert isinstance(first[field], (int, float)), f"{field} must be numeric"
        assert 0 <= first[field] <= 1, f"{field} must be in [0, 1]"
    assert isinstance(first["reasoning"], str) and first["reasoning"].strip(), first
    return first


def target_ids(data: dict, anchor_type: str) -> list[int]:
    field = "cv_id" if anchor_type == "job" else "job_id"
    return [match[field] for match in data["matches"]]


def assert_expectation(data: dict, expectation: dict) -> None:
    ids = target_ids(data, expectation["anchor_type"])
    assert ids[0] == expectation["expected_top_id"], (expectation["id"], ids)
    for entity_id in expectation["must_include"]:
        assert entity_id in ids, (expectation["id"], entity_id, ids)
    for entity_id in expectation["must_exclude"]:
        assert entity_id not in ids, (expectation["id"], entity_id, ids)
    positions = {entity_id: idx for idx, entity_id in enumerate(ids)}
    for higher, lower in expectation["must_rank_above"]:
        assert positions[higher] < positions[lower], (expectation["id"], higher, lower, ids)


schema = get_json("/openapi.json")
expected_paths = set(fixture["v2_prototype_paths"])
actual_v2_paths = {
    path
    for path in schema["paths"]
    if path.startswith("/api/v2/prototype/matching/")
}
assert actual_v2_paths == expected_paths, actual_v2_paths

job_expectation = next(
    item for item in fixture["main_expectations"] if item["id"] == "job2006_devops_cert_ranking"
)
job_response = post_json(
    f"/api/v2/prototype/matching/job/{job_expectation['anchor_id']}/run",
    top_k=job_expectation["top_k"],
    min_score=job_expectation["min_score"],
)
job_top = assert_contract(job_response, job_expectation)
assert_expectation(job_response, job_expectation)

cv_expectation = next(
    item for item in fixture["cv_to_jd_expectations"] if item["id"] == "cv1006_devops_reverse_ranking"
)
cv_response = post_json(
    f"/api/v2/prototype/matching/cv/{cv_expectation['anchor_id']}/run",
    top_k=cv_expectation["top_k"],
    min_score=cv_expectation["min_score"],
)
cv_top = assert_contract(cv_response, cv_expectation)
assert_expectation(cv_response, cv_expectation)

print("[live-smoke] JD -> CV top match:", json.dumps(job_top, sort_keys=True))
print("[live-smoke] CV -> JD top match:", json.dumps(cv_top, sort_keys=True))
print("[live-smoke] OpenAPI V2 paths:", json.dumps(sorted(actual_v2_paths)))
print("[live-smoke] OK")
PY
