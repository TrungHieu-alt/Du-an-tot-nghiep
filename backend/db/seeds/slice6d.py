from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import random
from typing import Any

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from db.seeds.models import (
    Application,
    ApplicationEvent,
    BOOTSTRAP_ORG_SLUG,
    CandidateProfile,
    CandidateResume,
    CandidateResumeEmbedding,
    JobPost,
    JobPostEmbedding,
    Organization,
    RecruiterInvite,
    RecruiterProfile,
    User,
)
from jobconnect.integrations.embedding import get_embedding_provider
from jobconnect.modules.api.shared import hash_password
from jobconnect.modules.matching.embedding import embed_text

LOCATIONS = ("ha_noi", "tp_hcm", "da_nang")
JOB_TYPES = ("remote", "fulltime", "parttime")
SENIORITIES = ("intern", "fresher", "junior", "mid", "senior", "lead")
EDUCATIONS = ("lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si")
LABELS = (
    "strong_pass",
    "good_pass",
    "title_match_low_skill",
    "skill_match_hard_filter_fail",
    "education_or_cert_fail",
    "noisy_pass",
)
SEED_PREFIX = "[SEED-6D]"
DEFAULT_SEED = 20260517
JOB_ID_START = 2101
JOB_COUNT = 40
RESUME_ID_START = 11001
RESUME_COUNT = 240
RECRUITER_USER_ID_START = 5001
CANDIDATE_USER_ID_START = 6001
ADMIN_USER_ID = 7001
ORG_ID_START = 8001
ORG_COUNT = 8
INDEPENDENT_ORG_ID = 8999


@dataclass(frozen=True)
class Slice6DConfig:
    seed: int = DEFAULT_SEED


def generate_dataset(config: Slice6DConfig) -> dict[str, Any]:
    rng = random.Random(config.seed)
    jobs: list[dict[str, Any]] = []
    resumes: list[dict[str, Any]] = []
    matrix: list[dict[str, Any]] = []

    batch_names = [
        "it_software_qa",
        "it_data_devops",
        "it_security_ai_ml",
        "ai_bi_data_product_ba",
        "product_project_sales_marketing_cs",
        "finance_accounting_hr_admin",
        "design_ux_content_ops",
        "ops_logistics_education_healthcare_service",
    ]
    family_names = [
        "backend-platform",
        "frontend-web",
        "data-ai",
        "product-ba",
        "sales-marketing",
        "finance-hr-admin",
        "design-content",
        "ops-logistics",
    ]
    fail_hard_modes = ["location", "job_type", "seniority", "location", "job_type", "seniority", "location", "seniority"]
    fail_edu_or_cert_modes = ["education", "certification", "education", "certification", "education", "certification", "education", "certification"]

    for batch_idx in range(8):
        batch_id = f"batch_{batch_idx + 1:02d}"
        for offset in range(5):
            job_idx = batch_idx * 5 + offset
            job_id = JOB_ID_START + job_idx
            recruiter_user_id = RECRUITER_USER_ID_START + job_idx
            organization_id = ORG_ID_START + batch_idx
            family = family_names[batch_idx]
            mode_hard = fail_hard_modes[(batch_idx + offset) % len(fail_hard_modes)]
            mode_edu_or_cert = fail_edu_or_cert_modes[(batch_idx + offset) % len(fail_edu_or_cert_modes)]
            is_remote = (job_idx % 5 == 0)
            location = LOCATIONS[job_idx % len(LOCATIONS)]
            job_type = "remote" if is_remote else JOB_TYPES[(job_idx + 1) % len(JOB_TYPES)]
            seniority = SENIORITIES[min(5, 2 + (job_idx % 4))]
            education = EDUCATIONS[min(4, 2 + (job_idx % 3))]
            certifications = _normalize_terms([f"{family}-cert-a", f"{family}-cert-b"] if mode_edu_or_cert == "certification" else [f"{family}-cert-a"])
            skill_pool = _skill_pool(family)

            job = {
                "job_id": job_id,
                "batch_id": batch_id,
                "industry_group": batch_names[batch_idx],
                "family": family,
                "title": f"{SEED_PREFIX} {family} role {job_id}",
                "requirement": f"{family} requirement for role {job_id} with practical delivery ownership and collaboration.",
                "skills": skill_pool[:6],
                "location": location,
                "job_type": job_type,
                "seniority": seniority,
                "education": education,
                "required_certifications": certifications,
                "status": "published",
            }
            jobs.append(job)

            label_builders = [
                _make_strong_resume,
                _make_good_resume,
                _make_title_match_low_skill_resume,
                _make_skill_match_hard_filter_fail_resume,
                _make_education_or_cert_fail_resume,
                _make_noisy_resume,
            ]
            for label_idx, builder in enumerate(label_builders):
                resume_idx = job_idx * 6 + label_idx
                resume_id = RESUME_ID_START + resume_idx
                candidate_user_id = CANDIDATE_USER_ID_START + resume_idx
                item = builder(
                    rng=rng,
                    job=job,
                    resume_id=resume_id,
                    candidate_user_id=candidate_user_id,
                    fail_hard_mode=mode_hard,
                    fail_edu_or_cert_mode=mode_edu_or_cert,
                )
                resumes.append(item["resume"])
                matrix.append(item["meta"])

    return {"jobs": jobs, "resumes": resumes, "matrix": matrix}


def validate_preseed_dataset(dataset: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    jobs = dataset["jobs"]
    resumes = dataset["resumes"]
    matrix = dataset["matrix"]
    job_ids = {j["job_id"] for j in jobs}
    resume_ids = set()

    if len(jobs) != JOB_COUNT:
        errors.append(f"jobs count must be {JOB_COUNT}, got {len(jobs)}")
    if len(resumes) != RESUME_COUNT:
        errors.append(f"resumes count must be {RESUME_COUNT}, got {len(resumes)}")
    if len(matrix) != RESUME_COUNT:
        errors.append(f"matrix count must be {RESUME_COUNT}, got {len(matrix)}")

    for job in jobs:
        if job["location"] not in LOCATIONS:
            errors.append(f"job {job['job_id']} invalid location")
        if job["job_type"] not in JOB_TYPES:
            errors.append(f"job {job['job_id']} invalid job_type")
        if job["seniority"] not in SENIORITIES:
            errors.append(f"job {job['job_id']} invalid seniority")
        if job["education"] not in EDUCATIONS:
            errors.append(f"job {job['job_id']} invalid education")
        if job["status"] != "published":
            errors.append(f"job {job['job_id']} status must be published")
        if job["job_id"] < JOB_ID_START or job["job_id"] >= JOB_ID_START + JOB_COUNT:
            errors.append(f"job {job['job_id']} out of range")
        if job["skills"] != _normalize_terms(job["skills"]):
            errors.append(f"job {job['job_id']} skills not normalized")
        if job["required_certifications"] != _normalize_terms(job["required_certifications"]):
            errors.append(f"job {job['job_id']} required_certifications not normalized")

    labels_by_job: dict[int, set[str]] = {}
    for meta in matrix:
        labels_by_job.setdefault(meta["job_id"], set()).add(meta["design_label"])
        if meta["design_label"] not in LABELS:
            errors.append(f"job {meta['job_id']} resume {meta['resume_id']} invalid label")
        if meta["job_id"] not in job_ids:
            errors.append(f"job {meta['job_id']} missing for matrix mapping")

    for job_id, labels in labels_by_job.items():
        if labels != set(LABELS):
            errors.append(f"job {job_id} label coverage mismatch")

    for resume in resumes:
        rid = resume["resume_id"]
        if rid in resume_ids:
            errors.append(f"duplicate resume_id {rid}")
        resume_ids.add(rid)
        if resume["location"] not in LOCATIONS:
            errors.append(f"resume {rid} invalid location")
        if resume["job_type"] not in JOB_TYPES:
            errors.append(f"resume {rid} invalid job_type")
        if resume["seniority"] not in SENIORITIES:
            errors.append(f"resume {rid} invalid seniority")
        if resume["education"] not in EDUCATIONS:
            errors.append(f"resume {rid} invalid education")
        if resume["status"] != "active":
            errors.append(f"resume {rid} status must be active")
        if resume["resume_id"] < RESUME_ID_START or resume["resume_id"] >= RESUME_ID_START + RESUME_COUNT:
            errors.append(f"resume {rid} out of range")
        if resume["skills"] != _normalize_terms(resume["skills"]):
            errors.append(f"resume {rid} skills not normalized")
        if resume["certifications"] != _normalize_terms(resume["certifications"]):
            errors.append(f"resume {rid} certifications not normalized")

    return errors


def seed_broad_6d(session: Session, config: Slice6DConfig) -> dict[str, Any]:
    dataset = generate_dataset(config)
    errors = validate_preseed_dataset(dataset)
    if errors:
        raise ValueError("pre-seed validation failed: " + "; ".join(errors[:8]))

    metrics: dict[str, Any] = {"seed": config.seed}
    _reset_slice6d_data(session, metrics)
    _seed_foundation(session, metrics)
    _seed_jobs_and_resumes(session, dataset, metrics)
    return metrics


def backfill_embeddings_6d(session: Session) -> dict[str, Any]:
    provider = get_embedding_provider()
    metrics: dict[str, Any] = {"provider_embedding_version": provider.embedding_version, "provider_dim": provider.dim}

    job_rows = list(session.execute(select(JobPost).where(JobPost.job_id >= JOB_ID_START, JobPost.job_id < JOB_ID_START + JOB_COUNT)).scalars())
    resume_rows = list(
        session.execute(
            select(CandidateResume).where(
                CandidateResume.resume_id >= RESUME_ID_START,
                CandidateResume.resume_id < RESUME_ID_START + RESUME_COUNT,
            )
        ).scalars()
    )

    upserted_jobs = 0
    upserted_resumes = 0
    for job in job_rows:
        emb_title = _vector_literal(provider.embed(job.title))
        emb_skills = _vector_literal(provider.embed(" ".join(job.skills or [])))
        emb_requirement = _vector_literal(provider.embed(job.requirement))
        session.execute(
            text(
                """
                INSERT INTO job_post_embeddings
                    (job_id, emb_title, emb_skills, emb_requirement, embedding_version, updated_at)
                VALUES
                    (:job_id, CAST(:emb_title AS vector), CAST(:emb_skills AS vector),
                     CAST(:emb_requirement AS vector), :embedding_version, now())
                ON CONFLICT (job_id) DO UPDATE
                SET emb_title = EXCLUDED.emb_title,
                    emb_skills = EXCLUDED.emb_skills,
                    emb_requirement = EXCLUDED.emb_requirement,
                    embedding_version = EXCLUDED.embedding_version,
                    updated_at = now()
                """
            ),
            {
                "job_id": job.job_id,
                "emb_title": emb_title,
                "emb_skills": emb_skills,
                "emb_requirement": emb_requirement,
                "embedding_version": provider.embedding_version,
            },
        )
        upserted_jobs += 1

    for resume in resume_rows:
        emb_title = _vector_literal(provider.embed(resume.title))
        emb_skills = _vector_literal(provider.embed(" ".join(resume.skills or [])))
        emb_summary = _vector_literal(provider.embed(resume.summary))
        emb_experience = _vector_literal(provider.embed(resume.experience))
        session.execute(
            text(
                """
                INSERT INTO candidate_resume_embeddings
                    (resume_id, emb_title, emb_skills, emb_summary, emb_experience, embedding_version, updated_at)
                VALUES
                    (:resume_id, CAST(:emb_title AS vector), CAST(:emb_skills AS vector),
                     CAST(:emb_summary AS vector), CAST(:emb_experience AS vector), :embedding_version, now())
                ON CONFLICT (resume_id) DO UPDATE
                SET emb_title = EXCLUDED.emb_title,
                    emb_skills = EXCLUDED.emb_skills,
                    emb_summary = EXCLUDED.emb_summary,
                    emb_experience = EXCLUDED.emb_experience,
                    embedding_version = EXCLUDED.embedding_version,
                    updated_at = now()
                """
            ),
            {
                "resume_id": resume.resume_id,
                "emb_title": emb_title,
                "emb_skills": emb_skills,
                "emb_summary": emb_summary,
                "emb_experience": emb_experience,
                "embedding_version": provider.embedding_version,
            },
        )
        upserted_resumes += 1

    metrics["job_embeddings_upserted"] = upserted_jobs
    metrics["resume_embeddings_upserted"] = upserted_resumes
    return metrics


def validate_postseed_db(session: Session) -> list[str]:
    errors: list[str] = []

    row = session.execute(
        text(
            """
            SELECT
              (SELECT COUNT(*) FROM job_posts WHERE job_id >= :job_start AND job_id < :job_end) AS job_count,
              (SELECT COUNT(*) FROM candidate_resumes WHERE resume_id >= :resume_start AND resume_id < :resume_end) AS resume_count,
              (SELECT COUNT(*) FROM job_post_embeddings WHERE job_id >= :job_start AND job_id < :job_end) AS job_emb_count,
              (SELECT COUNT(*) FROM candidate_resume_embeddings WHERE resume_id >= :resume_start AND resume_id < :resume_end) AS resume_emb_count
            """
        ),
        {
            "job_start": JOB_ID_START,
            "job_end": JOB_ID_START + JOB_COUNT,
            "resume_start": RESUME_ID_START,
            "resume_end": RESUME_ID_START + RESUME_COUNT,
        },
    ).one()
    job_count, resume_count, job_emb_count, resume_emb_count = row

    if job_count != JOB_COUNT:
        errors.append(f"job_posts count expected {JOB_COUNT}, got {job_count}")
    if resume_count != RESUME_COUNT:
        errors.append(f"candidate_resumes count expected {RESUME_COUNT}, got {resume_count}")
    if job_emb_count != JOB_COUNT:
        errors.append(f"job_post_embeddings count expected {JOB_COUNT}, got {job_emb_count}")
    if resume_emb_count != RESUME_COUNT:
        errors.append(f"candidate_resume_embeddings count expected {RESUME_COUNT}, got {resume_emb_count}")
    return errors


def _seed_foundation(session: Session, metrics: dict[str, Any]) -> None:
    _upsert_admin(session)
    _upsert_organizations(session)
    recruiter_created = recruiter_updated = 0
    candidate_created = candidate_updated = 0
    recruiter_profile_created = recruiter_profile_updated = 0
    candidate_profile_created = candidate_profile_updated = 0

    # Upsert users first, then flush to satisfy FK constraints before profile writes.
    for idx in range(JOB_COUNT):
        user_id = RECRUITER_USER_ID_START + idx
        created = _upsert_user(
            session,
            user_id=user_id,
            email=f"seed+6d-recruiter{idx + 1}@example.local",
            role="recruiter",
            status="active",
        )
        recruiter_created += int(created)
        recruiter_updated += int(not created)

    for idx in range(RESUME_COUNT):
        user_id = CANDIDATE_USER_ID_START + idx
        created = _upsert_user(
            session,
            user_id=user_id,
            email=f"seed+6d-candidate{idx + 1}@example.local",
            role="candidate",
            status="active",
        )
        candidate_created += int(created)
        candidate_updated += int(not created)

    session.flush()

    for idx in range(JOB_COUNT):
        user_id = RECRUITER_USER_ID_START + idx
        org_id = ORG_ID_START + (idx // 5)
        created_prof = _upsert_recruiter_profile(session, user_id=user_id, organization_id=org_id)
        recruiter_profile_created += int(created_prof)
        recruiter_profile_updated += int(not created_prof)

    for idx in range(RESUME_COUNT):
        user_id = CANDIDATE_USER_ID_START + idx
        created_prof = _upsert_candidate_profile(session, user_id=user_id, offset=idx)
        candidate_profile_created += int(created_prof)
        candidate_profile_updated += int(not created_prof)

    metrics["users_recruiter_created"] = recruiter_created
    metrics["users_recruiter_updated"] = recruiter_updated
    metrics["users_candidate_created"] = candidate_created
    metrics["users_candidate_updated"] = candidate_updated
    metrics["recruiter_profiles_created"] = recruiter_profile_created
    metrics["recruiter_profiles_updated"] = recruiter_profile_updated
    metrics["candidate_profiles_created"] = candidate_profile_created
    metrics["candidate_profiles_updated"] = candidate_profile_updated


def _seed_jobs_and_resumes(session: Session, dataset: dict[str, Any], metrics: dict[str, Any]) -> None:
    jobs_created = jobs_updated = resumes_created = resumes_updated = 0
    for job in dataset["jobs"]:
        row = session.execute(select(JobPost).where(JobPost.job_id == job["job_id"])).scalar_one_or_none()
        published_at = datetime(2026, 5, 17, tzinfo=timezone.utc) + timedelta(minutes=job["job_id"] - JOB_ID_START)
        if row is None:
            row = JobPost(
                job_id=job["job_id"],
                organization_id=ORG_ID_START + ((job["job_id"] - JOB_ID_START) // 5),
                recruiter_user_id=RECRUITER_USER_ID_START + (job["job_id"] - JOB_ID_START),
                title=job["title"],
                requirement=job["requirement"],
                skills=job["skills"],
                location=job["location"],
                job_type=job["job_type"],
                seniority=job["seniority"],
                education=job["education"],
                required_certifications=job["required_certifications"],
                status="published",
                published_at=published_at,
            )
            session.add(row)
            jobs_created += 1
        else:
            row.organization_id = ORG_ID_START + ((job["job_id"] - JOB_ID_START) // 5)
            row.recruiter_user_id = RECRUITER_USER_ID_START + (job["job_id"] - JOB_ID_START)
            row.title = job["title"]
            row.requirement = job["requirement"]
            row.skills = job["skills"]
            row.location = job["location"]
            row.job_type = job["job_type"]
            row.seniority = job["seniority"]
            row.education = job["education"]
            row.required_certifications = job["required_certifications"]
            row.status = "published"
            row.published_at = published_at
            jobs_updated += 1

    for resume in dataset["resumes"]:
        row = session.execute(select(CandidateResume).where(CandidateResume.resume_id == resume["resume_id"])).scalar_one_or_none()
        if row is None:
            row = CandidateResume(
                resume_id=resume["resume_id"],
                candidate_user_id=resume["candidate_user_id"],
                title=resume["title"],
                summary=resume["summary"],
                experience=resume["experience"],
                skills=resume["skills"],
                location=resume["location"],
                job_type=resume["job_type"],
                seniority=resume["seniority"],
                education=resume["education"],
                certifications=resume["certifications"],
                is_primary=resume["is_primary"],
                status="active",
            )
            session.add(row)
            resumes_created += 1
        else:
            row.candidate_user_id = resume["candidate_user_id"]
            row.title = resume["title"]
            row.summary = resume["summary"]
            row.experience = resume["experience"]
            row.skills = resume["skills"]
            row.location = resume["location"]
            row.job_type = resume["job_type"]
            row.seniority = resume["seniority"]
            row.education = resume["education"]
            row.certifications = resume["certifications"]
            row.is_primary = resume["is_primary"]
            row.status = "active"
            resumes_updated += 1

    metrics["jobs_created"] = jobs_created
    metrics["jobs_updated"] = jobs_updated
    metrics["resumes_created"] = resumes_created
    metrics["resumes_updated"] = resumes_updated


def _reset_slice6d_data(session: Session, metrics: dict[str, Any]) -> None:
    job_ids = list(range(JOB_ID_START, JOB_ID_START + JOB_COUNT))
    resume_ids = list(range(RESUME_ID_START, RESUME_ID_START + RESUME_COUNT))
    candidate_user_ids = list(range(CANDIDATE_USER_ID_START, CANDIDATE_USER_ID_START + RESUME_COUNT))
    recruiter_user_ids = list(range(RECRUITER_USER_ID_START, RECRUITER_USER_ID_START + JOB_COUNT))
    all_user_ids = candidate_user_ids + recruiter_user_ids + [ADMIN_USER_ID]
    org_ids = list(range(ORG_ID_START, ORG_ID_START + ORG_COUNT))

    app_ids = list(
        session.execute(
            select(Application.application_id).where(
                Application.job_id.in_(job_ids) | Application.resume_id.in_(resume_ids) | Application.candidate_user_id.in_(candidate_user_ids)
            )
        ).scalars()
    )
    if app_ids:
        metrics["application_events_deleted"] = session.execute(
            delete(ApplicationEvent).where(ApplicationEvent.application_id.in_(app_ids))
        ).rowcount or 0
    metrics["invites_deleted"] = session.execute(
        delete(RecruiterInvite).where(
            RecruiterInvite.job_id.in_(job_ids)
            | RecruiterInvite.resume_id.in_(resume_ids)
            | RecruiterInvite.candidate_user_id.in_(candidate_user_ids)
            | RecruiterInvite.recruiter_user_id.in_(recruiter_user_ids)
        )
    ).rowcount or 0
    metrics["applications_deleted"] = session.execute(
        delete(Application).where(
            Application.job_id.in_(job_ids) | Application.resume_id.in_(resume_ids) | Application.candidate_user_id.in_(candidate_user_ids)
        )
    ).rowcount or 0
    metrics["resume_embeddings_deleted"] = session.execute(
        delete(CandidateResumeEmbedding).where(CandidateResumeEmbedding.resume_id.in_(resume_ids))
    ).rowcount or 0
    metrics["job_embeddings_deleted"] = session.execute(
        delete(JobPostEmbedding).where(JobPostEmbedding.job_id.in_(job_ids))
    ).rowcount or 0
    metrics["resumes_deleted"] = session.execute(
        delete(CandidateResume).where(CandidateResume.resume_id.in_(resume_ids))
    ).rowcount or 0
    metrics["jobs_deleted"] = session.execute(delete(JobPost).where(JobPost.job_id.in_(job_ids))).rowcount or 0
    metrics["candidate_profiles_deleted"] = session.execute(
        delete(CandidateProfile).where(CandidateProfile.user_id.in_(candidate_user_ids))
    ).rowcount or 0
    metrics["recruiter_profiles_deleted"] = session.execute(
        delete(RecruiterProfile).where(RecruiterProfile.user_id.in_(recruiter_user_ids))
    ).rowcount or 0
    metrics["users_deleted"] = session.execute(delete(User).where(User.user_id.in_(all_user_ids))).rowcount or 0
    metrics["organizations_deleted"] = session.execute(
        delete(Organization).where(Organization.organization_id.in_(org_ids))
    ).rowcount or 0


def _upsert_admin(session: Session) -> None:
    row = session.execute(select(User).where(User.user_id == ADMIN_USER_ID)).scalar_one_or_none()
    if row is None:
        session.add(
            User(
                user_id=ADMIN_USER_ID,
                email="seed+6d-admin@example.local",
                password_hash=hash_password("SeedPass123!"),
                role="admin",
                status="active",
            )
        )
        return
    row.email = "seed+6d-admin@example.local"
    row.password_hash = hash_password("SeedPass123!")
    row.role = "admin"
    row.status = "active"


def _upsert_organizations(session: Session) -> None:
    # Always ensure independent exists at canonical slug.
    independent = session.execute(select(Organization).where(Organization.slug == BOOTSTRAP_ORG_SLUG)).scalar_one_or_none()
    if independent is None:
        session.add(
            Organization(
                organization_id=INDEPENDENT_ORG_ID,
                name="Independent",
                slug=BOOTSTRAP_ORG_SLUG,
                about="Shared profile bucket for independent/freelance recruiters.",
            )
        )

    for idx in range(ORG_COUNT):
        org_id = ORG_ID_START + idx
        slug = f"seed-6d-batch-{idx + 1:02d}"
        row = session.execute(select(Organization).where(Organization.organization_id == org_id)).scalar_one_or_none()
        if row is None:
            session.add(
                Organization(
                    organization_id=org_id,
                    name=f"{SEED_PREFIX} Org Batch {idx + 1:02d}",
                    slug=slug,
                    about=f"{SEED_PREFIX} broad dataset organization for batch {idx + 1:02d}",
                )
            )
        else:
            row.name = f"{SEED_PREFIX} Org Batch {idx + 1:02d}"
            row.slug = slug
            row.about = f"{SEED_PREFIX} broad dataset organization for batch {idx + 1:02d}"


def _upsert_user(session: Session, *, user_id: int, email: str, role: str, status: str) -> bool:
    row = session.execute(select(User).where(User.user_id == user_id)).scalar_one_or_none()
    if row is None:
        session.add(
            User(
                user_id=user_id,
                email=email,
                password_hash=hash_password("SeedPass123!"),
                role=role,
                status=status,
            )
        )
        return True
    row.email = email
    row.password_hash = hash_password("SeedPass123!")
    row.role = role
    row.status = status
    return False


def _upsert_candidate_profile(session: Session, *, user_id: int, offset: int) -> bool:
    row = session.execute(select(CandidateProfile).where(CandidateProfile.user_id == user_id)).scalar_one_or_none()
    location = LOCATIONS[offset % len(LOCATIONS)]
    payload = {
        "full_name": f"{SEED_PREFIX} Candidate {offset + 1:03d}",
        "phone": f"09{(offset + 10000000) % 100000000:08d}",
        "current_location": location,
        "total_experience_years": offset % 11,
        "headline": f"{SEED_PREFIX} Candidate headline {offset + 1:03d}",
    }
    if row is None:
        session.add(CandidateProfile(user_id=user_id, **payload))
        return True
    for key, value in payload.items():
        setattr(row, key, value)
    return False


def _upsert_recruiter_profile(session: Session, *, user_id: int, organization_id: int) -> bool:
    row = session.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == user_id)).scalar_one_or_none()
    payload = {
        "organization_id": organization_id,
        "full_name": f"{SEED_PREFIX} Recruiter {user_id}",
        "title": "Technical Recruiter",
        "phone": f"09{(user_id + 10000000) % 100000000:08d}",
    }
    if row is None:
        session.add(RecruiterProfile(user_id=user_id, **payload))
        return True
    for key, value in payload.items():
        setattr(row, key, value)
    return False


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.12f}" for v in values) + "]"


def _normalize_terms(items: list[str]) -> list[str]:
    out: list[str] = []
    seen = set()
    for raw in items:
        token = " ".join(raw.strip().lower().split())
        if not token or token in seen:
            continue
        out.append(token)
        seen.add(token)
    return out


def _skill_pool(family: str) -> list[str]:
    base = ["communication", "problem solving"]
    mapping = {
        "backend-platform": ["python", "fastapi", "postgresql", "docker", "kubernetes", "microservices"],
        "frontend-web": ["typescript", "react", "css", "html", "testing library", "vite"],
        "data-ai": ["python", "sql", "machine learning", "pandas", "feature engineering", "model serving"],
        "product-ba": ["requirements analysis", "stakeholder management", "roadmapping", "user research", "backlog grooming", "analytics"],
        "sales-marketing": ["lead generation", "crm", "campaign planning", "copywriting", "seo", "customer outreach"],
        "finance-hr-admin": ["financial reporting", "account reconciliation", "payroll", "compliance", "excel", "hr operations"],
        "design-content": ["figma", "interaction design", "content strategy", "visual hierarchy", "prototype testing", "accessibility"],
        "ops-logistics": ["inventory planning", "vendor management", "scheduling", "process optimization", "sla tracking", "incident handling"],
    }
    return _normalize_terms(mapping.get(family, []) + base)


def _lower_education(education: str) -> str:
    idx = EDUCATIONS.index(education)
    return EDUCATIONS[max(0, idx - 1)]


def _change_job_type(job_type: str) -> str:
    if job_type == "remote":
        return "fulltime"
    return "remote" if job_type != "remote" else "parttime"


def _change_seniority(seniority: str) -> str:
    idx = SENIORITIES.index(seniority)
    return SENIORITIES[idx - 1] if idx > 0 else SENIORITIES[idx + 1]


def _different_location(location: str) -> str:
    for value in LOCATIONS:
        if value != location:
            return value
    return location


def _make_resume_payload(
    *,
    job: dict[str, Any],
    resume_id: int,
    candidate_user_id: int,
    title: str,
    summary: str,
    experience: str,
    skills: list[str],
    location: str,
    job_type: str,
    seniority: str,
    education: str,
    certifications: list[str],
) -> dict[str, Any]:
    return {
        "resume_id": resume_id,
        "candidate_user_id": candidate_user_id,
        "title": title,
        "summary": summary,
        "experience": experience,
        "skills": _normalize_terms(skills),
        "location": location,
        "job_type": job_type,
        "seniority": seniority,
        "education": education,
        "certifications": _normalize_terms(certifications),
        "is_primary": True,
        "status": "active",
    }


def _case_meta(*, job: dict[str, Any], resume_id: int, design_label: str, case_tags: list[str]) -> dict[str, Any]:
    return {
        "job_id": job["job_id"],
        "resume_id": resume_id,
        "design_label": design_label,
        "batch_id": job["batch_id"],
        "industry_group": job["industry_group"],
        "designed_for_job_id": job["job_id"],
        "case_tags": case_tags,
    }


def _make_strong_resume(*, rng: random.Random, job: dict[str, Any], resume_id: int, candidate_user_id: int, **_: Any) -> dict[str, Any]:
    loc = _different_location(job["location"]) if job["job_type"] == "remote" else job["location"]
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} Strong {job['family']} {resume_id}",
        summary=f"Strong fit for {job['family']} responsibilities with direct domain impact.",
        experience=f"Delivered core {job['family']} roadmap with measurable business outcomes and mentoring.",
        skills=job["skills"][:5] + ["delivery excellence"],
        location=loc,
        job_type=job["job_type"],
        seniority=job["seniority"],
        education=job["education"],
        certifications=job["required_certifications"],
    )
    return {"resume": payload, "meta": _case_meta(job=job, resume_id=resume_id, design_label="strong_pass", case_tags=["strong", "pass"])}


def _make_good_resume(*, rng: random.Random, job: dict[str, Any], resume_id: int, candidate_user_id: int, **_: Any) -> dict[str, Any]:
    loc = _different_location(job["location"]) if job["job_type"] == "remote" else job["location"]
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} Good {job['family']} {resume_id}",
        summary=f"Good fit for {job['family']} with moderate overlap on requirements.",
        experience=f"Handled several {job['family']} initiatives and cross-team deliveries.",
        skills=job["skills"][:3] + ["coordination", "reporting"],
        location=loc,
        job_type=job["job_type"],
        seniority=job["seniority"],
        education=job["education"],
        certifications=job["required_certifications"][:1],
    )
    return {"resume": payload, "meta": _case_meta(job=job, resume_id=resume_id, design_label="good_pass", case_tags=["good", "pass"])}


def _make_title_match_low_skill_resume(*, rng: random.Random, job: dict[str, Any], resume_id: int, candidate_user_id: int, **_: Any) -> dict[str, Any]:
    loc = _different_location(job["location"]) if job["job_type"] == "remote" else job["location"]
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} {job['title']} adjacent profile",
        summary=f"Title seems similar but domain execution for {job['family']} is weak.",
        experience="Mostly adjacent operations and support tasks with limited core technical depth.",
        skills=["documentation", "coordination", "ticket triage"],
        location=loc,
        job_type=job["job_type"],
        seniority=job["seniority"],
        education=job["education"],
        certifications=job["required_certifications"][:1],
    )
    return {
        "resume": payload,
        "meta": _case_meta(
            job=job, resume_id=resume_id, design_label="title_match_low_skill", case_tags=["pass", "title_trap", "low_skill_overlap"]
        ),
    }


def _make_skill_match_hard_filter_fail_resume(
    *,
    rng: random.Random,
    job: dict[str, Any],
    resume_id: int,
    candidate_user_id: int,
    fail_hard_mode: str,
    **_: Any,
) -> dict[str, Any]:
    location = job["location"]
    job_type = job["job_type"]
    seniority = job["seniority"]
    if fail_hard_mode == "location":
        if job_type == "remote":
            job_type = "fulltime"
        else:
            location = _different_location(job["location"])
    elif fail_hard_mode == "job_type":
        job_type = _change_job_type(job["job_type"])
    else:
        seniority = _change_seniority(job["seniority"])
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} FilterFail {job['family']} {resume_id}",
        summary="Skill set appears close but one hard-filter dimension intentionally fails.",
        experience=f"Hands-on work across {job['family']} stack with similar tools.",
        skills=job["skills"][:5],
        location=location,
        job_type=job_type,
        seniority=seniority,
        education=job["education"],
        certifications=job["required_certifications"][:1],
    )
    return {
        "resume": payload,
        "meta": _case_meta(
            job=job,
            resume_id=resume_id,
            design_label="skill_match_hard_filter_fail",
            case_tags=["hard_fail", f"fail_{fail_hard_mode}", "single_cause"],
        ),
    }


def _make_education_or_cert_fail_resume(
    *,
    rng: random.Random,
    job: dict[str, Any],
    resume_id: int,
    candidate_user_id: int,
    fail_edu_or_cert_mode: str,
    **_: Any,
) -> dict[str, Any]:
    education = job["education"]
    certifications = job["required_certifications"][:]
    if fail_edu_or_cert_mode == "education":
        education = _lower_education(job["education"])
    else:
        if certifications:
            certifications = certifications[:-1]
        else:
            certifications = []
    loc = _different_location(job["location"]) if job["job_type"] == "remote" else job["location"]
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} EduCertFail {job['family']} {resume_id}",
        summary="High structural fit but intentionally fails education or certification.",
        experience=f"Delivery experience in {job['family']} scope with measurable outcomes.",
        skills=job["skills"][:4] + ["teamwork"],
        location=loc,
        job_type=job["job_type"],
        seniority=job["seniority"],
        education=education,
        certifications=certifications,
    )
    mode_tag = "fail_education" if fail_edu_or_cert_mode == "education" else "fail_certification"
    return {
        "resume": payload,
        "meta": _case_meta(
            job=job,
            resume_id=resume_id,
            design_label="education_or_cert_fail",
            case_tags=["hard_fail", mode_tag, "single_cause"],
        ),
    }


def _make_noisy_resume(*, rng: random.Random, job: dict[str, Any], resume_id: int, candidate_user_id: int, **_: Any) -> dict[str, Any]:
    loc = _different_location(job["location"]) if job["job_type"] == "remote" else job["location"]
    payload = _make_resume_payload(
        job=job,
        resume_id=resume_id,
        candidate_user_id=candidate_user_id,
        title=f"{SEED_PREFIX} Noisy {job['family']} {resume_id}",
        summary=f"Passes hard filters for {job['family']} but only weak topical overlap.",
        experience="General execution exposure with limited depth in the target domain.",
        skills=["coordination", "reporting", "operations support"],
        location=loc,
        job_type=job["job_type"],
        seniority=job["seniority"],
        education=job["education"],
        certifications=job["required_certifications"][:1],
    )
    return {"resume": payload, "meta": _case_meta(job=job, resume_id=resume_id, design_label="noisy_pass", case_tags=["pass", "noisy"])}


def dataset_json(dataset: dict[str, Any]) -> str:
    return json.dumps(dataset, ensure_ascii=True, indent=2, sort_keys=True)
