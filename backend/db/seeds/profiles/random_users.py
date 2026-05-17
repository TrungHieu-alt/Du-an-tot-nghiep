from __future__ import annotations

import random
import string
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.seeds.models import User
from jobconnect.modules.api.shared import hash_password

ROLES = {"candidate", "recruiter", "admin"}
STATUSES = {"active", "invited", "disabled"}


@dataclass(frozen=True)
class RandomUserSeedConfig:
    count: int
    role: str
    status: str
    email_prefix: str
    email_domain: str
    default_password: str
    seed: int | None = None


def run_random_user_seed(session: Session, config: RandomUserSeedConfig) -> dict[str, Any]:
    if config.role not in ROLES:
        raise ValueError(f"Unsupported role '{config.role}'. Allowed: {sorted(ROLES)}")
    if config.status not in STATUSES:
        raise ValueError(f"Unsupported status '{config.status}'. Allowed: {sorted(STATUSES)}")
    if config.count <= 0:
        raise ValueError("--count must be greater than 0.")

    rng = random.Random(config.seed)
    created = 0
    skipped = 0

    for index in range(config.count):
        local_part = _random_local_part(rng, config.email_prefix, index)
        email = f"{local_part}@{config.email_domain}"

        existing = session.execute(select(User.user_id).where(User.email == email)).scalar_one_or_none()
        if existing is not None:
            skipped += 1
            continue

        row = User(
            email=email,
            password_hash=hash_password(config.default_password),
            role=config.role,
            status=config.status,
        )
        session.add(row)
        created += 1

    session.flush()
    return {
        "requested": config.count,
        "created": created,
        "skipped_existing_email": skipped,
        "role": config.role,
        "status": config.status,
        "email_prefix": config.email_prefix,
        "email_domain": config.email_domain,
        "seed": config.seed,
    }


def _random_local_part(rng: random.Random, email_prefix: str, index: int) -> str:
    suffix = "".join(rng.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{email_prefix}{index:06d}-{suffix}"
