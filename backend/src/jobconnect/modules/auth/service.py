from __future__ import annotations

import psycopg
from fastapi import Response

from jobconnect.modules.api.shared import business_error, create_access_token, hash_password, verify_password
from jobconnect.modules.auth.schemas import AuthResponse, LoginRequest, RegisterRequest, UserSummary


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def user_summary(row: tuple) -> UserSummary:
    return UserSummary(
        user_id=row[0],
        email=row[1],
        role=row[2],
        status=row[3],
        created_at=row[4].isoformat() if row[4] is not None and hasattr(row[4], "isoformat") else row[4],
    )


def register(request: RegisterRequest) -> AuthResponse:
    with _api().get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, role)
                VALUES (%s, %s, %s)
                RETURNING user_id, email, role, status, created_at
                """,
                (request.email.lower(), hash_password(request.password), request.role),
            )
            row = cur.fetchone()
        except psycopg.errors.UniqueViolation as exc:
            raise business_error(409, "duplicate_email", "Email already exists.") from exc
    user = user_summary(row)
    token, expires_in = create_access_token(user.user_id, user.role)
    return AuthResponse(access_token=token, expires_in=expires_in, user=user)


def login(request: LoginRequest) -> AuthResponse:
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, email, role, status, created_at, password_hash FROM users WHERE email = %s",
            (request.email.lower(),),
        )
        row = cur.fetchone()
    if row is None or not verify_password(request.password, row[5]):
        raise business_error(401, "invalid_credentials", "Invalid email or password.")
    if row[3] == "disabled":
        raise business_error(403, "disabled_user", "Disabled users cannot login.")
    user = user_summary(row[:5])
    token, expires_in = create_access_token(user.user_id, user.role)
    return AuthResponse(access_token=token, expires_in=expires_in, user=user)


def logout() -> Response:
    return Response(status_code=204)
