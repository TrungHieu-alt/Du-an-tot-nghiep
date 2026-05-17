from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db.seeds.models import (
    BOOTSTRAP_ORG_SLUG,
    SEED_TITLE_PREFIX,
    Application,
    ApplicationEvent,
    CandidateProfile,
    CandidateResume,
    JobPost,
    Organization,
    RecruiterInvite,
    RecruiterProfile,
    User,
)
from jobconnect.modules.api.shared import hash_password
from jobconnect.modules.matching.embedding import embed_text


@dataclass(frozen=True)
class DemoCredentials:
    candidate_email: str = "seed+candidate1@example.local"
    recruiter_email: str = "seed+recruiter1@example.local"
    admin_email: str = "seed+admin1@example.local"
    default_password: str = "SeedPass123!"


class DemoSeeder:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.metrics: dict[str, int] = {
            "users_created": 0,
            "users_updated": 0,
            "organizations_created": 0,
            "organizations_updated": 0,
            "candidate_profiles_created": 0,
            "candidate_profiles_updated": 0,
            "recruiter_profiles_created": 0,
            "recruiter_profiles_updated": 0,
            "resumes_created": 0,
            "resumes_updated": 0,
            "jobs_created": 0,
            "jobs_updated": 0,
            "resume_embeddings_upserted": 0,
            "job_embeddings_upserted": 0,
            "applications_created": 0,
            "application_events_created": 0,
            "invites_created": 0,
        }
        self.creds = DemoCredentials()

    def seed(self, target: str = "all") -> dict[str, int]:
        context = self._seed_identities()

        if target in {"all", "resumes"}:
            resume = self._seed_resume(context["candidate_user_id"])
            self._upsert_resume_embedding(resume.resume_id, resume)
        else:
            resume = self._get_resume(context["candidate_user_id"])

        if target in {"all", "jobs"}:
            job = self._seed_job(context["recruiter_user_id"], context["demo_org_id"])
            self._upsert_job_embedding(job.job_id, job)
        else:
            job = self._get_job(context["recruiter_user_id"])

        if target in {"all", "jobs", "resumes"} and job is not None and resume is not None:
            self._seed_application_and_invite(
                job_id=job.job_id,
                resume_id=resume.resume_id,
                candidate_user_id=context["candidate_user_id"],
                recruiter_user_id=context["recruiter_user_id"],
            )

        return self.metrics

    def _seed_identities(self) -> dict[str, int]:
        self._upsert_organization(
            slug=BOOTSTRAP_ORG_SLUG,
            name="Independent",
            logo_url=None,
            about="Shared profile bucket for independent/freelance recruiters.",
        )

        demo_org = self._upsert_organization(
            slug="seed-acme",
            name="Seed Acme Recruiting",
            logo_url=None,
            about="[SEED] Demo organization for recruiter onboarding and job flow checks.",
        )

        candidate = self._upsert_user(self.creds.candidate_email, "candidate", "active", self.creds.default_password)
        recruiter = self._upsert_user(self.creds.recruiter_email, "recruiter", "active", self.creds.default_password)
        self._upsert_user(self.creds.admin_email, "admin", "active", self.creds.default_password)

        self._upsert_candidate_profile(candidate.user_id)
        self._upsert_recruiter_profile(recruiter.user_id, demo_org.organization_id)

        return {
            "candidate_user_id": candidate.user_id,
            "recruiter_user_id": recruiter.user_id,
            "demo_org_id": demo_org.organization_id,
        }

    def _upsert_user(self, email: str, role: str, status: str, password: str) -> User:
        row = self.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        password_hash = hash_password(password)
        if row is None:
            row = User(email=email, role=role, status=status, password_hash=password_hash)
            self.session.add(row)
            self.session.flush()
            self.metrics["users_created"] += 1
            return row

        row.role = role
        row.status = status
        row.password_hash = password_hash
        self.session.flush()
        self.metrics["users_updated"] += 1
        return row

    def _upsert_organization(
        self,
        *,
        slug: str,
        name: str,
        logo_url: str | None,
        about: str | None,
    ) -> Organization:
        row = self.session.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none()
        if row is None:
            row = Organization(slug=slug, name=name, logo_url=logo_url, about=about)
            self.session.add(row)
            self.session.flush()
            self.metrics["organizations_created"] += 1
            return row

        row.name = name
        row.logo_url = logo_url
        row.about = about
        self.session.flush()
        self.metrics["organizations_updated"] += 1
        return row

    def _upsert_candidate_profile(self, user_id: int) -> CandidateProfile:
        row = self.session.execute(select(CandidateProfile).where(CandidateProfile.user_id == user_id)).scalar_one_or_none()
        if row is None:
            row = CandidateProfile(
                user_id=user_id,
                full_name="Seed Candidate One",
                phone="0900000001",
                current_location="tp_hcm",
                total_experience_years=4,
                headline="[SEED] Backend Engineer",
            )
            self.session.add(row)
            self.session.flush()
            self.metrics["candidate_profiles_created"] += 1
            return row

        row.full_name = "Seed Candidate One"
        row.phone = "0900000001"
        row.current_location = "tp_hcm"
        row.total_experience_years = 4
        row.headline = "[SEED] Backend Engineer"
        self.session.flush()
        self.metrics["candidate_profiles_updated"] += 1
        return row

    def _upsert_recruiter_profile(self, user_id: int, organization_id: int) -> RecruiterProfile:
        row = self.session.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == user_id)).scalar_one_or_none()
        if row is None:
            row = RecruiterProfile(
                user_id=user_id,
                organization_id=organization_id,
                full_name="Seed Recruiter One",
                title="Technical Recruiter",
                phone="0900000002",
            )
            self.session.add(row)
            self.session.flush()
            self.metrics["recruiter_profiles_created"] += 1
            return row

        row.organization_id = organization_id
        row.full_name = "Seed Recruiter One"
        row.title = "Technical Recruiter"
        row.phone = "0900000002"
        self.session.flush()
        self.metrics["recruiter_profiles_updated"] += 1
        return row

    def _seed_resume(self, candidate_user_id: int) -> CandidateResume:
        title = f"{SEED_TITLE_PREFIX} Candidate Resume Backend Mid"
        row = self.session.execute(
            select(CandidateResume).where(
                CandidateResume.candidate_user_id == candidate_user_id,
                CandidateResume.title == title,
            )
        ).scalar_one_or_none()

        if row is None:
            row = CandidateResume(
                candidate_user_id=candidate_user_id,
                title=title,
                summary="Backend engineer focused on FastAPI, PostgreSQL, and production operations.",
                experience=(
                    "Built API modules, optimized SQL queries, and operated CI/CD deployment pipelines "
                    "for marketplace products."
                ),
                skills=["python", "fastapi", "postgresql", "docker", "sqlalchemy"],
                location="tp_hcm",
                job_type="fulltime",
                seniority="mid",
                education="dai_hoc",
                certifications=["aws certified developer associate"],
                is_primary=True,
                status="active",
            )
            self.session.add(row)
            self.session.flush()
            self.metrics["resumes_created"] += 1
            return row

        row.summary = "Backend engineer focused on FastAPI, PostgreSQL, and production operations."
        row.experience = (
            "Built API modules, optimized SQL queries, and operated CI/CD deployment pipelines "
            "for marketplace products."
        )
        row.skills = ["python", "fastapi", "postgresql", "docker", "sqlalchemy"]
        row.location = "tp_hcm"
        row.job_type = "fulltime"
        row.seniority = "mid"
        row.education = "dai_hoc"
        row.certifications = ["aws certified developer associate"]
        row.is_primary = True
        row.status = "active"
        self.session.flush()
        self.metrics["resumes_updated"] += 1
        return row

    def _seed_job(self, recruiter_user_id: int, organization_id: int) -> JobPost:
        title = f"{SEED_TITLE_PREFIX} Backend Engineer Mid"
        row = self.session.execute(
            select(JobPost).where(
                JobPost.recruiter_user_id == recruiter_user_id,
                JobPost.title == title,
            )
        ).scalar_one_or_none()

        published_at = datetime.now(timezone.utc)
        if row is None:
            row = JobPost(
                organization_id=organization_id,
                recruiter_user_id=recruiter_user_id,
                title=title,
                requirement=(
                    "Need backend engineer for FastAPI, PostgreSQL, Docker, and production monitoring. "
                    "Collaborate with product and data teams."
                ),
                skills=["python", "fastapi", "postgresql", "docker", "sqlalchemy"],
                location="tp_hcm",
                job_type="fulltime",
                seniority="mid",
                education="dai_hoc",
                required_certifications=["aws certified developer associate"],
                status="published",
                published_at=published_at,
            )
            self.session.add(row)
            self.session.flush()
            self.metrics["jobs_created"] += 1
            return row

        row.organization_id = organization_id
        row.requirement = (
            "Need backend engineer for FastAPI, PostgreSQL, Docker, and production monitoring. "
            "Collaborate with product and data teams."
        )
        row.skills = ["python", "fastapi", "postgresql", "docker", "sqlalchemy"]
        row.location = "tp_hcm"
        row.job_type = "fulltime"
        row.seniority = "mid"
        row.education = "dai_hoc"
        row.required_certifications = ["aws certified developer associate"]
        row.status = "published"
        row.published_at = published_at
        self.session.flush()
        self.metrics["jobs_updated"] += 1
        return row

    def _upsert_resume_embedding(self, resume_id: int, resume: CandidateResume) -> None:
        emb_title = _vector_literal(embed_text(resume.title).tolist())
        emb_skills = _vector_literal(embed_text(" ".join(resume.skills)).tolist())
        emb_summary = _vector_literal(embed_text(resume.summary).tolist())
        emb_experience = _vector_literal(embed_text(resume.experience).tolist())

        self.session.execute(
            text(
                """
                INSERT INTO candidate_resume_embeddings
                    (resume_id, emb_title, emb_skills, emb_summary, emb_experience, embedding_version, updated_at)
                VALUES
                    (:resume_id, CAST(:emb_title AS vector), CAST(:emb_skills AS vector),
                     CAST(:emb_summary AS vector), CAST(:emb_experience AS vector), :embedding_version, now())
                ON CONFLICT (resume_id) DO UPDATE
                SET
                    emb_title = EXCLUDED.emb_title,
                    emb_skills = EXCLUDED.emb_skills,
                    emb_summary = EXCLUDED.emb_summary,
                    emb_experience = EXCLUDED.emb_experience,
                    embedding_version = EXCLUDED.embedding_version,
                    updated_at = now()
                """
            ),
            {
                "resume_id": resume_id,
                "emb_title": emb_title,
                "emb_skills": emb_skills,
                "emb_summary": emb_summary,
                "emb_experience": emb_experience,
                "embedding_version": "hash-v1",
            },
        )
        self.metrics["resume_embeddings_upserted"] += 1

    def _upsert_job_embedding(self, job_id: int, job: JobPost) -> None:
        emb_title = _vector_literal(embed_text(job.title).tolist())
        emb_skills = _vector_literal(embed_text(" ".join(job.skills)).tolist())
        emb_requirement = _vector_literal(embed_text(job.requirement).tolist())

        self.session.execute(
            text(
                """
                INSERT INTO job_post_embeddings
                    (job_id, emb_title, emb_skills, emb_requirement, embedding_version, updated_at)
                VALUES
                    (:job_id, CAST(:emb_title AS vector), CAST(:emb_skills AS vector),
                     CAST(:emb_requirement AS vector), :embedding_version, now())
                ON CONFLICT (job_id) DO UPDATE
                SET
                    emb_title = EXCLUDED.emb_title,
                    emb_skills = EXCLUDED.emb_skills,
                    emb_requirement = EXCLUDED.emb_requirement,
                    embedding_version = EXCLUDED.embedding_version,
                    updated_at = now()
                """
            ),
            {
                "job_id": job_id,
                "emb_title": emb_title,
                "emb_skills": emb_skills,
                "emb_requirement": emb_requirement,
                "embedding_version": "hash-v1",
            },
        )
        self.metrics["job_embeddings_upserted"] += 1

    def _seed_application_and_invite(
        self,
        *,
        job_id: int,
        resume_id: int,
        candidate_user_id: int,
        recruiter_user_id: int,
    ) -> None:
        application = self.session.execute(
            select(Application).where(Application.job_id == job_id, Application.resume_id == resume_id)
        ).scalar_one_or_none()

        if application is None:
            application = Application(
                job_id=job_id,
                resume_id=resume_id,
                candidate_user_id=candidate_user_id,
                status="submitted",
            )
            self.session.add(application)
            self.session.flush()
            self.metrics["applications_created"] += 1

        event = self.session.execute(
            select(ApplicationEvent).where(
                ApplicationEvent.application_id == application.application_id,
                ApplicationEvent.to_status == "submitted",
                ApplicationEvent.note == "seed_initial_submission",
            )
        ).scalar_one_or_none()
        if event is None:
            self.session.add(
                ApplicationEvent(
                    application_id=application.application_id,
                    from_status=None,
                    to_status="submitted",
                    actor_user_id=candidate_user_id,
                    note="seed_initial_submission",
                )
            )
            self.session.flush()
            self.metrics["application_events_created"] += 1

        invite = self.session.execute(
            select(RecruiterInvite).where(
                RecruiterInvite.job_id == job_id,
                RecruiterInvite.resume_id == resume_id,
                RecruiterInvite.status == "pending",
                RecruiterInvite.message == "[SEED] Demo invite from recruiter to candidate.",
            )
        ).scalar_one_or_none()
        if invite is None:
            self.session.add(
                RecruiterInvite(
                    job_id=job_id,
                    resume_id=resume_id,
                    candidate_user_id=candidate_user_id,
                    recruiter_user_id=recruiter_user_id,
                    status="pending",
                    message="[SEED] Demo invite from recruiter to candidate.",
                )
            )
            self.session.flush()
            self.metrics["invites_created"] += 1

    def _get_resume(self, candidate_user_id: int) -> CandidateResume | None:
        title = f"{SEED_TITLE_PREFIX} Candidate Resume Backend Mid"
        return self.session.execute(
            select(CandidateResume).where(
                CandidateResume.candidate_user_id == candidate_user_id,
                CandidateResume.title == title,
            )
        ).scalar_one_or_none()

    def _get_job(self, recruiter_user_id: int) -> JobPost | None:
        title = f"{SEED_TITLE_PREFIX} Backend Engineer Mid"
        return self.session.execute(
            select(JobPost).where(
                JobPost.recruiter_user_id == recruiter_user_id,
                JobPost.title == title,
            )
        ).scalar_one_or_none()


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{float(v):.8f}" for v in values) + "]"


def run_demo_seed(session: Session, target: str = "all") -> dict[str, Any]:
    seeder = DemoSeeder(session)
    return seeder.seed(target=target)
