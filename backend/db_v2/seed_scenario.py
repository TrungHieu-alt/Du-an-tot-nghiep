"""Seed the Matching V2 Slice 6B scenario dataset.

The seed is non-additive: it truncates only the four V2 prototype tables before
inserting the compact 6 JD / 36 CV scenario dataset and deterministic local
embeddings.

Usage:
    python backend/db_v2/seed_scenario.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import psycopg


DB_V2_DIR = Path(__file__).resolve().parent
BACKEND_DIR = DB_V2_DIR.parent
DEFAULT_DATASET = DB_V2_DIR / "scenarios" / "matching_v2_slice_6b.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from db_v2.scenario_embeddings import (  # noqa: E402
    build_embedding_payload,
    normalize_dataset,
    vector_to_pgvector,
)
from db_v2.validate_scenario_dataset import validate_dataset  # noqa: E402


def _conninfo() -> str:
    return (
        f"host={os.getenv('POSTGRES_HOST', 'localhost')} "
        f"port={os.getenv('POSTGRES_PORT', '5433')} "
        f"user={os.getenv('POSTGRES_USER', 'jobmatcher')} "
        f"password={os.getenv('POSTGRES_PASSWORD', 'jobmatcher')} "
        f"dbname={os.getenv('POSTGRES_DB', 'jobmatcher_v2')}"
    )


def load_dataset(path: Path = DEFAULT_DATASET) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return normalize_dataset(raw)


def seed_scenario(conn: psycopg.Connection, dataset_path: Path = DEFAULT_DATASET) -> None:
    """Validate, truncate, and insert the scenario dataset."""
    validate_dataset(dataset_path)
    dataset = load_dataset(dataset_path)
    embeddings = build_embedding_payload(dataset)

    with conn.cursor() as cur:
        cur.execute(
            """
            TRUNCATE candidate_embeddings_v2,
                     job_embeddings_v2,
                     candidate_profiles_v2,
                     job_posts_v2
            RESTART IDENTITY CASCADE
            """
        )
        _insert_jobs(cur, dataset["jobs"])
        _insert_candidates(cur, dataset["candidates"])
        _insert_job_embeddings(cur, embeddings["jobs"])
        _insert_candidate_embeddings(cur, embeddings["candidates"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    args = parser.parse_args()

    conninfo = _conninfo()
    print(f"[seed_scenario] connecting: {conninfo}")
    with psycopg.connect(conninfo, autocommit=False) as conn:
        print("[seed_scenario] validating dataset")
        seed_scenario(conn, args.dataset)
        conn.commit()
    print("[seed_scenario] inserted 6 JD, 36 CV, 6 job embeddings, 35 candidate embeddings")
    return 0


def _insert_jobs(cur: psycopg.Cursor, jobs: list[dict[str, Any]]) -> None:
    for job in jobs:
        cur.execute(
            """
            INSERT INTO job_posts_v2 (
                job_id, title, skills, requirement, location, job_type,
                seniority, education, required_certifications
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                job["job_id"],
                job["title"],
                job["skills"],
                job["requirement"],
                job["location"],
                job["job_type"],
                job["seniority"],
                job["education"],
                job["required_certifications"],
            ),
        )


def _insert_candidates(cur: psycopg.Cursor, candidates: list[dict[str, Any]]) -> None:
    for cv in candidates:
        cur.execute(
            """
            INSERT INTO candidate_profiles_v2 (
                cv_id, title, skills, summary, experience, location,
                job_type, seniority, education, certifications
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                cv["cv_id"],
                cv["title"],
                cv["skills"],
                cv["summary"],
                cv["experience"],
                cv["location"],
                cv["job_type"],
                cv["seniority"],
                cv["education"],
                cv["certifications"],
            ),
        )


def _insert_job_embeddings(
    cur: psycopg.Cursor,
    embeddings: dict[int, dict[str, list[float] | None]],
) -> None:
    for job_id, fields in sorted(embeddings.items()):
        cur.execute(
            """
            INSERT INTO job_embeddings_v2 (
                job_id, emb_title, emb_skills, emb_requirement
            )
            VALUES (%s, %s::vector, %s::vector, %s::vector)
            """,
            (
                job_id,
                vector_to_pgvector(fields["emb_title"]),
                vector_to_pgvector(fields["emb_skills"]),
                vector_to_pgvector(fields["emb_requirement"]),
            ),
        )


def _insert_candidate_embeddings(
    cur: psycopg.Cursor,
    embeddings: dict[int, dict[str, list[float] | None]],
) -> None:
    for cv_id, fields in sorted(embeddings.items()):
        cur.execute(
            """
            INSERT INTO candidate_embeddings_v2 (
                cv_id, emb_title, emb_skills, emb_summary, emb_experience
            )
            VALUES (%s, %s::vector, %s::vector, %s::vector, %s::vector)
            """,
            (
                cv_id,
                vector_to_pgvector(fields["emb_title"]),
                vector_to_pgvector(fields["emb_skills"]),
                vector_to_pgvector(fields["emb_summary"]),
                vector_to_pgvector(fields["emb_experience"]),
            ),
        )


if __name__ == "__main__":
    sys.exit(main())
