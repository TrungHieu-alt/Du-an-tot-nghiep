#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

echo "[live-smoke] starting postgres, mongo, backend"
docker compose up -d postgres mongo backend

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

base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

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


def post_json(path: str) -> dict:
    payload = json.dumps({"top_k": 10, "min_score": 0.7}).encode("utf-8")
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


def assert_contract(data: dict, *, anchor_type: str, anchor_id: int) -> dict:
    missing = required_response_fields - set(data)
    assert not missing, f"{anchor_type}: missing response fields {sorted(missing)}"
    assert data["anchor_type"] == anchor_type, data
    assert data["anchor_id"] == anchor_id, data
    assert data["total_candidates"] == 5, data
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


job_response = post_json("/api/v2/prototype/matching/job/2003/run")
job_top = assert_contract(job_response, anchor_type="job", anchor_id=2003)
assert job_top["cv_id"] == 1003, job_response
assert job_top["job_id"] == 2003, job_response

cv_response = post_json("/api/v2/prototype/matching/cv/1003/run")
cv_top = assert_contract(cv_response, anchor_type="cv", anchor_id=1003)
assert cv_top["cv_id"] == 1003, cv_response
assert cv_top["job_id"] == 2003, cv_response

print("[live-smoke] JD -> CV top match:", json.dumps(job_top, sort_keys=True))
print("[live-smoke] CV -> JD top match:", json.dumps(cv_top, sort_keys=True))
print("[live-smoke] OK")
PY
