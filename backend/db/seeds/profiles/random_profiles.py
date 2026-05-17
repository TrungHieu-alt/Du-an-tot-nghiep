from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.seeds.models import BOOTSTRAP_ORG_SLUG, CandidateProfile, Organization, RecruiterProfile, User

LOCATIONS = ("ha_noi", "tp_hcm", "da_nang")
RECRUITER_TITLES = (
    "Talent Acquisition Specialist",
    "Technical Recruiter",
    "HR Business Partner",
    "Senior Recruiter",
)
HEADLINES = (
    "Backend Engineer",
    "Frontend Developer",
    "Data Analyst",
    "Product Specialist",
    "QA Engineer",
)


@dataclass(frozen=True)
class RandomProfileSeedConfig:
    status: str = "active"
    seed: int | None = None
    recruiter_org_slug: str = BOOTSTRAP_ORG_SLUG


def run_random_profile_seed(session: Session, config: RandomProfileSeedConfig) -> dict[str, Any]:
    rng = random.Random(config.seed)
    metrics: dict[str, Any] = {
        "candidate_profiles_created": 0,
        "candidate_profiles_updated": 0,
        "recruiter_profiles_created": 0,
        "recruiter_profiles_updated": 0,
        "users_scanned": 0,
    }

    recruiter_org_id = _ensure_recruiter_org(session, slug=config.recruiter_org_slug)

    users = list(
        session.execute(
            select(User).where(User.status == config.status)
        ).scalars()
    )
    metrics["users_scanned"] = len(users)

    for user in users:
        if user.role == "candidate":
            created = _upsert_candidate_profile(session, rng, user.user_id)
            key = "candidate_profiles_created" if created else "candidate_profiles_updated"
            metrics[key] += 1
        elif user.role == "recruiter":
            created = _upsert_recruiter_profile(session, rng, user.user_id, recruiter_org_id)
            key = "recruiter_profiles_created" if created else "recruiter_profiles_updated"
            metrics[key] += 1

    session.flush()
    metrics["recruiter_org_slug"] = config.recruiter_org_slug
    metrics["seed"] = config.seed
    metrics["status"] = config.status
    return metrics


def _ensure_recruiter_org(session: Session, slug: str) -> int:
    org = session.execute(select(Organization).where(Organization.slug == slug)).scalar_one_or_none()
    if org is None:
        org = Organization(
            name="Independent",
            slug=slug,
            logo_url=None,
            about="Shared profile bucket for independent/freelance recruiters.",
        )
        session.add(org)
        session.flush()
    return org.organization_id


def _upsert_candidate_profile(session: Session, rng: random.Random, user_id: int) -> bool:
    row = session.execute(select(CandidateProfile).where(CandidateProfile.user_id == user_id)).scalar_one_or_none()
    full_name = f"Candidate {user_id}"
    phone = f"09{rng.randint(10000000, 99999999)}"
    location = rng.choice(LOCATIONS)
    years = rng.randint(0, 12)
    headline = rng.choice(HEADLINES)

    if row is None:
        session.add(
            CandidateProfile(
                user_id=user_id,
                full_name=full_name,
                phone=phone,
                current_location=location,
                total_experience_years=years,
                headline=headline,
            )
        )
        return True

    row.full_name = full_name
    row.phone = phone
    row.current_location = location
    row.total_experience_years = years
    row.headline = headline
    return False


def _upsert_recruiter_profile(session: Session, rng: random.Random, user_id: int, organization_id: int) -> bool:
    row = session.execute(select(RecruiterProfile).where(RecruiterProfile.user_id == user_id)).scalar_one_or_none()
    full_name = f"Recruiter {user_id}"
    title = rng.choice(RECRUITER_TITLES)
    phone = f"09{rng.randint(10000000, 99999999)}"

    if row is None:
        session.add(
            RecruiterProfile(
                user_id=user_id,
                organization_id=organization_id,
                full_name=full_name,
                title=title,
                phone=phone,
            )
        )
        return True

    row.organization_id = organization_id
    row.full_name = full_name
    row.title = title
    row.phone = phone
    return False
