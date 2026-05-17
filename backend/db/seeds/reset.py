from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db.seeds.models import (
    BOOTSTRAP_ORG_SLUG,
    SEED_EMAIL_DOMAIN,
    SEED_EMAIL_PREFIX,
    SEED_ORG_SLUG_PREFIX,
    SEED_TITLE_PREFIX,
    Application,
    ApplicationEvent,
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

TARGETS = {"all", "jobs", "resumes", "users", "organizations"}


def reset_seed_data(session: Session, target: str, with_related: bool = False) -> dict[str, int]:
    if target not in TARGETS:
        allowed = ", ".join(sorted(TARGETS))
        raise ValueError(f"Unsupported target '{target}'. Allowed targets: {allowed}")

    metrics: dict[str, int] = {}

    if target == "all":
        _merge(metrics, _reset_jobs(session))
        _merge(metrics, _reset_resumes(session))
        _merge(metrics, _reset_users(session))
        _merge(metrics, _reset_organizations(session))
        return metrics

    if target == "jobs":
        _merge(metrics, _reset_jobs(session))
        return metrics

    if target == "resumes":
        _merge(metrics, _reset_resumes(session))
        return metrics

    if target == "users":
        if with_related:
            _merge(metrics, _reset_jobs(session))
            _merge(metrics, _reset_resumes(session))
        _merge(metrics, _reset_users(session))
        return metrics

    if target == "organizations":
        if with_related:
            _merge(metrics, _reset_jobs(session))
            _merge(metrics, _reset_users(session))
        _merge(metrics, _reset_organizations(session))
        return metrics

    return metrics


def _reset_jobs(session: Session) -> dict[str, int]:
    metrics: dict[str, int] = {}
    seed_user_ids = _seed_user_ids(session)
    if not seed_user_ids:
        return metrics

    job_ids = _seed_job_ids(session, seed_user_ids)
    if not job_ids:
        return metrics

    application_ids = list(
        session.execute(select(Application.application_id).where(Application.job_id.in_(job_ids))).scalars()
    )

    if application_ids:
        metrics["application_events_deleted"] = session.execute(
            delete(ApplicationEvent).where(ApplicationEvent.application_id.in_(application_ids))
        ).rowcount or 0

    metrics["invites_deleted"] = session.execute(delete(RecruiterInvite).where(RecruiterInvite.job_id.in_(job_ids))).rowcount or 0
    metrics["applications_deleted"] = session.execute(delete(Application).where(Application.job_id.in_(job_ids))).rowcount or 0
    metrics["job_embeddings_deleted"] = session.execute(delete(JobPostEmbedding).where(JobPostEmbedding.job_id.in_(job_ids))).rowcount or 0
    metrics["jobs_deleted"] = session.execute(delete(JobPost).where(JobPost.job_id.in_(job_ids))).rowcount or 0
    return _prune(metrics)


def _reset_resumes(session: Session) -> dict[str, int]:
    metrics: dict[str, int] = {}
    seed_user_ids = _seed_user_ids(session)
    if not seed_user_ids:
        return metrics

    resume_ids = _seed_resume_ids(session, seed_user_ids)
    if not resume_ids:
        return metrics

    application_ids = list(
        session.execute(select(Application.application_id).where(Application.resume_id.in_(resume_ids))).scalars()
    )

    if application_ids:
        metrics["application_events_deleted"] = session.execute(
            delete(ApplicationEvent).where(ApplicationEvent.application_id.in_(application_ids))
        ).rowcount or 0

    metrics["invites_deleted"] = session.execute(
        delete(RecruiterInvite).where(RecruiterInvite.resume_id.in_(resume_ids))
    ).rowcount or 0
    metrics["applications_deleted"] = session.execute(
        delete(Application).where(Application.resume_id.in_(resume_ids))
    ).rowcount or 0
    metrics["resume_embeddings_deleted"] = session.execute(
        delete(CandidateResumeEmbedding).where(CandidateResumeEmbedding.resume_id.in_(resume_ids))
    ).rowcount or 0
    metrics["resumes_deleted"] = session.execute(delete(CandidateResume).where(CandidateResume.resume_id.in_(resume_ids))).rowcount or 0
    return _prune(metrics)


def _reset_users(session: Session) -> dict[str, int]:
    metrics: dict[str, int] = {}
    user_ids = _seed_user_ids(session)
    if not user_ids:
        return metrics

    metrics["invites_deleted_by_candidate"] = session.execute(
        delete(RecruiterInvite).where(RecruiterInvite.candidate_user_id.in_(user_ids))
    ).rowcount or 0
    metrics["invites_deleted_by_recruiter"] = session.execute(
        delete(RecruiterInvite).where(RecruiterInvite.recruiter_user_id.in_(user_ids))
    ).rowcount or 0

    application_ids = list(
        session.execute(select(Application.application_id).where(Application.candidate_user_id.in_(user_ids))).scalars()
    )
    if application_ids:
        metrics["application_events_deleted"] = session.execute(
            delete(ApplicationEvent).where(ApplicationEvent.application_id.in_(application_ids))
        ).rowcount or 0

    metrics["applications_deleted"] = session.execute(
        delete(Application).where(Application.candidate_user_id.in_(user_ids))
    ).rowcount or 0
    metrics["candidate_profiles_deleted"] = session.execute(
        delete(CandidateProfile).where(CandidateProfile.user_id.in_(user_ids))
    ).rowcount or 0
    metrics["recruiter_profiles_deleted"] = session.execute(
        delete(RecruiterProfile).where(RecruiterProfile.user_id.in_(user_ids))
    ).rowcount or 0
    metrics["users_deleted"] = session.execute(delete(User).where(User.user_id.in_(user_ids))).rowcount or 0
    return _prune(metrics)


def _reset_organizations(session: Session) -> dict[str, int]:
    metrics: dict[str, int] = {}

    org_ids = list(
        session.execute(
            select(Organization.organization_id).where(
                Organization.slug.like(f"{SEED_ORG_SLUG_PREFIX}%"),
                Organization.slug != BOOTSTRAP_ORG_SLUG,
            )
        ).scalars()
    )
    if not org_ids:
        return metrics

    profile_org_ids = list(
        session.execute(
            select(RecruiterProfile.organization_id).where(RecruiterProfile.organization_id.in_(org_ids))
        ).scalars()
    )
    if profile_org_ids:
        metrics["recruiter_profiles_deleted"] = session.execute(
            delete(RecruiterProfile).where(RecruiterProfile.organization_id.in_(profile_org_ids))
        ).rowcount or 0

    metrics["organizations_deleted"] = session.execute(
        delete(Organization).where(Organization.organization_id.in_(org_ids))
    ).rowcount or 0
    return _prune(metrics)


def _seed_user_ids(session: Session) -> list[int]:
    return list(
        session.execute(
            select(User.user_id).where(
                User.email.like(f"{SEED_EMAIL_PREFIX}%{SEED_EMAIL_DOMAIN}"),
            )
        ).scalars()
    )


def _seed_job_ids(session: Session, seed_user_ids: list[int]) -> list[int]:
    return list(
        session.execute(
            select(JobPost.job_id).where(
                JobPost.recruiter_user_id.in_(seed_user_ids),
                JobPost.title.like(f"{SEED_TITLE_PREFIX}%"),
            )
        ).scalars()
    )


def _seed_resume_ids(session: Session, seed_user_ids: list[int]) -> list[int]:
    return list(
        session.execute(
            select(CandidateResume.resume_id).where(
                CandidateResume.candidate_user_id.in_(seed_user_ids),
                CandidateResume.title.like(f"{SEED_TITLE_PREFIX}%"),
            )
        ).scalars()
    )


def _merge(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value


def _prune(metrics: dict[str, int]) -> dict[str, int]:
    return {k: v for k, v in metrics.items() if v > 0}
