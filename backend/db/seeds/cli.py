from __future__ import annotations

import argparse
import json
from typing import Any

from db.seeds.profiles.demo import run_demo_seed
from db.seeds.profiles.random_profiles import RandomProfileSeedConfig, run_random_profile_seed
from db.seeds.profiles.random_users import RandomUserSeedConfig, run_random_user_seed
from db.seeds.reset import TARGETS, reset_seed_data
from db.seeds.session import create_seed_engine, create_session_factory
from db.seeds.slice6d import (
    Slice6DConfig,
    backfill_embeddings_6d,
    generate_dataset,
    seed_broad_6d,
    validate_postseed_db,
    validate_preseed_dataset,
)

PROFILES = {"demo"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Seed/reset database data using SQLAlchemy ORM tooling.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    seed_parser = subparsers.add_parser("seed", help="Apply a seed profile.")
    _add_profile_args(seed_parser, include_target=True)

    reset_parser = subparsers.add_parser("reset", help="Reset seed records for a target scope.")
    _add_reset_args(reset_parser)

    reseed_parser = subparsers.add_parser("reseed", help="Reset a target scope, then apply a seed profile.")
    _add_profile_args(reseed_parser, include_target=False)
    _add_reset_args(reseed_parser)

    dry_run_parser = subparsers.add_parser("dry-run", help="Run seed/reset/reseed without committing.")
    dry_run_parser.add_argument("--mode", choices=["seed", "reset", "reseed"], default="seed")
    _add_profile_args(dry_run_parser, include_target=False)
    _add_reset_args(dry_run_parser)

    random_users_parser = subparsers.add_parser(
        "seed-random-users",
        help="Create random user rows for quick data seeding.",
    )
    random_users_parser.add_argument("--count", type=int, default=100)
    random_users_parser.add_argument("--role", choices=["candidate", "recruiter", "admin"], default="candidate")
    random_users_parser.add_argument("--status", choices=["active", "invited", "disabled"], default="active")
    random_users_parser.add_argument("--email-prefix", default="seed+random-")
    random_users_parser.add_argument("--email-domain", default="example.local")
    random_users_parser.add_argument("--password", default="SeedPass123!")
    random_users_parser.add_argument("--seed", type=int, default=None)

    random_users_bundle_parser = subparsers.add_parser(
        "seed-random-users-bundle",
        help="Create candidate/recruiter/admin random users in one command.",
    )
    random_users_bundle_parser.add_argument("--candidate-count", type=int, default=240)
    random_users_bundle_parser.add_argument("--recruiter-count", type=int, default=40)
    random_users_bundle_parser.add_argument("--admin-count", type=int, default=1)
    random_users_bundle_parser.add_argument("--status", choices=["active", "invited", "disabled"], default="active")
    random_users_bundle_parser.add_argument("--email-domain", default="example.local")
    random_users_bundle_parser.add_argument("--password", default="SeedPass123!")
    random_users_bundle_parser.add_argument("--seed", type=int, default=None)
    random_users_bundle_parser.add_argument("--candidate-prefix", default="seed+random-candidate-")
    random_users_bundle_parser.add_argument("--recruiter-prefix", default="seed+random-recruiter-")
    random_users_bundle_parser.add_argument("--admin-prefix", default="seed+random-admin-")

    random_profiles_bundle_parser = subparsers.add_parser(
        "seed-random-profiles-bundle",
        help="Create/update random recruiter and candidate profiles for existing users.",
    )
    random_profiles_bundle_parser.add_argument("--status", choices=["active", "invited", "disabled"], default="active")
    random_profiles_bundle_parser.add_argument("--seed", type=int, default=None)
    random_profiles_bundle_parser.add_argument("--recruiter-org-slug", default="independent")

    seed_broad_parser = subparsers.add_parser(
        "seed-broad-6d",
        help="Reset + seed runtime-aligned broad 6D dataset (40 jobs / 240 resumes).",
    )
    seed_broad_parser.add_argument("--seed", type=int, default=20260517)

    backfill_broad_parser = subparsers.add_parser(
        "backfill-embeddings-6d",
        help="Backfill embeddings for broad 6D seeded jobs/resumes using active embedding provider.",
    )
    backfill_broad_parser.add_argument("--no-validate-post", action="store_true")

    validate_broad_parser = subparsers.add_parser(
        "validate-broad-6d",
        help="Validate broad 6D dataset in pre-seed or post-seed phase.",
    )
    validate_broad_parser.add_argument("--phase", choices=["pre", "post"], required=True)
    validate_broad_parser.add_argument("--seed", type=int, default=20260517)

    return parser


def _add_profile_args(parser: argparse.ArgumentParser, *, include_target: bool) -> None:
    parser.add_argument("--profile", choices=sorted(PROFILES), default="demo")
    if include_target:
        parser.add_argument("--target", choices=sorted(TARGETS), default="all")


def _add_reset_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", choices=sorted(TARGETS), default="all")
    parser.add_argument(
        "--with-related",
        action="store_true",
        help="When supported, also reset adjacent related entities for the selected target.",
    )


def run() -> int:
    parser = build_parser()
    args = parser.parse_args()

    effective_command = args.command
    dry_run = effective_command == "dry-run"
    if effective_command == "dry-run":
        effective_command = args.mode

    engine = create_seed_engine()
    session_factory = create_session_factory(engine)
    session = session_factory()

    payload: dict[str, Any] = {
        "command": args.command,
        "effective_command": effective_command,
        "profile": getattr(args, "profile", None),
        "target": getattr(args, "target", None),
        "with_related": bool(getattr(args, "with_related", False)),
        "dry_run": dry_run,
        "metrics": {},
    }

    try:
        if effective_command == "seed":
            _ensure_profile(args.profile)
            payload["metrics"] = run_demo_seed(session, target=args.target)
        elif effective_command == "reset":
            payload["metrics"] = reset_seed_data(session, target=args.target, with_related=args.with_related)
        elif effective_command == "reseed":
            _ensure_profile(args.profile)
            reset_metrics = reset_seed_data(session, target=args.target, with_related=args.with_related)
            seed_metrics = run_demo_seed(session, target=args.target)
            payload["metrics"] = {"reset": reset_metrics, "seed": seed_metrics}
        elif effective_command == "seed-random-users":
            payload["metrics"] = run_random_user_seed(
                session,
                RandomUserSeedConfig(
                    count=args.count,
                    role=args.role,
                    status=args.status,
                    email_prefix=args.email_prefix,
                    email_domain=args.email_domain,
                    default_password=args.password,
                    seed=args.seed,
                ),
            )
        elif effective_command == "seed-random-users-bundle":
            base_seed = args.seed
            payload["metrics"] = {
                "candidate": run_random_user_seed(
                    session,
                    RandomUserSeedConfig(
                        count=args.candidate_count,
                        role="candidate",
                        status=args.status,
                        email_prefix=args.candidate_prefix,
                        email_domain=args.email_domain,
                        default_password=args.password,
                        seed=base_seed,
                    ),
                ),
                "recruiter": run_random_user_seed(
                    session,
                    RandomUserSeedConfig(
                        count=args.recruiter_count,
                        role="recruiter",
                        status=args.status,
                        email_prefix=args.recruiter_prefix,
                        email_domain=args.email_domain,
                        default_password=args.password,
                        seed=None if base_seed is None else base_seed + 1,
                    ),
                ),
                "admin": run_random_user_seed(
                    session,
                    RandomUserSeedConfig(
                        count=args.admin_count,
                        role="admin",
                        status=args.status,
                        email_prefix=args.admin_prefix,
                        email_domain=args.email_domain,
                        default_password=args.password,
                        seed=None if base_seed is None else base_seed + 2,
                    ),
                ),
            }
        elif effective_command == "seed-random-profiles-bundle":
            payload["metrics"] = run_random_profile_seed(
                session,
                RandomProfileSeedConfig(
                    status=args.status,
                    seed=args.seed,
                    recruiter_org_slug=args.recruiter_org_slug,
                ),
            )
        elif effective_command == "seed-broad-6d":
            payload["metrics"] = seed_broad_6d(session, Slice6DConfig(seed=args.seed))
        elif effective_command == "backfill-embeddings-6d":
            payload["metrics"] = backfill_embeddings_6d(session)
            if not args.no_validate_post:
                post_errors = validate_postseed_db(session)
                payload["post_validation_errors"] = post_errors
                if post_errors:
                    raise ValueError("post-seed validation failed after embedding backfill")
        elif effective_command == "validate-broad-6d":
            if args.phase == "pre":
                dataset = generate_dataset(Slice6DConfig(seed=args.seed))
                payload["metrics"] = {
                    "phase": "pre",
                    "jobs_count": len(dataset["jobs"]),
                    "resumes_count": len(dataset["resumes"]),
                    "matrix_count": len(dataset["matrix"]),
                }
                payload["validation_errors"] = validate_preseed_dataset(dataset)
                if payload["validation_errors"]:
                    raise ValueError("pre-seed validation failed")
            else:
                payload["metrics"] = {"phase": "post"}
                payload["validation_errors"] = validate_postseed_db(session)
                if payload["validation_errors"]:
                    raise ValueError("post-seed validation failed")
        else:
            raise ValueError(f"Unsupported command: {effective_command}")

        if dry_run:
            session.rollback()
        else:
            session.commit()
    except Exception as exc:
        session.rollback()
        payload["error"] = str(exc)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 1
    finally:
        session.close()
        engine.dispose()

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _ensure_profile(profile: str) -> None:
    if profile not in PROFILES:
        allowed = ", ".join(sorted(PROFILES))
        raise ValueError(f"Unsupported profile '{profile}'. Allowed profiles: {allowed}")


if __name__ == "__main__":
    raise SystemExit(run())
