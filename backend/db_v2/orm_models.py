"""SQLAlchemy ORM models for Matching V2 prototype tables.

Scope lock: exactly 4 tables.
  - job_posts_v2
  - candidate_profiles_v2
  - job_embeddings_v2
  - candidate_embeddings_v2

Do NOT add match_results_v2 or any business lifecycle table (user, recruiter,
candidate, application).  These models are for seed tooling only — the runtime
matching path uses psycopg directly and must not import this module.

Schema source of truth: docs/REQUIREMENTS.md §5 and db_v2/migrations/001_init.sql.
Vector columns use pgvector.sqlalchemy.Vector(384) per Slice 6A requirement.
"""

from __future__ import annotations

from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import BigInteger, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobPostV2Orm(Base):
    """Maps to job_posts_v2. Scope: JD profile fields only."""

    __tablename__ = "job_posts_v2"
    __table_args__ = (
        CheckConstraint(
            "location IN ('Hà Nội','TP. Hồ Chí Minh','Đà Nẵng')",
            name="job_posts_v2_location_chk",
        ),
        CheckConstraint(
            "job_type IN ('remote','fulltime','parttime')",
            name="job_posts_v2_job_type_chk",
        ),
        CheckConstraint(
            "seniority IN ('intern','fresher','junior','mid','senior','lead')",
            name="job_posts_v2_seniority_chk",
        ),
        CheckConstraint(
            "education IN ('high_school','bachelor','master','phd')",
            name="job_posts_v2_education_chk",
        ),
    )

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    requirement: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    location: Mapped[str] = mapped_column(Text, nullable=False)
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    seniority: Mapped[str] = mapped_column(Text, nullable=False)
    education: Mapped[str] = mapped_column(Text, nullable=False)
    required_certifications: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )


class CandidateProfileV2Orm(Base):
    """Maps to candidate_profiles_v2. Scope: CV profile fields only."""

    __tablename__ = "candidate_profiles_v2"
    __table_args__ = (
        CheckConstraint(
            "location IN ('Hà Nội','TP. Hồ Chí Minh','Đà Nẵng')",
            name="candidate_profiles_v2_location_chk",
        ),
        CheckConstraint(
            "job_type IN ('remote','fulltime','parttime')",
            name="candidate_profiles_v2_job_type_chk",
        ),
        CheckConstraint(
            "seniority IN ('intern','fresher','junior','mid','senior','lead')",
            name="candidate_profiles_v2_seniority_chk",
        ),
        CheckConstraint(
            "education IN ('high_school','bachelor','master','phd')",
            name="candidate_profiles_v2_education_chk",
        ),
    )

    cv_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    experience: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    location: Mapped[str] = mapped_column(Text, nullable=False)
    job_type: Mapped[str] = mapped_column(Text, nullable=False)
    seniority: Mapped[str] = mapped_column(Text, nullable=False)
    education: Mapped[str] = mapped_column(Text, nullable=False)
    certifications: Mapped[list[str]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )


class JobEmbeddingsV2Orm(Base):
    """Maps to job_embeddings_v2. Vector columns use pgvector.sqlalchemy.Vector(384).

    All embedding columns are nullable — a missing embedding scores 0 in the
    matching pipeline per REQUIREMENTS.md §9.
    """

    __tablename__ = "job_embeddings_v2"

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    emb_title: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    emb_skills: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    emb_requirement: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)


class CandidateEmbeddingsV2Orm(Base):
    """Maps to candidate_embeddings_v2. Vector columns use pgvector.sqlalchemy.Vector(384).

    All embedding columns are nullable — a missing embedding scores 0 in the
    matching pipeline per REQUIREMENTS.md §9.
    """

    __tablename__ = "candidate_embeddings_v2"

    cv_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    emb_title: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    emb_skills: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    emb_summary: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
    emb_experience: Mapped[Optional[list[float]]] = mapped_column(Vector(384), nullable=True)
