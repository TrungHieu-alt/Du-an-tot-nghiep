"""Read-only verification checks for Matching V2 prototype database.

Usage:
    python backend/db_v2/verify.py
"""

from __future__ import annotations

import os
import sys

import psycopg


EXPECTED_TABLES = {
    "candidate_profiles_v2",
    "job_posts_v2",
    "candidate_embeddings_v2",
    "job_embeddings_v2",
}


def _conninfo() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5433')} "
        f"user={os.getenv('POSTGRES_USER', 'jobmatcher')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'jobmatcher')} "
        f"dbname={os.getenv('POSTGRES_DB', 'jobmatcher_v2')}"
    )


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with psycopg.connect(_conninfo()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            tables = [row[0] for row in cur.fetchall()]
            _assert(set(tables) == EXPECTED_TABLES, f"unexpected tables: {tables}")

            cur.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'match_results_v2'
                """
            )
            _assert(cur.fetchone()[0] == 0, "match_results_v2 must not exist")

            cur.execute(
                """
                SELECT conname
                FROM pg_constraint
                WHERE conrelid::regclass::text IN ('candidate_profiles_v2', 'job_posts_v2')
                  AND contype = 'c'
                """
            )
            constraints = {row[0] for row in cur.fetchall()}
            required_constraints = {
                "candidate_profiles_v2_location_chk",
                "candidate_profiles_v2_job_type_chk",
                "candidate_profiles_v2_seniority_chk",
                "candidate_profiles_v2_education_chk",
                "job_posts_v2_location_chk",
                "job_posts_v2_job_type_chk",
                "job_posts_v2_seniority_chk",
                "job_posts_v2_education_chk",
            }
            _assert(required_constraints.issubset(constraints), "required CHECK constraints missing")

            cur.execute(
                """
                SELECT
                    vector_dims(ce.emb_title),
                    vector_dims(ce.emb_skills),
                    vector_dims(ce.emb_summary),
                    vector_dims(ce.emb_experience),
                    vector_dims(je.emb_title),
                    vector_dims(je.emb_skills),
                    vector_dims(je.emb_requirement)
                FROM candidate_embeddings_v2 ce
                JOIN job_embeddings_v2 je ON true
                LIMIT 1
                """
            )
            dims = cur.fetchone()
            _assert(dims is not None, "seed embeddings are missing")
            _assert(all(d == 384 for d in dims), f"embedding dimensions must be 384, got {dims}")

            cur.execute(
                """
                SELECT j.job_id, c.cv_id, vector_dims(je.emb_requirement), vector_dims(ce.emb_experience)
                FROM job_posts_v2 j
                JOIN job_embeddings_v2 je ON je.job_id = j.job_id
                JOIN candidate_profiles_v2 c ON true
                JOIN candidate_embeddings_v2 ce ON ce.cv_id = c.cv_id
                LIMIT 1
                """
            )
            sanity = cur.fetchone()
            _assert(sanity is not None, "sanity query failed to read JD/CV/embedding")

    print("verify_db_v2: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
