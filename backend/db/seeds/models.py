from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class Organization(Base):
    __tablename__ = "organizations"

    organization_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text)
    about: Mapped[Optional[str]] = mapped_column(Text)


class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(64))


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    current_location: Mapped[Optional[str]] = mapped_column(String(64))
    total_experience_years: Mapped[Optional[int]] = mapped_column()
    headline: Mapped[Optional[str]] = mapped_column(String(255))


class CandidateResume(Base):
    __tablename__ = "candidate_resumes"

    resume_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    experience: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    location: Mapped[str] = mapped_column(String(64), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    seniority: Mapped[str] = mapped_column(String(64), nullable=False)
    education: Mapped[str] = mapped_column(String(64), nullable=False)
    certifications: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")


class JobPost(Base):
    __tablename__ = "job_posts"

    job_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.organization_id"), nullable=False)
    recruiter_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    location: Mapped[str] = mapped_column(String(64), nullable=False)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    seniority: Mapped[str] = mapped_column(String(64), nullable=False)
    education: Mapped[str] = mapped_column(String(64), nullable=False)
    required_certifications: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CandidateResumeEmbedding(Base):
    __tablename__ = "candidate_resume_embeddings"

    resume_id: Mapped[int] = mapped_column(ForeignKey("candidate_resumes.resume_id"), primary_key=True)


class JobPostEmbedding(Base):
    __tablename__ = "job_post_embeddings"

    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.job_id"), primary_key=True)


class Application(Base):
    __tablename__ = "applications"

    application_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.job_id"), nullable=False)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    resume_id: Mapped[int] = mapped_column(ForeignKey("candidate_resumes.resume_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="submitted")
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    event_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    application_id: Mapped[int] = mapped_column(ForeignKey("applications.application_id"), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class RecruiterInvite(Base):
    __tablename__ = "recruiter_invites"

    invite_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_posts.job_id"), nullable=False)
    resume_id: Mapped[int] = mapped_column(ForeignKey("candidate_resumes.resume_id"), nullable=False)
    candidate_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    recruiter_user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


SEED_EMAIL_DOMAIN = "@example.local"
SEED_EMAIL_PREFIX = "seed+"
SEED_TITLE_PREFIX = "[SEED]"
SEED_ORG_SLUG_PREFIX = "seed-"
BOOTSTRAP_ORG_SLUG = "independent"
