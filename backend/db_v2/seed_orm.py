"""ORM-based seed tooling for Matching V2 prototype PostgreSQL database.

Mirrors the data from db_v2/seeds/001_seed.sql using SQLAlchemy ORM
instead of raw SQL, satisfying the Slice 6A ORM seed requirement.

Usage (with the postgres compose service running):

    python backend/db_v2/seed_orm.py

The script truncates the 4 prototype tables and re-inserts canonical seed data.
Connection details come from environment variables: POSTGRES_HOST, POSTGRES_PORT,
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB.

Scope lock: only operates on the 4 prototype tables.
Do NOT add match_results_v2 or any business lifecycle table here.
"""

from __future__ import annotations

import sys

import numpy as np
from sqlalchemy.orm import Session

from db_v2.orm_models import (
    CandidateEmbeddingsV2Orm,
    CandidateProfileV2Orm,
    JobEmbeddingsV2Orm,
    JobPostV2Orm,
)
from db_v2.session import get_v2_engine, make_session_factory


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _vec(value: float) -> list[float]:
    """Build a deterministic 384-dim vector filled with a single value."""
    return np.full(384, value, dtype=np.float32).tolist()


# ---------------------------------------------------------------------------
# Seed data — mirrors 001_seed.sql exactly
# ---------------------------------------------------------------------------

_CANDIDATES = [
    CandidateProfileV2Orm(
        cv_id=1001,
        title="Senior Backend Engineer",
        skills=["python", "fastapi", "postgres"],
        summary="Backend engineer with 6 years building REST APIs and data pipelines.",
        experience="6 years at fintech and e-commerce companies, owning Python services on PostgreSQL.",
        location="ha_noi",
        job_type="fulltime",
        seniority="senior",
        education="dai_hoc",
        certifications=["aws_saa"],
    ),
    CandidateProfileV2Orm(
        cv_id=1002,
        title="Junior Frontend Developer",
        skills=["react", "typescript", "vite"],
        summary="Frontend developer focused on React SPA work.",
        experience="1.5 years building React + TypeScript dashboards with Vite tooling.",
        location="tp_hcm",
        job_type="fulltime",
        seniority="junior",
        education="dai_hoc",
        certifications=[],
    ),
    CandidateProfileV2Orm(
        cv_id=1003,
        title="Senior Fullstack Engineer",
        skills=["python", "react", "postgres", "docker"],
        summary="Fullstack engineer comfortable across Python services and React apps.",
        experience="5 years building Python backends and React frontends, deploying via Docker.",
        location="ha_noi",
        job_type="remote",
        seniority="senior",
        education="thac_si",
        certifications=["aws_saa", "cka"],
    ),
    CandidateProfileV2Orm(
        cv_id=1004,
        title="Mid Backend Developer",
        skills=["java", "spring", "mysql"],
        summary="Java backend developer with Spring Boot focus.",
        experience="3 years writing Spring Boot services backed by MySQL.",
        location="da_nang",
        job_type="parttime",
        seniority="mid",
        education="lop_12",
        certifications=[],
    ),
    CandidateProfileV2Orm(
        cv_id=1005,
        title="Lead Data Engineer",
        skills=["python", "sql", "spark", "ml"],
        summary="Data engineering lead with hands-on Spark and ML pipeline experience.",
        experience="8 years building large-scale data pipelines and leading data platform teams.",
        location="ha_noi",
        job_type="fulltime",
        seniority="lead",
        education="tien_si",
        certifications=["databricks_de"],
    ),
]

_JOBS = [
    JobPostV2Orm(
        job_id=2001,
        title="Backend Engineer",
        skills=["python", "fastapi"],
        requirement="Build REST APIs in Python/FastAPI with PostgreSQL. 1-3 years experience.",
        location="ha_noi",
        job_type="fulltime",
        seniority="junior",
        education="dai_hoc",
        required_certifications=[],
    ),
    JobPostV2Orm(
        job_id=2002,
        title="Frontend Engineer",
        skills=["react", "typescript"],
        requirement="Build React + TypeScript SPAs. Familiar with modern Vite tooling.",
        location="tp_hcm",
        job_type="fulltime",
        seniority="junior",
        education="dai_hoc",
        required_certifications=[],
    ),
    JobPostV2Orm(
        job_id=2003,
        title="Senior Fullstack Engineer",
        skills=["python", "react", "postgres"],
        requirement="Own Python services and React UIs end-to-end. 5+ years experience.",
        location="ha_noi",
        job_type="remote",
        seniority="senior",
        education="dai_hoc",
        required_certifications=[],
    ),
    JobPostV2Orm(
        job_id=2004,
        title="Lead Data Engineer",
        skills=["python", "spark", "sql"],
        requirement="Lead a data platform team building Spark pipelines on PostgreSQL warehouse.",
        location="ha_noi",
        job_type="fulltime",
        seniority="lead",
        education="thac_si",
        required_certifications=["databricks_de"],
    ),
    JobPostV2Orm(
        job_id=2005,
        title="Java Backend Developer",
        skills=["java", "spring"],
        requirement="Maintain Spring Boot services. Part-time role at our Da Nang office.",
        location="da_nang",
        job_type="parttime",
        seniority="mid",
        education="lop_12",
        required_certifications=[],
    ),
]

_CANDIDATE_EMBEDDINGS = [
    CandidateEmbeddingsV2Orm(cv_id=1001, emb_title=_vec(0.10), emb_skills=_vec(0.11), emb_summary=_vec(0.12), emb_experience=_vec(0.13)),
    CandidateEmbeddingsV2Orm(cv_id=1002, emb_title=_vec(0.20), emb_skills=_vec(0.21), emb_summary=_vec(0.22), emb_experience=_vec(0.23)),
    CandidateEmbeddingsV2Orm(cv_id=1003, emb_title=_vec(0.30), emb_skills=_vec(0.31), emb_summary=_vec(0.32), emb_experience=_vec(0.33)),
    CandidateEmbeddingsV2Orm(cv_id=1004, emb_title=_vec(0.40), emb_skills=_vec(0.41), emb_summary=_vec(0.42), emb_experience=_vec(0.43)),
    CandidateEmbeddingsV2Orm(cv_id=1005, emb_title=_vec(0.50), emb_skills=_vec(0.51), emb_summary=_vec(0.52), emb_experience=_vec(0.53)),
]

_JOB_EMBEDDINGS = [
    JobEmbeddingsV2Orm(job_id=2001, emb_title=_vec(0.60), emb_skills=_vec(0.61), emb_requirement=_vec(0.62)),
    JobEmbeddingsV2Orm(job_id=2002, emb_title=_vec(0.65), emb_skills=_vec(0.66), emb_requirement=_vec(0.67)),
    JobEmbeddingsV2Orm(job_id=2003, emb_title=_vec(0.70), emb_skills=_vec(0.71), emb_requirement=_vec(0.72)),
    JobEmbeddingsV2Orm(job_id=2004, emb_title=_vec(0.75), emb_skills=_vec(0.76), emb_requirement=_vec(0.77)),
    JobEmbeddingsV2Orm(job_id=2005, emb_title=_vec(0.80), emb_skills=_vec(0.81), emb_requirement=_vec(0.82)),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def seed_all(session: Session) -> None:
    """Insert canonical seed data into the 4 prototype tables via ORM.

    Truncates all 4 tables first (CASCADE to handle FK order), then inserts
    in FK-safe order: profiles first, embeddings second.

    Scope lock: only the 4 prototype tables. No match_results_v2.
    """
    from sqlalchemy import text

    # Truncate all 4 tables in one statement (CASCADE handles FK ordering).
    session.execute(
        text(
            "TRUNCATE candidate_embeddings_v2, job_embeddings_v2, "
            "candidate_profiles_v2, job_posts_v2 RESTART IDENTITY CASCADE"
        )
    )

    session.add_all(_CANDIDATES)
    session.add_all(_JOBS)
    session.flush()  # ensure PKs are visible before FK inserts

    session.add_all(_CANDIDATE_EMBEDDINGS)
    session.add_all(_JOB_EMBEDDINGS)
    session.commit()


def main() -> int:
    engine = get_v2_engine()
    factory = make_session_factory(engine)
    with factory() as session:
        print("[seed_orm] truncating and re-seeding 4 prototype tables via ORM ...")
        seed_all(session)
    print("[seed_orm] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
