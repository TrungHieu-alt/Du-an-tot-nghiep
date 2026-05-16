from __future__ import annotations

from typing import Optional

from jobconnect.modules.api.shared import CurrentUser, business_error
from jobconnect.modules.auth.service import user_summary
from jobconnect.modules.organizations.schemas import Organization
from jobconnect.modules.users.schemas import (
    CandidateProfile,
    CandidateProfileRequest,
    MeResponse,
    RecruiterProfile,
    RecruiterProfileRequest,
)


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def me(user: CurrentUser) -> MeResponse:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, email, role, status, created_at FROM users WHERE user_id = %s",
            (user.user_id,),
        )
        summary = user_summary(cur.fetchone())
        candidate_profile: Optional[CandidateProfile] = None
        recruiter_profile: Optional[RecruiterProfile] = None
        organization: Optional[Organization] = None

        if summary.role == "candidate":
            cur.execute(
                """
                SELECT user_id, full_name, phone, current_location,
                       total_experience_years, headline
                  FROM candidate_profiles WHERE user_id = %s
                """,
                (summary.user_id,),
            )
            crow = cur.fetchone()
            if crow is not None:
                candidate_profile = CandidateProfile(
                    user_id=crow[0],
                    full_name=crow[1],
                    phone=crow[2],
                    current_location=crow[3],
                    total_experience_years=crow[4],
                    headline=crow[5],
                )
        elif summary.role == "recruiter":
            cur.execute(
                """
                SELECT rp.user_id, rp.organization_id, rp.full_name, rp.title, rp.phone,
                       o.organization_id, o.name, o.slug, o.logo_url, o.about
                  FROM recruiter_profiles rp
                  JOIN organizations o ON o.organization_id = rp.organization_id
                 WHERE rp.user_id = %s
                """,
                (summary.user_id,),
            )
            rrow = cur.fetchone()
            if rrow is not None:
                recruiter_profile = RecruiterProfile(
                    user_id=rrow[0],
                    organization_id=rrow[1],
                    full_name=rrow[2],
                    title=rrow[3],
                    phone=rrow[4],
                )
                organization = Organization(
                    organization_id=rrow[5],
                    name=rrow[6],
                    slug=rrow[7],
                    logo_url=rrow[8],
                    about=rrow[9],
                )

    return MeResponse(
        user=summary,
        candidate_profile=candidate_profile,
        recruiter_profile=recruiter_profile,
        organization=organization,
    )


def get_candidate_profile(user: CurrentUser) -> CandidateProfile:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, full_name, phone, current_location, total_experience_years, headline
            FROM candidate_profiles WHERE user_id = %s
            """,
            (user.user_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Candidate profile not found.")
    return CandidateProfile(
        user_id=row[0],
        full_name=row[1],
        phone=row[2],
        current_location=row[3],
        total_experience_years=row[4],
        headline=row[5],
    )


def put_candidate_profile(request: CandidateProfileRequest, user: CurrentUser) -> CandidateProfile:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_profiles
                (user_id, full_name, phone, current_location, total_experience_years, headline)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name = EXCLUDED.full_name,
                phone = EXCLUDED.phone,
                current_location = EXCLUDED.current_location,
                total_experience_years = EXCLUDED.total_experience_years,
                headline = EXCLUDED.headline,
                updated_at = now()
            RETURNING user_id, full_name, phone, current_location, total_experience_years, headline
            """,
            (
                user.user_id,
                request.full_name,
                request.phone,
                request.current_location,
                request.total_experience_years,
                request.headline,
            ),
        )
        row = cur.fetchone()
    return CandidateProfile(
        user_id=row[0],
        full_name=row[1],
        phone=row[2],
        current_location=row[3],
        total_experience_years=row[4],
        headline=row[5],
    )


def get_recruiter_profile(user: CurrentUser) -> RecruiterProfile:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT user_id, organization_id, full_name, title, phone
            FROM recruiter_profiles WHERE user_id = %s
            """,
            (user.user_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Recruiter profile not found.")
    return RecruiterProfile(
        user_id=row[0], organization_id=row[1], full_name=row[2], title=row[3], phone=row[4]
    )


def put_recruiter_profile(request: RecruiterProfileRequest, user: CurrentUser) -> RecruiterProfile:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM organizations WHERE organization_id = %s", (request.organization_id,))
        if cur.fetchone() is None:
            raise business_error(404, "not_found", "Organization not found.")
        cur.execute(
            """
            INSERT INTO recruiter_profiles (user_id, organization_id, full_name, title, phone)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                organization_id = EXCLUDED.organization_id,
                full_name = EXCLUDED.full_name,
                title = EXCLUDED.title,
                phone = EXCLUDED.phone,
                updated_at = now()
            RETURNING user_id, organization_id, full_name, title, phone
            """,
            (user.user_id, request.organization_id, request.full_name, request.title, request.phone),
        )
        row = cur.fetchone()
    return RecruiterProfile(user_id=row[0], organization_id=row[1], full_name=row[2], title=row[3], phone=row[4])
