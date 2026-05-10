"""Non-additive scenario seed for Matching V2 Slice 6B.

Truncates the 4 prototype tables and inserts exactly 6 JDs + 36 CVs
from dataset.json, generating deterministic embeddings via embedder.py.
CV 3018 (has_embedding=false) intentionally has no embedding row.
Skills in dataset.json are normalized on load (lowercase, trim, dedupe).

Usage (from backend/ inside the container):
    python -m db_v2.scenario.reset_scenario

Connection: same env vars as matching_v2.db (POSTGRES_HOST, POSTGRES_PORT,
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB).

Scope lock: only the 4 prototype tables. Do NOT touch match_results_v2
or any production table.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from db_v2.orm_models import (
    CandidateEmbeddingsV2Orm,
    CandidateProfileV2Orm,
    JobEmbeddingsV2Orm,
    JobPostV2Orm,
)
from db_v2.scenario.embedder import embed_text
from db_v2.session import get_v2_engine, make_session_factory

_DATASET_PATH = Path(__file__).parent / "dataset.json"


# ---------------------------------------------------------------------------
# Skill normalization
# ---------------------------------------------------------------------------

def _normalize_skills(skills: list[str]) -> list[str]:
    """Lowercase, strip, deduplicate preserving first-occurrence order."""
    seen: dict[str, None] = {}
    for s in skills:
        key = s.strip().lower()
        if key:
            seen[key] = None
    return list(seen.keys())


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------

def seed_scenario(session: Session) -> None:
    dataset = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))

    # Truncate all 4 tables in one statement (CASCADE handles FK ordering).
    session.execute(
        text(
            "TRUNCATE candidate_embeddings_v2, job_embeddings_v2, "
            "candidate_profiles_v2, job_posts_v2 RESTART IDENTITY CASCADE"
        )
    )

    # ----- Insert jobs -----
    job_orm_list: list[JobPostV2Orm] = []
    for j in dataset["jobs"]:
        job_orm_list.append(
            JobPostV2Orm(
                job_id=j["job_id"],
                title=j["title"],
                skills=_normalize_skills(j["skills"]),
                requirement=j["requirement"],
                location=j["location"],
                job_type=j["job_type"],
                seniority=j["seniority"],
                education=j["education"],
                required_certifications=_normalize_skills(j["required_certifications"]),
            )
        )
    session.add_all(job_orm_list)

    # ----- Insert candidates -----
    cv_orm_list: list[CandidateProfileV2Orm] = []
    for c in dataset["candidates"]:
        cv_orm_list.append(
            CandidateProfileV2Orm(
                cv_id=c["cv_id"],
                title=c["title"],
                skills=_normalize_skills(c["skills"]),
                summary=c["summary"],
                experience=c["experience"],
                location=c["location"],
                job_type=c["job_type"],
                seniority=c["seniority"],
                education=c["education"],
                certifications=_normalize_skills(c["certifications"]),
            )
        )
    session.add_all(cv_orm_list)
    session.flush()  # ensure PKs visible before FK inserts

    # ----- Insert job embeddings -----
    job_emb_list: list[JobEmbeddingsV2Orm] = []
    for j in dataset["jobs"]:
        skills_text = " ".join(_normalize_skills(j["skills"]))
        job_emb_list.append(
            JobEmbeddingsV2Orm(
                job_id=j["job_id"],
                emb_title=embed_text(j["title"]).tolist(),
                emb_skills=embed_text(skills_text).tolist(),
                emb_requirement=embed_text(j["requirement"]).tolist(),
            )
        )
    session.add_all(job_emb_list)

    # ----- Insert candidate embeddings (skip has_embedding=false) -----
    cv_emb_list: list[CandidateEmbeddingsV2Orm] = []
    for c in dataset["candidates"]:
        if not c["has_embedding"]:
            print(f"  [skip embedding] cv_id={c['cv_id']} ({c['role']})")
            continue
        skills_text = " ".join(_normalize_skills(c["skills"]))
        cv_emb_list.append(
            CandidateEmbeddingsV2Orm(
                cv_id=c["cv_id"],
                emb_title=embed_text(c["title"]).tolist(),
                emb_skills=embed_text(skills_text).tolist(),
                emb_summary=embed_text(c["summary"]).tolist(),
                emb_experience=embed_text(c["experience"]).tolist(),
            )
        )
    session.add_all(cv_emb_list)
    session.commit()

    print(
        f"[reset_scenario] inserted {len(job_orm_list)} jobs, "
        f"{len(cv_orm_list)} candidates, "
        f"{len(job_emb_list)} job embeddings, "
        f"{len(cv_emb_list)} candidate embeddings"
    )


def main() -> int:
    engine = get_v2_engine()
    factory = make_session_factory(engine)
    print("[reset_scenario] truncating and re-seeding 4 prototype tables ...")
    with factory() as session:
        seed_scenario(session)
    print("[reset_scenario] done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
