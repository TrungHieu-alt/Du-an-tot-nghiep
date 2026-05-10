"""Validate the Matching V2 Slice 6B scenario dataset.

This script is intentionally fail-fast. It validates the compact 6 JD / 36 CV
dataset before seed and can also validate a live PostgreSQL state after seed.

Usage:
    python backend/db_v2/validate_scenario_dataset.py
    python backend/db_v2/validate_scenario_dataset.py --db
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any


DB_V2_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DB_V2_DIR.parent
DEFAULT_DATASET = DB_V2_DIR / "scenarios" / "matching_v2_slice_6b.json"
DEFAULT_SCHEMA = DB_V2_DIR / "scenarios" / "matching_v2_slice_6b.schema.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db_v2.scenario_embeddings import (  # noqa: E402
    EMBEDDING_DIM,
    build_embedding_payload,
    normalize_dataset,
    normalize_terms,
    stable_embedding_hash,
)


EDUCATION_RANK = {
    "lop_9": 0,
    "lop_12": 1,
    "dai_hoc": 2,
    "thac_si": 3,
    "tien_si": 4,
}


EXPECTED_JOB_COUNT = 6
EXPECTED_CV_COUNT = 36
EXPECTED_JOB_EMBEDDING_ROWS = 6
EXPECTED_CV_EMBEDDING_ROWS = 35

REQUIRED_COVERAGE = {
    "remote_ignores_location",
    "non_remote_location_strict_fail_isolated",
    "job_type_strict_fail_isolated",
    "seniority_exact_fail_isolated",
    "education_higher_pass",
    "education_lower_fail_isolated",
    "required_certification_fail",
    "multi_cert_subset_fail",
    "low_skill_overlap_pass_ranks_low",
    "title_similar_wrong_domain",
    "skills_similar_fail_seniority_location_job_type",
    "strong_good_noisy_three_anchors",
    "jd_to_cv_tie_break_by_cv_id",
    "top_k_truncation",
    "total_after_filter_zero",
    "min_score_zero_hard_filter_verification",
    "partial_missing_embedding_no_crash",
    "deterministic_scores_and_reasoning",
    "reverse_cv_to_jd_expected_ranking",
    "normalization",
}

OPTIONAL_COVERAGE = {
    "cv_to_jd_tie_break_by_job_id_if_feasible",
}


class ValidationFailure(AssertionError):
    """Raised when scenario validation fails."""


def validate_dataset(
    dataset_path: Path = DEFAULT_DATASET,
    schema_path: Path = DEFAULT_SCHEMA,
    *,
    check_db: bool = False,
) -> dict[str, Any]:
    raw = _load_json(dataset_path)
    schema = _load_json(schema_path)
    _validate_schema_contract(raw, schema)
    dataset = normalize_dataset(raw)

    _validate_counts(dataset)
    _validate_normalization(raw, dataset)
    _validate_groups(dataset)
    _validate_coverage(dataset)
    embeddings = _validate_embeddings(dataset)
    in_memory_results = _validate_expectations_in_memory(dataset, embeddings)

    summary: dict[str, Any] = {
        "dataset": str(dataset_path),
        "schema": str(schema_path),
        "jobs": len(dataset["jobs"]),
        "candidates": len(dataset["candidates"]),
        "job_embeddings": len(embeddings["jobs"]),
        "candidate_embeddings": len(embeddings["candidates"]),
        "embedding_hash": stable_embedding_hash(embeddings),
        "expectations": len(dataset["expectations"]),
        "in_memory_expectations": in_memory_results,
    }

    if check_db:
        summary["db"] = _validate_db_state(dataset)

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--db", action="store_true", help="Validate live DB state too")
    args = parser.parse_args()

    summary = validate_dataset(args.dataset, args.schema, check_db=args.db)
    print("[scenario-validate] json_schema_validation=pass")
    print(
        "[scenario-validate] counts "
        f"jobs={summary['jobs']} candidates={summary['candidates']} "
        f"job_embeddings={summary['job_embeddings']} "
        f"candidate_embeddings={summary['candidate_embeddings']}"
    )
    print(f"[scenario-validate] embedding_hash={summary['embedding_hash']}")
    print(
        "[scenario-validate] expectations="
        f"{summary['in_memory_expectations']['passed']}/"
        f"{summary['in_memory_expectations']['total']} in_memory"
    )
    if "db" in summary:
        db = summary["db"]
        print(
            "[scenario-validate] db_counts "
            f"jobs={db['job_posts_v2']} candidates={db['candidate_profiles_v2']} "
            f"job_embeddings={db['job_embeddings_v2']} "
            f"candidate_embeddings={db['candidate_embeddings_v2']}"
        )
        print(
            "[scenario-validate] db_expectations="
            f"{db['expectations']['passed']}/{db['expectations']['total']}"
        )
    print("[scenario-validate] OK")
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationFailure(f"invalid JSON in {path}: {exc}") from exc


def _validate_schema_contract(dataset: dict[str, Any], schema: dict[str, Any]) -> None:
    required_top = set(schema.get("required", []))
    _assert(required_top.issubset(dataset), f"missing top-level keys: {required_top - set(dataset)}")
    _assert(
        dataset.get("schema_version") == schema["properties"]["schema_version"]["const"],
        "schema_version does not match schema const",
    )
    _assert(dataset.get("broad_dataset_deferred") is True, "broad dataset must be deferred")

    defs = schema["$defs"]
    locations = set(defs["location"]["enum"])
    job_types = set(defs["job_type"]["enum"])
    seniorities = set(defs["seniority"]["enum"])
    educations = set(defs["education"]["enum"])

    _assert(len(dataset.get("jobs", [])) == EXPECTED_JOB_COUNT, "schema job count must be 6")
    _assert(len(dataset.get("candidates", [])) == EXPECTED_CV_COUNT, "schema CV count must be 36")
    _assert(len(dataset.get("scenario_groups", [])) == EXPECTED_JOB_COUNT, "schema group count must be 6")

    required_job = set(defs["job"]["required"])
    required_cv = set(defs["candidate"]["required"])
    for job in dataset["jobs"]:
        _assert(required_job.issubset(job), f"job {job.get('job_id')} missing required fields")
        _assert(job["location"] in locations, f"job {job['job_id']} invalid location")
        _assert(job["job_type"] in job_types, f"job {job['job_id']} invalid job_type")
        _assert(job["seniority"] in seniorities, f"job {job['job_id']} invalid seniority")
        _assert(job["education"] in educations, f"job {job['job_id']} invalid education")
    for cv in dataset["candidates"]:
        _assert(required_cv.issubset(cv), f"cv {cv.get('cv_id')} missing required fields")
        _assert(cv["location"] in locations, f"cv {cv['cv_id']} invalid location")
        _assert(cv["job_type"] in job_types, f"cv {cv['cv_id']} invalid job_type")
        _assert(cv["seniority"] in seniorities, f"cv {cv['cv_id']} invalid seniority")
        _assert(cv["education"] in educations, f"cv {cv['cv_id']} invalid education")

    partial = dataset["partial_embedding_case"]
    partial_schema = schema["properties"]["partial_embedding_case"]["properties"]
    _assert(partial["field"] in partial_schema["field"]["enum"], "invalid partial embedding field")
    _assert(partial["mode"] in partial_schema["mode"]["enum"], "invalid partial embedding mode")


def _validate_counts(dataset: dict[str, Any]) -> None:
    jobs = dataset["jobs"]
    cvs = dataset["candidates"]
    job_ids = [job["job_id"] for job in jobs]
    cv_ids = [cv["cv_id"] for cv in cvs]
    _assert(len(jobs) == EXPECTED_JOB_COUNT, f"expected 6 jobs, got {len(jobs)}")
    _assert(len(cvs) == EXPECTED_CV_COUNT, f"expected 36 CVs, got {len(cvs)}")
    _assert(len(set(job_ids)) == EXPECTED_JOB_COUNT, "job IDs must be unique")
    _assert(len(set(cv_ids)) == EXPECTED_CV_COUNT, "CV IDs must be unique")
    _assert(job_ids == [4001, 4002, 4003, 4004, 4005, 4006], "job IDs must be 4001..4006")
    _assert(cv_ids == list(range(3001, 3037)), "CV IDs must be 3001..3036")


def _validate_normalization(raw: dict[str, Any], normalized: dict[str, Any]) -> None:
    raw_jobs = {job["job_id"]: job for job in raw["jobs"]}
    raw_cvs = {cv["cv_id"]: cv for cv in raw["candidates"]}

    for job in normalized["jobs"]:
        _assert(job["skills"] == normalize_terms(job["skills"]), f"job {job['job_id']} skills not normalized")
        _assert(
            job["required_certifications"] == normalize_terms(job["required_certifications"]),
            f"job {job['job_id']} certs not normalized",
        )
        _assert(
            raw_jobs[job["job_id"]]["skills"] == job["skills"],
            f"job {job['job_id']} source skills should already be normalized",
        )
        _assert(
            raw_jobs[job["job_id"]]["required_certifications"] == job["required_certifications"],
            f"job {job['job_id']} source certs should already be normalized",
        )

    normalization_cases = 0
    for cv in normalized["candidates"]:
        raw_cv = raw_cvs[cv["cv_id"]]
        _assert(cv["skills"] == normalize_terms(cv["skills"]), f"cv {cv['cv_id']} skills not normalized")
        _assert(cv["certifications"] == normalize_terms(cv["certifications"]), f"cv {cv['cv_id']} certs not normalized")
        source_changed = (
            raw_cv["skills"] != cv["skills"]
            or raw_cv["certifications"] != cv["certifications"]
        )
        if cv.get("normalization_case"):
            normalization_cases += 1
            _assert(source_changed, f"cv {cv['cv_id']} normalization case did not change")
        else:
            _assert(not source_changed, f"cv {cv['cv_id']} source arrays are not normalized")

    _assert(normalization_cases == 1, f"expected exactly one normalization case, got {normalization_cases}")


def _validate_groups(dataset: dict[str, Any]) -> None:
    jobs_by_id = {job["job_id"]: job for job in dataset["jobs"]}
    cvs_by_id = {cv["cv_id"]: cv for cv in dataset["candidates"]}
    grouped: dict[int, list[int]] = {}
    for cv in dataset["candidates"]:
        grouped.setdefault(cv["designed_for_job_id"], []).append(cv["cv_id"])

    for group in dataset["scenario_groups"]:
        job_id = group["job_id"]
        designed = group["designed_cv_ids"]
        _assert(job_id in jobs_by_id, f"group references missing job {job_id}")
        _assert(len(designed) == 6, f"job {job_id} must have exactly 6 designed CVs")
        _assert(grouped.get(job_id) == designed, f"job {job_id} designed CV mapping mismatch")
        _assert(len(set(designed)) == 6, f"job {job_id} designed CV IDs must be unique")

        job = jobs_by_id[job_id]
        expected_pass = set(group["expected_hard_filter_pass"])
        expected_fail = {int(k): v for k, v in group["expected_hard_filter_fail"].items()}
        actual_pass = {
            cv_id
            for cv_id in designed
            if _passes_hard_filter(job, cvs_by_id[cv_id])
        }
        _assert(actual_pass == expected_pass, f"job {job_id} hard-filter pass mismatch: {actual_pass} != {expected_pass}")
        _assert(set(expected_fail) == set(designed) - expected_pass, f"job {job_id} hard-filter fail mismatch")
        _validate_sibling_diversity(job_id, [cvs_by_id[cv_id] for cv_id in designed])

        roles = {cvs_by_id[cv_id]["scenario_role"] for cv_id in designed}
        _assert("strong_pass" in roles, f"job {job_id} missing strong_pass")
        _assert("noisy_pass" in roles, f"job {job_id} missing noisy_pass")
        _assert(
            "good_pass" in roles or {"good_pass_a", "good_pass_b"}.issubset(roles),
            f"job {job_id} missing good pass",
        )


def _validate_sibling_diversity(job_id: int, cvs: list[dict[str, Any]]) -> None:
    for idx, left in enumerate(cvs):
        for right in cvs[idx + 1:]:
            diff = 0
            diff += left["title"] != right["title"]
            diff += set(left["skills"]) != set(right["skills"])
            diff += left["summary"] != right["summary"]
            diff += left["experience"] != right["experience"]
            diff += left["seniority"] != right["seniority"]
            diff += left["education"] != right["education"]
            diff += (left["location"], left["job_type"]) != (right["location"], right["job_type"])
            diff += set(left["certifications"]) != set(right["certifications"])
            _assert(
                diff >= 3,
                f"job {job_id} CV diversity failed for {left['cv_id']} and {right['cv_id']}: {diff} groups differ",
            )


def _validate_coverage(dataset: dict[str, Any]) -> None:
    coverage = dataset["coverage"]
    missing = REQUIRED_COVERAGE - set(coverage)
    _assert(not missing, f"missing coverage keys: {sorted(missing)}")
    empty = [key for key in REQUIRED_COVERAGE if not coverage.get(key)]
    _assert(not empty, f"coverage keys must not be empty: {empty}")
    for key in OPTIONAL_COVERAGE:
        _assert(key in coverage, f"missing optional coverage note: {key}")


def _validate_embeddings(dataset: dict[str, Any]) -> dict[str, dict[int, dict[str, list[float] | None]]]:
    first = build_embedding_payload(dataset)
    second = build_embedding_payload(dataset)
    _assert(stable_embedding_hash(first) == stable_embedding_hash(second), "embeddings are not deterministic")
    _assert(len(first["jobs"]) == EXPECTED_JOB_EMBEDDING_ROWS, "expected 6 job embedding rows")
    _assert(len(first["candidates"]) == EXPECTED_CV_EMBEDDING_ROWS, "expected 35 candidate embedding rows")

    partial = dataset["partial_embedding_case"]
    partial_cv_id = int(partial["cv_id"])
    if partial["mode"] == "missing_row":
        _assert(partial_cv_id not in first["candidates"], f"cv {partial_cv_id} embedding row should be missing")
    else:
        _assert(partial_cv_id in first["candidates"], f"cv {partial_cv_id} embedding row should exist")

    null_fields: list[tuple[int, str]] = []
    vectors_seen: set[tuple[float, ...]] = set()
    for section in ("jobs", "candidates"):
        for entity_id, fields in first[section].items():
            for field_name, vector in fields.items():
                if vector is None:
                    if section == "candidates":
                        null_fields.append((entity_id, field_name))
                    continue
                _assert(len(vector) == EMBEDDING_DIM, f"{section} {entity_id} {field_name} wrong dim")
                norm = math.sqrt(sum(value * value for value in vector))
                _assert(abs(norm - 1.0) <= 1e-6, f"{section} {entity_id} {field_name} norm {norm}")
                rounded = tuple(round(value, 8) for value in vector)
                _assert(len(set(rounded)) > 2, f"{section} {entity_id} {field_name} appears constant")
                vectors_seen.add(rounded)

    expected_null = [] if partial["mode"] == "missing_row" else [(partial_cv_id, partial["field"])]
    _assert(null_fields == expected_null, f"unexpected null embedding fields: {null_fields}")
    _assert(len(vectors_seen) > 20, "embeddings are not diverse enough")
    return first


def _validate_expectations_in_memory(
    dataset: dict[str, Any],
    embeddings: dict[str, dict[int, dict[str, list[float] | None]]],
) -> dict[str, int]:
    job_map = {job["job_id"]: job for job in dataset["jobs"]}
    cv_map = {cv["cv_id"]: cv for cv in dataset["candidates"]}
    job_emb_map = embeddings["jobs"]
    cv_emb_map = embeddings["candidates"]

    passed = 0
    for expectation in dataset["expectations"]:
        if expectation["anchor_type"] == "job":
            result = _run_job_memory(
                expectation["anchor_id"],
                expectation["top_k"],
                expectation["min_score"],
                job_map,
                cv_map,
                job_emb_map,
                cv_emb_map,
            )
        else:
            result = _run_cv_memory(
                expectation["anchor_id"],
                expectation["top_k"],
                expectation["min_score"],
                job_map,
                cv_map,
                job_emb_map,
                cv_emb_map,
            )
        _assert_expectation(expectation, result)
        passed += 1
    return {"passed": passed, "total": len(dataset["expectations"])}


def _validate_db_state(dataset: dict[str, Any]) -> dict[str, Any]:
    import psycopg

    conninfo = (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5433')} "
        f"user={os.getenv('POSTGRES_USER', 'jobmatcher')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'jobmatcher')} "
        f"dbname={os.getenv('POSTGRES_DB', 'jobmatcher_v2')}"
    )
    with psycopg.connect(conninfo) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            tables = {row[0] for row in cur.fetchall()}
            expected_tables = {
                "candidate_profiles_v2",
                "job_posts_v2",
                "candidate_embeddings_v2",
                "job_embeddings_v2",
            }
            _assert(tables == expected_tables, f"unexpected DB tables: {tables}")

            counts: dict[str, int] = {}
            for table in sorted(expected_tables):
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = int(cur.fetchone()[0])

            _assert(counts["job_posts_v2"] == EXPECTED_JOB_COUNT, "DB job count mismatch")
            _assert(counts["candidate_profiles_v2"] == EXPECTED_CV_COUNT, "DB CV count mismatch")
            _assert(counts["job_embeddings_v2"] == EXPECTED_JOB_EMBEDDING_ROWS, "DB job embedding count mismatch")
            _assert(counts["candidate_embeddings_v2"] == EXPECTED_CV_EMBEDDING_ROWS, "DB CV embedding count mismatch")

            cur.execute(
                "SELECT cv_id, skills, certifications FROM candidate_profiles_v2 ORDER BY cv_id"
            )
            for cv_id, skills, certs in cur.fetchall():
                _assert(list(skills) == normalize_terms(skills), f"DB cv {cv_id} skills not normalized")
                _assert(list(certs) == normalize_terms(certs), f"DB cv {cv_id} certs not normalized")

            _validate_db_vectors(cur, dataset)

        expectation_summary = _validate_expectations_db(conn, dataset)
        counts["expectations"] = expectation_summary
    return counts


def _validate_db_vectors(cur: Any, dataset: dict[str, Any]) -> None:
    partial = dataset["partial_embedding_case"]
    partial_cv_id = int(partial["cv_id"])
    null_fields: list[tuple[int, str]] = []
    cur.execute(
        """
        SELECT cv_id,
               emb_title::text,
               emb_skills::text,
               emb_summary::text,
               emb_experience::text
        FROM candidate_embeddings_v2
        ORDER BY cv_id
        """
    )
    for cv_id, title, skills, summary, experience in cur.fetchall():
        for field, raw in {
            "emb_title": title,
            "emb_skills": skills,
            "emb_summary": summary,
            "emb_experience": experience,
        }.items():
            vector = _parse_pgvector(raw)
            if vector is None:
                null_fields.append((cv_id, field))
            else:
                _assert(len(vector) == EMBEDDING_DIM, f"DB cv {cv_id} {field} wrong dim")
                norm = math.sqrt(sum(value * value for value in vector))
                _assert(abs(norm - 1.0) <= 1e-4, f"DB cv {cv_id} {field} norm {norm}")

    cur.execute(
        """
        SELECT job_id,
               emb_title::text,
               emb_skills::text,
               emb_requirement::text
        FROM job_embeddings_v2
        ORDER BY job_id
        """
    )
    for job_id, title, skills, requirement in cur.fetchall():
        for field, raw in {
            "emb_title": title,
            "emb_skills": skills,
            "emb_requirement": requirement,
        }.items():
            vector = _parse_pgvector(raw)
            _assert(vector is not None, f"DB job {job_id} {field} must not be null")
            _assert(len(vector) == EMBEDDING_DIM, f"DB job {job_id} {field} wrong dim")
            norm = math.sqrt(sum(value * value for value in vector))
            _assert(abs(norm - 1.0) <= 1e-4, f"DB job {job_id} {field} norm {norm}")

    cur.execute(
        "SELECT EXISTS (SELECT 1 FROM candidate_embeddings_v2 WHERE cv_id = %s)",
        (partial_cv_id,),
    )
    partial_row_exists = bool(cur.fetchone()[0])
    if partial["mode"] == "missing_row":
        _assert(not partial_row_exists, f"cv {partial_cv_id} embedding row should be missing")
        expected_null: list[tuple[int, str]] = []
    else:
        _assert(partial_row_exists, f"cv {partial_cv_id} embedding row should exist")
        expected_null = [(partial_cv_id, partial["field"])]
    _assert(null_fields == expected_null, f"DB null fields mismatch: {null_fields}")


def _validate_expectations_db(conn: Any, dataset: dict[str, Any]) -> dict[str, int]:
    from matching_v2.runner import run_for_cv, run_for_job

    passed = 0
    for expectation in dataset["expectations"]:
        if expectation["anchor_type"] == "job":
            response = run_for_job(
                conn,
                expectation["anchor_id"],
                top_k=expectation["top_k"],
                min_score=expectation["min_score"],
            )
            result = _response_to_result(response, id_field="cv_id")
        else:
            response = run_for_cv(
                conn,
                expectation["anchor_id"],
                top_k=expectation["top_k"],
                min_score=expectation["min_score"],
            )
            result = _response_to_result(response, id_field="job_id")
        _assert_expectation(expectation, result)
        passed += 1
    return {"passed": passed, "total": len(dataset["expectations"])}


def _passes_hard_filter(job: dict[str, Any], cv: dict[str, Any]) -> bool:
    if job["job_type"] != cv["job_type"]:
        return False
    if job["job_type"] != "remote" and job["location"] != cv["location"]:
        return False
    if job["seniority"] != cv["seniority"]:
        return False
    if EDUCATION_RANK.get(cv["education"], -1) < EDUCATION_RANK.get(job["education"], 99):
        return False
    required = set(job["required_certifications"])
    return required.issubset(set(cv["certifications"]))


def _score_pair_local(
    job: dict[str, Any],
    job_emb: dict[str, list[float] | None] | None,
    cv: dict[str, Any],
    cv_emb: dict[str, list[float] | None] | None,
) -> tuple[dict[str, float], list[str]]:
    missing: list[str] = []
    j_title = job_emb.get("emb_title") if job_emb else None
    c_title = cv_emb.get("emb_title") if cv_emb else None
    if j_title is None:
        missing.append("jd.emb_title")
    if c_title is None:
        missing.append("cv.emb_title")
    title_score = _cosine_similarity(j_title, c_title)

    j_skills = job_emb.get("emb_skills") if job_emb else None
    c_skills = cv_emb.get("emb_skills") if cv_emb else None
    if j_skills is None:
        missing.append("jd.emb_skills")
    if c_skills is None:
        missing.append("cv.emb_skills")
    semantic_skills = _cosine_similarity(j_skills, c_skills)
    exact = _exact_overlap_ratio(job["skills"], cv["skills"])
    skills_score = (0.6 * semantic_skills) + (0.4 * exact)

    j_req = job_emb.get("emb_requirement") if job_emb else None
    c_exp = cv_emb.get("emb_experience") if cv_emb else None
    if j_req is None:
        missing.append("jd.emb_requirement")
    if c_exp is None:
        missing.append("cv.emb_experience")
    req_exp_score = _cosine_similarity(j_req, c_exp)

    c_summary = cv_emb.get("emb_summary") if cv_emb else None
    if c_summary is None:
        missing.append("cv.emb_summary")
    req_summary_score = _cosine_similarity(j_req, c_summary)

    missing = list(dict.fromkeys(missing))
    final_score = (
        0.35 * title_score
        + 0.35 * skills_score
        + 0.20 * req_exp_score
        + 0.10 * req_summary_score
    )
    return (
        {
            "title_score": title_score,
            "skills_score": skills_score,
            "req_exp_score": req_exp_score,
            "req_summary_score": req_summary_score,
            "final_score": final_score,
        },
        missing,
    )


def _cosine_similarity(a: list[float] | None, b: list[float] | None) -> float:
    if a is None or b is None:
        return 0.0
    dot = sum(left * right for left, right in zip(a, b))
    norm_a = math.sqrt(sum(value * value for value in a))
    norm_b = math.sqrt(sum(value * value for value in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm_a * norm_b)))


def _exact_overlap_ratio(skills_a: list[str], skills_b: list[str]) -> float:
    set_a = {skill.strip().lower() for skill in skills_a if skill.strip()}
    set_b = {skill.strip().lower() for skill in skills_b if skill.strip()}
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / max(len(set_a), len(set_b))


def _matched_skills(skills_a: list[str], skills_b: list[str]) -> list[str]:
    set_a = {skill.strip().lower() for skill in skills_a if skill.strip()}
    set_b = {skill.strip().lower() for skill in skills_b if skill.strip()}
    return sorted(set_a & set_b)


def _build_reasoning(
    *,
    title_score: float,
    skills_score: float,
    req_exp_score: float,
    req_summary_score: float,
    matched_skills: list[str],
    missing_emb_fields: list[str],
) -> str:
    components = [
        ("title", title_score),
        ("skills", skills_score),
        ("requirement<->experience", req_exp_score),
        ("requirement<->summary", req_summary_score),
    ]
    best_name, best_value = max(components, key=lambda item: item[1])
    parts = [f"Strongest signal: '{best_name}' (score {best_value:.3f})."]
    if matched_skills:
        parts.append(
            f"Exact skill matches ({len(matched_skills)}): {', '.join(matched_skills)}."
        )
    else:
        parts.append("No exact skill overlap between JD and CV.")
    if missing_emb_fields:
        parts.append(
            f"Missing embeddings for: {', '.join(missing_emb_fields)} - those components defaulted to 0."
        )
    return " ".join(parts)


def _run_job_memory(
    job_id: int,
    top_k: int,
    min_score: float,
    job_map: dict[int, dict[str, Any]],
    cv_map: dict[int, dict[str, Any]],
    job_emb_map: dict[int, dict[str, list[float] | None]],
    cv_emb_map: dict[int, dict[str, list[float] | None]],
) -> dict[str, Any]:
    job = job_map[job_id]
    filtered = [cv for cv in cv_map.values() if _passes_hard_filter(job, cv)]
    scored = []
    for cv in filtered:
        scores, missing = _score_pair_local(job, job_emb_map.get(job_id), cv, cv_emb_map.get(cv["cv_id"]))
        scored.append((cv["cv_id"], scores, missing, _matched_skills(job["skills"], cv["skills"])))
    scored.sort(key=lambda item: (-item[1]["final_score"], item[0]))
    returned = [item for item in scored if item[1]["final_score"] >= min_score][:top_k]
    return _memory_result(filtered, returned)


def _run_cv_memory(
    cv_id: int,
    top_k: int,
    min_score: float,
    job_map: dict[int, dict[str, Any]],
    cv_map: dict[int, dict[str, Any]],
    job_emb_map: dict[int, dict[str, list[float] | None]],
    cv_emb_map: dict[int, dict[str, list[float] | None]],
) -> dict[str, Any]:
    cv = cv_map[cv_id]
    filtered = [job for job in job_map.values() if _passes_hard_filter(job, cv)]
    scored = []
    for job in filtered:
        scores, missing = _score_pair_local(job, job_emb_map.get(job["job_id"]), cv, cv_emb_map.get(cv_id))
        scored.append((job["job_id"], scores, missing, _matched_skills(job["skills"], cv["skills"])))
    scored.sort(key=lambda item: (-item[1]["final_score"], item[0]))
    returned = [item for item in scored if item[1]["final_score"] >= min_score][:top_k]
    return _memory_result(filtered, returned)


def _memory_result(filtered: list[Any], returned: list[tuple[int, dict[str, float], list[str], list[str]]]) -> dict[str, Any]:
    matches = []
    for entity_id, scores, missing, skills in returned:
        matches.append(
            {
                "id": entity_id,
                "scores": scores,
                "missing": missing,
                "reasoning": _build_reasoning(
                    title_score=scores["title_score"],
                    skills_score=scores["skills_score"],
                    req_exp_score=scores["req_exp_score"],
                    req_summary_score=scores["req_summary_score"],
                    matched_skills=skills,
                    missing_emb_fields=missing,
                ),
            }
        )
    return {
        "total_after_filter": len(filtered),
        "total_returned": len(matches),
        "matches": matches,
    }


def _response_to_result(response: Any, *, id_field: str) -> dict[str, Any]:
    matches = []
    for match in response.matches:
        entity_id = getattr(match, id_field)
        missing: list[str] = []
        if "Missing embeddings for:" in match.reasoning:
            suffix = match.reasoning.split("Missing embeddings for:", 1)[1]
            suffix = suffix.replace("\u2014", "-")
            suffix = suffix.split(" -", 1)[0]
            suffix = suffix.split(" --", 1)[0]
            missing = [item.strip() for item in suffix.split(",") if item.strip()]
        matches.append(
            {
                "id": entity_id,
                "scores": {
                    "final_score": match.final_score,
                    "title_score": match.title_score,
                    "skills_score": match.skills_score,
                    "req_exp_score": match.req_exp_score,
                    "req_summary_score": match.req_summary_score,
                },
                "missing": missing,
                "reasoning": match.reasoning,
            }
        )
    return {
        "total_after_filter": response.total_after_filter,
        "total_returned": response.total_returned,
        "matches": matches,
    }


def _assert_expectation(expectation: dict[str, Any], result: dict[str, Any]) -> None:
    match_ids = [match["id"] for match in result["matches"]]
    index = {entity_id: idx for idx, entity_id in enumerate(match_ids)}

    if "total_after_filter" in expectation:
        _assert(
            result["total_after_filter"] == expectation["total_after_filter"],
            f"{expectation['id']} total_after_filter mismatch: {result['total_after_filter']}",
        )
    if "total_after_filter_min" in expectation:
        _assert(
            result["total_after_filter"] >= expectation["total_after_filter_min"],
            f"{expectation['id']} total_after_filter below minimum: {result['total_after_filter']}",
        )
    if "total_returned" in expectation:
        _assert(
            result["total_returned"] == expectation["total_returned"],
            f"{expectation['id']} total_returned mismatch: {result['total_returned']}",
        )
    if "expected_top_id" in expectation:
        _assert(match_ids, f"{expectation['id']} expected a top match")
        _assert(
            match_ids[0] == expectation["expected_top_id"],
            f"{expectation['id']} top mismatch: {match_ids[:5]}",
        )
    for entity_id in expectation.get("must_include", []):
        _assert(entity_id in index, f"{expectation['id']} missing expected id {entity_id}; got {match_ids}")
    for entity_id in expectation.get("must_exclude", []):
        _assert(entity_id not in index, f"{expectation['id']} unexpectedly returned id {entity_id}")
    for higher, lower in expectation.get("must_rank_above", []):
        _assert(higher in index and lower in index, f"{expectation['id']} rank pair missing {higher}>{lower}")
        _assert(index[higher] < index[lower], f"{expectation['id']} rank order failed {higher}>{lower}: {match_ids}")
    for raw_id, fields in expectation.get("must_have_missing_embedding", {}).items():
        entity_id = int(raw_id)
        _assert(entity_id in index, f"{expectation['id']} missing embedding check id {entity_id} not returned")
        match = result["matches"][index[entity_id]]
        for field in fields:
            _assert(field in match["missing"], f"{expectation['id']} missing field {field} not reported: {match}")
        if "cv.emb_summary" in fields:
            _assert(
                match["scores"]["req_summary_score"] == 0.0,
                f"{expectation['id']} req_summary_score should be 0 for missing cv.emb_summary",
            )
        if "cv.emb_title" in fields:
            _assert(
                match["scores"]["title_score"] == 0.0,
                f"{expectation['id']} title_score should be 0 for missing cv.emb_title",
            )
        if "cv.emb_experience" in fields:
            _assert(
                match["scores"]["req_exp_score"] == 0.0,
                f"{expectation['id']} req_exp_score should be 0 for missing cv.emb_experience",
            )


def _parse_pgvector(raw: str | None) -> list[float] | None:
    if raw is None:
        return None
    stripped = raw.strip().strip("[]")
    if not stripped:
        return None
    return [float(value) for value in stripped.split(",")]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationFailure(message)


if __name__ == "__main__":
    sys.exit(main())
