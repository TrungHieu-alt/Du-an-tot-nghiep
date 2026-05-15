"""15-check post-generation validation gate for Slice 6B scenario dataset.

Run after reset_scenario.py to confirm all invariants hold against the
live database. Exits non-zero on any failure.

Usage:
    python -m db_v2.scenario.validate
"""

from __future__ import annotations

import sys
from typing import Any

import psycopg

from db_v2.scenario.embedder import embed_text


# ---------------------------------------------------------------------------
# DB connection (same env-var convention as matching_v2.db)
# ---------------------------------------------------------------------------

import os

def _conn() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        user=os.getenv("POSTGRES_USER", "jobmatcher"),
        password=os.getenv("POSTGRES_PASSWORD", "jobmatcher"),
        dbname=os.getenv("POSTGRES_DB", "jobmatcher_v2"),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"

_results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = PASS if condition else FAIL
    msg = f"[{status}] {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    _results.append((name, condition, detail))


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def run_all() -> int:
    with _conn() as conn:
        with conn.cursor() as cur:

            # ----------------------------------------------------------------
            # Check 1: Exactly 6 jobs in job_posts_v2
            # ----------------------------------------------------------------
            cur.execute("SELECT COUNT(*) FROM job_posts_v2 WHERE job_id BETWEEN 4001 AND 4006")
            n = cur.fetchone()[0]
            check("C01 job_posts_v2 has exactly 6 scenario jobs", n == 6, f"found {n}")

            # ----------------------------------------------------------------
            # Check 2: Exactly 36 candidates in candidate_profiles_v2
            # ----------------------------------------------------------------
            cur.execute("SELECT COUNT(*) FROM candidate_profiles_v2 WHERE cv_id BETWEEN 3001 AND 3036")
            n = cur.fetchone()[0]
            check("C02 candidate_profiles_v2 has exactly 36 scenario candidates", n == 36, f"found {n}")

            # ----------------------------------------------------------------
            # Check 3: Exactly 6 job embeddings
            # ----------------------------------------------------------------
            cur.execute("SELECT COUNT(*) FROM job_embeddings_v2 WHERE job_id BETWEEN 4001 AND 4006")
            n = cur.fetchone()[0]
            check("C03 job_embeddings_v2 has exactly 6 rows", n == 6, f"found {n}")

            # ----------------------------------------------------------------
            # Check 4: Exactly 35 candidate embeddings (CV 3018 is missing)
            # ----------------------------------------------------------------
            cur.execute("SELECT COUNT(*) FROM candidate_embeddings_v2 WHERE cv_id BETWEEN 3001 AND 3036")
            n = cur.fetchone()[0]
            check("C04 candidate_embeddings_v2 has exactly 35 rows (3018 excluded)", n == 35, f"found {n}")

            # ----------------------------------------------------------------
            # Check 5: CV 3018 has no embedding row
            # ----------------------------------------------------------------
            cur.execute("SELECT COUNT(*) FROM candidate_embeddings_v2 WHERE cv_id = 3018")
            n = cur.fetchone()[0]
            check("C05 CV 3018 has no embedding row", n == 0, f"found {n}")

            # ----------------------------------------------------------------
            # Check 6: Skills are normalized (lowercase, no leading/trailing spaces)
            # ----------------------------------------------------------------
            cur.execute("""
                SELECT cv_id, unnest(skills) AS skill
                FROM candidate_profiles_v2
                WHERE cv_id BETWEEN 3001 AND 3036
            """)
            bad_skills: list[str] = []
            for row in cur.fetchall():
                cv_id, skill = row
                if skill != skill.strip().lower():
                    bad_skills.append(f"cv_id={cv_id}: '{skill}'")
            check("C06 all candidate skills are normalized (lowercase, trimmed)", len(bad_skills) == 0, "; ".join(bad_skills[:5]))

            # ----------------------------------------------------------------
            # Check 7: Job skills are normalized
            # ----------------------------------------------------------------
            cur.execute("""
                SELECT job_id, unnest(skills) AS skill
                FROM job_posts_v2
                WHERE job_id BETWEEN 4001 AND 4006
            """)
            bad_jskills: list[str] = []
            for row in cur.fetchall():
                job_id, skill = row
                if skill != skill.strip().lower():
                    bad_jskills.append(f"job_id={job_id}: '{skill}'")
            check("C07 all job skills are normalized (lowercase, trimmed)", len(bad_jskills) == 0, "; ".join(bad_jskills[:5]))

            # ----------------------------------------------------------------
            # Check 8: No duplicate skills within any candidate
            # ----------------------------------------------------------------
            cur.execute("""
                SELECT cv_id, skill, COUNT(*) as cnt
                FROM (
                    SELECT cv_id, unnest(skills) AS skill
                    FROM candidate_profiles_v2
                    WHERE cv_id BETWEEN 3001 AND 3036
                ) t
                GROUP BY cv_id, skill
                HAVING COUNT(*) > 1
            """)
            dups = cur.fetchall()
            check("C08 no duplicate skills within any candidate", len(dups) == 0, str(dups[:3]))

            # ----------------------------------------------------------------
            # Check 9: Enum constraint — no invalid location/job_type/seniority/education
            # ----------------------------------------------------------------
            valid_locations = {"Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng"}
            valid_job_types = {"remote", "fulltime", "parttime"}
            valid_seniorities = {"intern", "fresher", "junior", "mid", "senior", "lead"}
            valid_educations = {"high_school", "bachelor", "master", "phd"}

            cur.execute("""
                SELECT cv_id, location, job_type, seniority, education
                FROM candidate_profiles_v2
                WHERE cv_id BETWEEN 3001 AND 3036
            """)
            invalid_enums: list[str] = []
            for cv_id, loc, jt, sen, edu in cur.fetchall():
                if loc not in valid_locations:
                    invalid_enums.append(f"cv_id={cv_id} invalid location={loc}")
                if jt not in valid_job_types:
                    invalid_enums.append(f"cv_id={cv_id} invalid job_type={jt}")
                if sen not in valid_seniorities:
                    invalid_enums.append(f"cv_id={cv_id} invalid seniority={sen}")
                if edu not in valid_educations:
                    invalid_enums.append(f"cv_id={cv_id} invalid education={edu}")
            check("C09 all candidate enum fields are valid", len(invalid_enums) == 0, "; ".join(invalid_enums[:5]))

            # ----------------------------------------------------------------
            # Check 10: JD-1 (4001) — remote job: location filter bypassed
            #           CV 3006 (TP. Hồ Chí Minh, fulltime) must NOT pass filter
            #           CV 3005 (Hà Nội, fulltime) must NOT pass filter (wrong job_type)
            #           CV 3001 (Hà Nội, remote) MUST pass filter
            # ----------------------------------------------------------------
            # Simulate hard filter for JD-1
            cur.execute("""
                SELECT cv_id FROM candidate_profiles_v2
                WHERE job_type = 'remote'
                  AND seniority = 'senior'
                  AND education IN ('bachelor', 'master', 'phd')
                  AND cv_id BETWEEN 3001 AND 3036
                ORDER BY cv_id
            """)
            passing_jd1 = {r[0] for r in cur.fetchall()}
            # Also check certification subset for those passing
            cur.execute("""
                SELECT cv_id, certifications FROM candidate_profiles_v2
                WHERE cv_id = ANY(%s)
            """, (list(passing_jd1),))
            cert_rows = {r[0]: set(r[1]) for r in cur.fetchall()}
            required_certs = {"cka", "aws_saa"}
            passing_jd1_with_certs = {cv_id for cv_id in passing_jd1
                                       if required_certs.issubset(cert_rows.get(cv_id, set()))}
            check(
                "C10 JD-1 filter: CV 3001 passes, CV 3005/3006 filtered",
                3001 in passing_jd1_with_certs and 3005 not in passing_jd1 and 3006 not in passing_jd1,
                f"passing_with_certs={sorted(passing_jd1_with_certs)}"
            )

            # ----------------------------------------------------------------
            # Check 11: JD-5 (4005) — parttime junior high_school+
            #           CV 3028 (high_school) must be filtered (below_education)
            #           CV 3029 (mid) must be filtered (wrong seniority)
            #           CV 3025, 3026, 3027, 3030 must pass
            # ----------------------------------------------------------------
            edu_rank = {"unknown": 0, "high_school": 1, "bachelor": 2, "master": 3, "phd": 4}
            cur.execute("""
                SELECT cv_id, education, seniority, job_type, location
                FROM candidate_profiles_v2
                WHERE cv_id BETWEEN 3001 AND 3036
            """)
            all_cvs = cur.fetchall()
            passing_jd5 = set()
            for cv_id, edu, sen, jt, loc in all_cvs:
                if (jt == "parttime" and
                        sen == "junior" and
                        edu_rank.get(edu, -1) >= edu_rank["high_school"] and
                        loc == "Hà Nội"):
                    passing_jd5.add(cv_id)
            check(
                "C11 JD-5 filter: CV 3025-3027,3030 pass; 3028(high_school) and 3029(mid) filtered",
                {3025, 3026, 3027, 3030}.issubset(passing_jd5)
                    and 3028 not in passing_jd5
                    and 3029 not in passing_jd5,
                f"passing={sorted(passing_jd5)}"
            )

            # ----------------------------------------------------------------
            # Check 12: CV 3036 passes 0 JDs (total_after_filter=0 anchor)
            # ----------------------------------------------------------------
            jd_filter_rules = [
                # (job_id, job_type, seniority, min_edu_rank, location, required_certs)
                (4001, "remote", "senior", 2, None, {"cka", "aws_saa"}),
                (4002, "fulltime", "lead", 2, "Hà Nội", set()),
                (4003, "fulltime", "mid", 2, "TP. Hồ Chí Minh", set()),
                (4004, "fulltime", "mid", 2, "Đà Nẵng", set()),
                (4005, "parttime", "junior", 1, "Hà Nội", set()),
                (4006, "fulltime", "mid", 2, "TP. Hồ Chí Minh", set()),
            ]
            cur.execute("""
                SELECT cv_id, education, seniority, job_type, location, certifications
                FROM candidate_profiles_v2
                WHERE cv_id = 3036
            """)
            row3036 = cur.fetchone()
            cv_edu, cv_sen, cv_jt, cv_loc, cv_certs = row3036[1], row3036[2], row3036[3], row3036[4], set(row3036[5])
            cv_edu_rank = edu_rank.get(cv_edu, -1)

            passes_any = False
            for jid, jt, sen, min_edu, loc, req_certs in jd_filter_rules:
                location_ok = (jt == "remote") or (cv_loc == loc)
                passes = (
                    cv_jt == jt and
                    cv_sen == sen and
                    cv_edu_rank >= min_edu and
                    location_ok and
                    req_certs.issubset(cv_certs)
                )
                if passes:
                    passes_any = True
                    break
            check("C12 CV 3036 passes 0 JDs (total_after_filter_zero anchor)", not passes_any,
                  f"cv_edu={cv_edu}, cv_sen={cv_sen}, cv_jt={cv_jt}, cv_loc={cv_loc}")

            # ----------------------------------------------------------------
            # Check 13: Tie-pair CVs 3032/3033 produce identical title embeddings
            # ----------------------------------------------------------------
            cur.execute("SELECT emb_title FROM candidate_embeddings_v2 WHERE cv_id = 3032")
            emb_3032 = cur.fetchone()[0]
            cur.execute("SELECT emb_title FROM candidate_embeddings_v2 WHERE cv_id = 3033")
            emb_3033 = cur.fetchone()[0]

            import numpy as np

            def _parse_vec(v) -> np.ndarray:
                if isinstance(v, str):
                    return np.array([float(x) for x in v.strip("[]").split(",")], dtype=np.float32)
                return np.array(v, dtype=np.float32)

            v3032 = _parse_vec(emb_3032)
            v3033 = _parse_vec(emb_3033)
            are_identical = np.allclose(v3032, v3033, atol=1e-6)
            check("C13 CV 3032 and 3033 have identical title embeddings (tie-pair)", are_identical,
                  f"max_diff={float(np.max(np.abs(v3032 - v3033))):.2e}")

            # ----------------------------------------------------------------
            # Check 14: All embedding vectors have dimension 384
            # ----------------------------------------------------------------
            cur.execute("""
                SELECT cv_id, emb_title, emb_skills, emb_summary, emb_experience
                FROM candidate_embeddings_v2
                WHERE cv_id BETWEEN 3001 AND 3036
            """)
            wrong_dims: list[str] = []
            for cv_id, d1, d2, d3, d4 in cur.fetchall():
                for raw, name in [(d1, "emb_title"), (d2, "emb_skills"), (d3, "emb_summary"), (d4, "emb_experience")]:
                    if raw is not None:
                        dim = len(_parse_vec(raw))
                        if dim != 384:
                            wrong_dims.append(f"cv_id={cv_id} {name}={dim}")
            cur.execute("""
                SELECT job_id, emb_title, emb_skills, emb_requirement
                FROM job_embeddings_v2
                WHERE job_id BETWEEN 4001 AND 4006
            """)
            for job_id, d1, d2, d3 in cur.fetchall():
                for raw, name in [(d1, "emb_title"), (d2, "emb_skills"), (d3, "emb_requirement")]:
                    if raw is not None:
                        dim = len(_parse_vec(raw))
                        if dim != 384:
                            wrong_dims.append(f"job_id={job_id} {name}={dim}")
            check("C14 all embeddings are 384-dimensional", len(wrong_dims) == 0, "; ".join(wrong_dims[:5]))

            # ----------------------------------------------------------------
            # Check 15: JD-2 (4002) — education filter: CV 3009 (high_school) filtered
            # ----------------------------------------------------------------
            cur.execute("""
                SELECT cv_id, education, seniority, job_type, location
                FROM candidate_profiles_v2
                WHERE cv_id BETWEEN 3001 AND 3036
            """)
            all_cvs_data = cur.fetchall()
            passing_jd2 = set()
            for cv_id, edu, sen, jt, loc in all_cvs_data:
                if (jt == "fulltime" and
                        sen == "lead" and
                        edu_rank.get(edu, -1) >= edu_rank["bachelor"] and
                        loc == "Hà Nội"):
                    passing_jd2.add(cv_id)
            check(
                "C15 JD-2 filter: CV 3007,3008 pass; CV 3009(high_school),3010(senior),3011(Đà Nẵng),3012(remote) filtered",
                {3007, 3008}.issubset(passing_jd2)
                    and 3009 not in passing_jd2
                    and 3010 not in passing_jd2
                    and 3011 not in passing_jd2
                    and 3012 not in passing_jd2,
                f"passing={sorted(passing_jd2)}"
            )

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    total = len(_results)
    failed = [name for name, ok, _ in _results if not ok]
    print(f"\n{'='*60}")
    print(f"Results: {total - len(failed)}/{total} passed")
    if failed:
        print("FAILED checks:")
        for name in failed:
            print(f"  - {name}")
        return 1
    print("All checks passed.")
    return 0


def main() -> int:
    return run_all()


if __name__ == "__main__":
    sys.exit(main())
