"""Authentication API for the v3 JobConnect surface.

This router is intentionally independent from the V2 matching/catalog runtime:
it owns only account registration, login, and current-user lookup. Existing
Matching V2 endpoints remain unguarded until role-based access is explicitly
added later.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from matching_v2.db import get_connection


UserRole = Literal["candidate", "employer", "admin"]

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = Field(default=None, max_length=255)
    role: UserRole = "candidate"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class AuthUser(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None
    role: UserRole


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: AuthUser


def _jwt_secret_key() -> str:
    return os.getenv("JWT_SECRET_KEY", "dev-only-change-me")


def _jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")


def _jwt_expire_minutes() -> int:
    raw_value = os.getenv("JWT_EXPIRE_MINUTES", "60")
    try:
        value = int(raw_value)
    except ValueError:
        return 60
    return max(value, 1)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user: AuthUser) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=_jwt_expire_minutes())
    payload = {
        "sub": user.id,
        "email": str(user.email),
        "role": user.role,
        "exp": expires_at,
    }
    return jwt.encode(payload, _jwt_secret_key(), algorithm=_jwt_algorithm())


def _normalize_email(email: EmailStr) -> str:
    return str(email).strip().lower()


def _normalize_full_name(full_name: str | None) -> str | None:
    if full_name is None:
        return None
    stripped = full_name.strip()
    return stripped or None


def _row_to_user(row: tuple) -> AuthUser:
    return AuthUser(
        id=str(row[0]),
        email=row[1],
        full_name=row[2],
        role=row[3],
    )


def _get_user_by_email(
    conn: psycopg.Connection,
    email: str,
    include_password_hash: bool = False,
) -> tuple[AuthUser, str] | AuthUser | None:
    select_cols = "id::text, email, full_name, role"
    if include_password_hash:
        select_cols += ", password_hash"

    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {select_cols}
            FROM users
            WHERE lower(email) = lower(%s)
            """,
            (email,),
        )
        row = cur.fetchone()

    if row is None:
        return None
    user = _row_to_user(row)
    if include_password_hash:
        return user, row[4]
    return user


def _get_user_by_id(conn: psycopg.Connection, user_id: str) -> AuthUser | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text, email, full_name, role
            FROM users
            WHERE id = %s::uuid
            """,
            (user_id,),
        )
        row = cur.fetchone()
    return _row_to_user(row) if row else None


def get_db_connection():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


DbConnection = Annotated[psycopg.Connection, Depends(get_db_connection)]
BearerToken = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(token: BearerToken, conn: DbConnection) -> AuthUser:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, _jwt_secret_key(), algorithms=[_jwt_algorithm()])
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise credentials_error
        uuid.UUID(subject)
    except (JWTError, ValueError):
        raise credentials_error from None

    user = _get_user_by_id(conn, subject)
    if user is None:
        raise credentials_error
    return user


@router.post(
    "/register",
    response_model=AuthUser,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
def register(payload: RegisterRequest, conn: DbConnection) -> AuthUser:
    email = _normalize_email(payload.email)
    full_name = _normalize_full_name(payload.full_name)

    if _get_user_by_email(conn, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
                RETURNING id::text, email, full_name, role
                """,
                (email, hash_password(payload.password), full_name, payload.role),
            )
            row = cur.fetchone()
        conn.commit()
    except psycopg.errors.UniqueViolation:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        ) from None

    return _row_to_user(row)


@router.post("/login", response_model=LoginResponse, summary="Login a user")
def login(payload: LoginRequest, conn: DbConnection) -> LoginResponse:
    email = _normalize_email(payload.email)
    result = _get_user_by_email(conn, email, include_password_hash=True)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, password_hash = result
    if not verify_password(payload.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return LoginResponse(access_token=create_access_token(user), user=user)


@router.get("/me", response_model=AuthUser, summary="Get current user")
def me(current_user: Annotated[AuthUser, Depends(get_current_user)]) -> AuthUser:
    return current_user
