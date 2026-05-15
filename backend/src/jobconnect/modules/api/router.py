from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional

import psycopg
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from jobconnect.core.database import get_connection
from jobconnect.integrations.pgvector import vector_to_pg_literal
from jobconnect.modules.matching.embedding import embed_text
from jobconnect.modules.matching.filters import passes_hard_filter
from jobconnect.modules.matching.models import (
    CandidateEmbeddings,
    CandidateProfileMatch,
    JobEmbeddings,
    JobPostMatch,
)
from jobconnect.modules.matching.reasoning import build_reasoning
from jobconnect.modules.matching.scoring import (
    compute_final_score,
    compute_skills_score,
    cosine_similarity,
    exact_overlap_ratio,
    matched_skills_sorted,
)


Role = Literal["candidate", "recruiter", "admin"]
UserStatus = Literal["active", "invited", "disabled"]
Location = Literal["ha_noi", "tp_hcm", "da_nang"]
JobType = Literal["remote", "fulltime", "parttime"]
Seniority = Literal["intern", "fresher", "junior", "mid", "senior", "lead"]
Education = Literal["lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si"]
ResumeStatus = Literal["draft", "active", "archived"]
JobStatus = Literal["draft", "published", "closed"]
ApplicationStatus = Literal["submitted", "shortlisted", "rejected", "hired", "withdrawn"]
InviteStatus = Literal["pending", "accepted", "rejected"]
ParseStatus = Literal["queued", "processing", "succeeded", "failed"]
NotificationStatus = Literal["unread", "read"]


class APIModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorBody(APIModel):
    code: str
    message: str
    fields: Optional[dict[str, str]] = None
    request_id: Optional[str] = None


class ErrorEnvelope(APIModel):
    error: ErrorBody


class UserSummary(APIModel):
    user_id: int
    email: str
    role: Role
    status: UserStatus
    created_at: str


class AuthResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class RegisterRequest(APIModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    role: Role


class LoginRequest(APIModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str


class CandidateProfileRequest(APIModel):
    full_name: str = Field(min_length=1)
    phone: Optional[str] = None
    current_location: Optional[Location] = None
    total_experience_years: Optional[int] = Field(default=None, ge=0)
    headline: Optional[str] = None


class CandidateProfile(CandidateProfileRequest):
    user_id: int


class OrganizationRequest(APIModel):
    name: str = Field(min_length=1)
    slug: Optional[str] = None
    logo_url: Optional[str] = None
    about: Optional[str] = None


class Organization(OrganizationRequest):
    organization_id: int


class RecruiterProfileRequest(APIModel):
    organization_id: int
    full_name: str = Field(min_length=1)
    title: Optional[str] = None
    phone: Optional[str] = None


class RecruiterProfile(RecruiterProfileRequest):
    user_id: int


class MeResponse(APIModel):
    user: UserSummary
    candidate_profile: Optional[CandidateProfile] = None
    recruiter_profile: Optional[RecruiterProfile] = None
    organization: Optional[Organization] = None


class ResumeRequest(APIModel):
    title: str = Field(min_length=1)
    summary: str = ""
    experience: str = ""
    skills: list[str] = Field(default_factory=list)
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    certifications: list[str] = Field(default_factory=list)
    is_primary: bool = False


class ResumeSummary(APIModel):
    resume_id: int
    title: str
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    status: ResumeStatus


class ResumeDetail(ResumeSummary):
    candidate_user_id: int
    summary: str
    experience: str
    is_primary: bool


class JobRequest(APIModel):
    organization_id: int
    title: str = Field(min_length=1)
    requirement: str = ""
    skills: list[str] = Field(default_factory=list)
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    required_certifications: list[str] = Field(default_factory=list)
    expires_at: Optional[str] = None


class JobSummary(APIModel):
    job_id: int
    title: str
    location: Location
    job_type: JobType
    seniority: Seniority
    education: Education
    skills: list[str] = Field(default_factory=list)
    required_certifications: list[str] = Field(default_factory=list)
    status: JobStatus
    published_at: Optional[str] = None


class JobDetail(JobSummary):
    organization_id: int
    recruiter_user_id: int
    requirement: str
    expires_at: Optional[str] = None


class Paginated(APIModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


class SemanticSearchRequest(APIModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=20, ge=1, le=50)
    filters: dict[str, Location | JobType | Seniority] = Field(default_factory=dict)


class MatchingRequest(APIModel):
    top_k: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.7, ge=0.0, le=1.0)
    rerank: bool = False


class MatchingScoreBreakdown(APIModel):
    title_sim: float
    skills_sim: float
    req_exp_sim: float
    req_summary_sim: float
    bonus_exact_skill: float = 0.0
    penalty_missing_required: float = 0.0


class MatchingItem(APIModel):
    rank: int
    job: Optional[JobSummary] = None
    resume: Optional[ResumeSummary] = None
    final_score: float
    score_breakdown: MatchingScoreBreakdown
    exact_skill_overlap: list[str]
    hard_filter_notes: list[str]
    reasoning: str
    missing_embedding_notes: list[str]


class MatchingResponse(APIModel):
    anchor: dict[str, Any]
    items: list[MatchingItem]
    runtime: dict[str, float]


class DocumentRequest(APIModel):
    document_type: Literal["candidate_resume", "job_post"]
    original_filename: str
    mime_type: str
    file_size_bytes: int = Field(gt=0, le=10 * 1024 * 1024)
    object_key: Optional[str] = None
    file_url: Optional[str] = None
    resume_id: Optional[int] = None
    job_id: Optional[int] = None


class DocumentDetail(DocumentRequest):
    document_id: int
    owner_user_id: int
    created_at: str


class ApplicationRequest(APIModel):
    job_id: int
    resume_id: int
    note: Optional[str] = None


class ApplicationStatusRequest(APIModel):
    status: ApplicationStatus
    note: Optional[str] = None


class ApplicationDetail(APIModel):
    application_id: int
    job_id: int
    candidate_user_id: int
    resume_id: int
    status: ApplicationStatus


class InviteRequest(APIModel):
    job_id: int
    resume_id: int
    message: Optional[str] = None


class InviteRejectRequest(APIModel):
    note: Optional[str] = None


class InviteDetail(APIModel):
    invite_id: int
    job_id: int
    resume_id: int
    candidate_user_id: int
    recruiter_user_id: int
    status: InviteStatus
    message: Optional[str] = None


class NotificationDetail(APIModel):
    notification_id: int
    recipient_user_id: int
    type: str
    status: NotificationStatus
    title: str
    body: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    email: str
    role: str
    status: str


def business_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def to_error_envelope(detail: Any, status_code: int) -> dict[str, Any]:
    if isinstance(detail, dict) and "code" in detail:
        return {"error": {"code": detail["code"], "message": detail["message"]}}
    return {"error": {"code": f"http_{status_code}", "message": str(detail)}}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_json(data: dict[str, Any]) -> str:
    return _b64(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _unb64_json(data: str) -> dict[str, Any]:
    padded = data + "=" * (-len(data) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))


def _jwt_secret() -> bytes:
    return os.getenv("JWT_SECRET", "dev-only-change-me").encode("utf-8")


def _jwt_ttl_seconds() -> int:
    try:
        return max(1, int(os.getenv("JWT_TTL_SECONDS", "86400")))
    except ValueError:
        return 86400


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    rounds = 200_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), rounds)
    return f"pbkdf2_sha256${rounds}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt, digest = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), int(rounds)
        ).hex()
        return hmac.compare_digest(actual, digest)
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    """Build a signed JWT with explicit `exp`. Returns (token, expires_in_seconds)."""
    ttl = _jwt_ttl_seconds()
    now = int(time.time())
    header = _b64_json({"alg": "HS256", "typ": "JWT"})
    payload = _b64_json({"sub": user_id, "role": role, "iat": now, "exp": now + ttl})
    signed = f"{header}.{payload}".encode("ascii")
    sig = _b64(hmac.new(_jwt_secret(), signed, hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}", ttl


def parse_token(token: str) -> dict[str, Any]:
    try:
        header, payload, sig = token.split(".", 2)
        signed = f"{header}.{payload}".encode("ascii")
        expected = _b64(hmac.new(_jwt_secret(), signed, hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            raise ValueError("bad signature")
        claims = _unb64_json(payload)
    except Exception as exc:
        raise business_error(401, "invalid_token", "Missing or invalid JWT.") from exc
    exp = claims.get("exp")
    if not isinstance(exp, int) or exp <= int(time.time()):
        raise business_error(401, "expired_token", "Token has expired.")
    return claims


def current_user(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise business_error(401, "missing_token", "Missing bearer token.")
    payload = parse_token(authorization.split(" ", 1)[1])
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, email, role, status FROM users WHERE user_id = %s",
            (payload["sub"],),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(401, "invalid_token", "Missing or invalid JWT.")
    return CurrentUser(user_id=row[0], email=row[1], role=row[2], status=row[3])


def require_active(user: CurrentUser = Depends(current_user)) -> CurrentUser:
    if user.status == "disabled":
        raise business_error(403, "disabled_user", "Disabled users cannot perform this action.")
    return user


def require_roles(*roles: str):
    def _dep(user: CurrentUser = Depends(require_active)) -> CurrentUser:
        if user.role not in roles:
            raise business_error(403, "forbidden", "Role is not allowed for this endpoint.")
        return user

    return _dep


def _dt(value: Any) -> Optional[str]:
    return value.isoformat() if value is not None and hasattr(value, "isoformat") else value


def _list(value: Optional[list[str]]) -> list[str]:
    return list(value or [])


def _vec(text: str) -> str:
    return vector_to_pg_literal(embed_text(text).tolist())


def _upsert_resume_embeddings(conn: psycopg.Connection, resume_id: int, data: ResumeRequest) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_resume_embeddings
                (resume_id, emb_title, emb_skills, emb_summary, emb_experience, embedding_version)
            VALUES (%s, %s::vector, %s::vector, %s::vector, %s::vector, 'hash-v1')
            ON CONFLICT (resume_id) DO UPDATE SET
                emb_title = EXCLUDED.emb_title,
                emb_skills = EXCLUDED.emb_skills,
                emb_summary = EXCLUDED.emb_summary,
                emb_experience = EXCLUDED.emb_experience,
                embedding_version = EXCLUDED.embedding_version,
                updated_at = now()
            """,
            (
                resume_id,
                _vec(data.title),
                _vec(" ".join(data.skills)),
                _vec(data.summary),
                _vec(data.experience),
            ),
        )


def _upsert_job_embeddings(conn: psycopg.Connection, job_id: int, data: JobRequest) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO job_post_embeddings
                (job_id, emb_title, emb_skills, emb_requirement, embedding_version)
            VALUES (%s, %s::vector, %s::vector, %s::vector, 'hash-v1')
            ON CONFLICT (job_id) DO UPDATE SET
                emb_title = EXCLUDED.emb_title,
                emb_skills = EXCLUDED.emb_skills,
                emb_requirement = EXCLUDED.emb_requirement,
                embedding_version = EXCLUDED.embedding_version,
                updated_at = now()
            """,
            (job_id, _vec(data.title), _vec(" ".join(data.skills)), _vec(data.requirement)),
        )


def user_summary(row: tuple) -> UserSummary:
    return UserSummary(
        user_id=row[0],
        email=row[1],
        role=row[2],
        status=row[3],
        created_at=_dt(row[4]),
    )


def resume_summary(row: tuple) -> ResumeSummary:
    return ResumeSummary(
        resume_id=row[0],
        title=row[1],
        location=row[2],
        job_type=row[3],
        seniority=row[4],
        education=row[5],
        skills=_list(row[6]),
        certifications=_list(row[7]),
        status=row[8],
    )


def resume_detail(row: tuple) -> ResumeDetail:
    base = resume_summary((row[0], row[2], row[6], row[7], row[8], row[9], row[5], row[10], row[12]))
    return ResumeDetail(
        **base.model_dump(),
        candidate_user_id=row[1],
        summary=row[3],
        experience=row[4],
        is_primary=row[11],
    )


def job_summary(row: tuple) -> JobSummary:
    return JobSummary(
        job_id=row[0],
        title=row[1],
        location=row[2],
        job_type=row[3],
        seniority=row[4],
        education=row[5],
        skills=_list(row[6]),
        required_certifications=_list(row[7]),
        status=row[8],
        published_at=_dt(row[9]),
    )


def job_detail(row: tuple) -> JobDetail:
    base = job_summary((row[0], row[3], row[6], row[7], row[8], row[9], row[5], row[10], row[11], row[12]))
    return JobDetail(
        **base.model_dump(),
        organization_id=row[1],
        recruiter_user_id=row[2],
        requirement=row[4],
        expires_at=_dt(row[13]),
    )


RESUME_DETAIL_COLS = (
    "resume_id, candidate_user_id, title, summary, experience, skills, location, "
    "job_type, seniority, education, certifications, is_primary, status"
)
JOB_DETAIL_COLS = (
    "job_id, organization_id, recruiter_user_id, title, requirement, skills, "
    "location, job_type, seniority, education, required_certifications, status, "
    "published_at, expires_at"
)


auth_router = APIRouter(prefix="/auth", tags=["auth"])
me_router = APIRouter(tags=["me"])
candidate_router = APIRouter(prefix="/candidate", tags=["candidate"])
recruiter_router = APIRouter(prefix="/recruiter", tags=["recruiter"])
organizations_router = APIRouter(prefix="/organizations", tags=["organizations"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
documents_router = APIRouter(prefix="/documents", tags=["documents"])
matching_router = APIRouter(prefix="/matching", tags=["matching"])
applications_router = APIRouter(prefix="/applications", tags=["applications"])
invites_router = APIRouter(prefix="/invites", tags=["invites"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@auth_router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: RegisterRequest) -> AuthResponse:
    with get_connection() as conn, conn.cursor() as cur:
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


@auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest) -> AuthResponse:
    with get_connection() as conn, conn.cursor() as cur:
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


@auth_router.post("/logout", status_code=204)
def logout(_: CurrentUser = Depends(current_user)) -> Response:
    return Response(status_code=204)


@me_router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(current_user)) -> MeResponse:
    with get_connection() as conn, conn.cursor() as cur:
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


@candidate_router.get("/profile", response_model=CandidateProfile)
def get_candidate_profile(user: CurrentUser = Depends(require_roles("candidate"))):
    with get_connection() as conn, conn.cursor() as cur:
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


@candidate_router.put("/profile", response_model=CandidateProfile)
def put_candidate_profile(
    request: CandidateProfileRequest,
    user: CurrentUser = Depends(require_roles("candidate")),
):
    with get_connection() as conn, conn.cursor() as cur:
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


@organizations_router.get("", response_model=Paginated)
def list_organizations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(current_user),
):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM organizations")
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT organization_id, name, slug, logo_url, about
            FROM organizations ORDER BY organization_id ASC LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        items = [
            Organization(
                organization_id=r[0], name=r[1], slug=r[2], logo_url=r[3], about=r[4]
            )
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@organizations_router.post("", response_model=Organization, status_code=201)
def create_organization(
    request: OrganizationRequest,
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO organizations (name, slug, logo_url, about)
            VALUES (%s, %s, %s, %s)
            RETURNING organization_id, name, slug, logo_url, about
            """,
            (request.name, request.slug, request.logo_url, request.about),
        )
        row = cur.fetchone()
        _audit(cur, user.user_id, "organization_created", "organization", row[0])
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])


@organizations_router.get("/{organization_id}", response_model=Organization)
def get_organization(organization_id: int, _: CurrentUser = Depends(current_user)):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT organization_id, name, slug, logo_url, about FROM organizations WHERE organization_id = %s",
            (organization_id,),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Organization not found.")
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])


@organizations_router.patch("/{organization_id}", response_model=Organization)
def update_organization(
    organization_id: int,
    request: OrganizationRequest,
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    # Slice 2: recruiters may only update an organization they belong to.
    if user.role == "recruiter" and not _recruiter_in_organization(user.user_id, organization_id):
        # Hide existence from non-member recruiters: 404 instead of 403.
        raise business_error(404, "not_found", "Organization not found.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE organizations SET name = %s, slug = %s, logo_url = %s, about = %s, updated_at = now()
            WHERE organization_id = %s
            RETURNING organization_id, name, slug, logo_url, about
            """,
            (request.name, request.slug, request.logo_url, request.about, organization_id),
        )
        row = cur.fetchone()
        if row:
            _audit(cur, user.user_id, "organization_updated", "organization", organization_id)
    if row is None:
        raise business_error(404, "not_found", "Organization not found.")
    return Organization(organization_id=row[0], name=row[1], slug=row[2], logo_url=row[3], about=row[4])


@recruiter_router.get("/profile", response_model=RecruiterProfile)
def get_recruiter_profile(user: CurrentUser = Depends(require_roles("recruiter"))):
    with get_connection() as conn, conn.cursor() as cur:
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


@recruiter_router.put("/profile", response_model=RecruiterProfile)
def put_recruiter_profile(
    request: RecruiterProfileRequest,
    user: CurrentUser = Depends(require_roles("recruiter")),
):
    with get_connection() as conn, conn.cursor() as cur:
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


@candidate_router.get("/resumes", response_model=Paginated)
def list_resumes(
    status: Optional[ResumeStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("candidate", "admin")),
):
    where = ["candidate_user_id = %s"] if user.role == "candidate" else ["TRUE"]
    params: list[Any] = [user.user_id] if user.role == "candidate" else []
    if status:
        where.append("status = %s")
        params.append(status)
    sql_where = " AND ".join(where)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM candidate_resumes WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT resume_id, title, location, job_type, seniority, education, skills, certifications, status
            FROM candidate_resumes WHERE {sql_where}
            ORDER BY resume_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [resume_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@candidate_router.post("/resumes", response_model=ResumeDetail, status_code=201)
def create_resume(request: ResumeRequest, user: CurrentUser = Depends(require_roles("candidate"))):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO candidate_resumes
                (candidate_user_id, title, summary, experience, skills, location,
                 job_type, seniority, education, certifications, is_primary)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING """ + RESUME_DETAIL_COLS,
            (
                user.user_id,
                request.title,
                request.summary,
                request.experience,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.certifications,
                request.is_primary,
            ),
        )
        row = cur.fetchone()
        _upsert_resume_embeddings(conn, row[0], request)
    return resume_detail(row)


@candidate_router.get("/resumes/search", response_model=Paginated)
def search_resumes(
    q: Optional[str] = None,
    location: Optional[Location] = None,
    job_type: Optional[JobType] = None,
    seniority: Optional[Seniority] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    where, params = _public_resume_filters(q, location, job_type, seniority)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM candidate_resumes WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT resume_id, title, location, job_type, seniority, education, skills, certifications, status
            FROM candidate_resumes WHERE {where}
            ORDER BY resume_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [resume_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@candidate_router.post("/resumes/semantic-search", response_model=Paginated)
def semantic_search_resumes(
    request: SemanticSearchRequest,
    _: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    q_vec = _vec(request.query)
    where, params = _public_resume_filters(
        None,
        request.filters.get("location"),
        request.filters.get("job_type"),
        request.filters.get("seniority"),
    )
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT r.resume_id, r.title, r.location, r.job_type, r.seniority, r.education,
                   r.skills, r.certifications, r.status,
                   1 - (e.emb_title <=> %s::vector) AS relevance_score
            FROM candidate_resumes r
            JOIN candidate_resume_embeddings e USING (resume_id)
            WHERE {where} AND e.emb_title IS NOT NULL
            ORDER BY relevance_score DESC, r.resume_id ASC
            LIMIT %s
            """,
            (q_vec, *params, request.top_k),
        )
        items = [
            {**resume_summary(r[:9]).model_dump(), "relevance_score": max(0.0, min(1.0, float(r[9])))}
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=len(items), limit=request.top_k, offset=0)


@candidate_router.get("/resumes/{resume_id}", response_model=ResumeDetail)
def get_resume(resume_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if user.role == "candidate" and row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can read only your own resumes.")
    if user.role == "recruiter" and row[12] != "active":
        raise business_error(404, "not_found", "Resume not found.")
    return resume_detail(row)


@candidate_router.patch("/resumes/{resume_id}", response_model=ResumeDetail)
def update_resume(
    resume_id: int,
    request: ResumeRequest,
    user: CurrentUser = Depends(require_roles("candidate")),
):
    row = _get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own resumes.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE candidate_resumes SET
                title = %s, summary = %s, experience = %s, skills = %s, location = %s,
                job_type = %s, seniority = %s, education = %s, certifications = %s,
                is_primary = %s, updated_at = now()
            WHERE resume_id = %s
            RETURNING """ + RESUME_DETAIL_COLS,
            (
                request.title,
                request.summary,
                request.experience,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.certifications,
                request.is_primary,
                resume_id,
            ),
        )
        updated = cur.fetchone()
        _upsert_resume_embeddings(conn, resume_id, request)
    return resume_detail(updated)


@candidate_router.post("/resumes/{resume_id}/activate", response_model=ResumeDetail)
def activate_resume(resume_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    return _set_resume_status(resume_id, "active", user)


@candidate_router.post("/resumes/{resume_id}/archive", response_model=ResumeDetail)
def archive_resume(resume_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    return _set_resume_status(resume_id, "archived", user)


@jobs_router.get("", response_model=Paginated)
def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where, params = _visible_job_list_filter(user, status)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM job_posts WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT job_id, title, location, job_type, seniority, education, skills,
                   required_certifications, status, published_at
            FROM job_posts WHERE {where}
            ORDER BY job_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [job_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@jobs_router.post("", response_model=JobDetail, status_code=201)
def create_job(request: JobRequest, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT 1 FROM organizations WHERE organization_id = %s", (request.organization_id,))
        if cur.fetchone() is None:
            raise business_error(404, "not_found", "Organization not found.")
        cur.execute(
            """
            INSERT INTO job_posts
                (organization_id, recruiter_user_id, title, requirement, skills, location,
                 job_type, seniority, education, required_certifications, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING """ + JOB_DETAIL_COLS,
            (
                request.organization_id,
                user.user_id,
                request.title,
                request.requirement,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.required_certifications,
                request.expires_at,
            ),
        )
        row = cur.fetchone()
        _upsert_job_embeddings(conn, row[0], request)
    return job_detail(row)


@jobs_router.get("/search", response_model=Paginated)
def search_jobs(
    q: Optional[str] = None,
    location: Optional[Location] = None,
    job_type: Optional[JobType] = None,
    seniority: Optional[Seniority] = None,
    status: Optional[JobStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where, params = _visible_job_search_filter(user, q, location, job_type, seniority, status)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM job_posts WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT job_id, title, location, job_type, seniority, education, skills,
                   required_certifications, status, published_at
            FROM job_posts WHERE {where}
            ORDER BY job_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [job_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@jobs_router.post("/semantic-search", response_model=Paginated)
def semantic_search_jobs(request: SemanticSearchRequest, user: CurrentUser = Depends(require_active)):
    q_vec = _vec(request.query)
    where, params = _visible_job_search_filter(
        user,
        None,
        request.filters.get("location"),
        request.filters.get("job_type"),
        request.filters.get("seniority"),
        None,
    )
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT j.job_id, j.title, j.location, j.job_type, j.seniority, j.education,
                   j.skills, j.required_certifications, j.status, j.published_at,
                   1 - (e.emb_title <=> %s::vector) AS relevance_score
            FROM job_posts j
            JOIN job_post_embeddings e USING (job_id)
            WHERE {where} AND e.emb_title IS NOT NULL
            ORDER BY relevance_score DESC, j.job_id ASC
            LIMIT %s
            """,
            (q_vec, *params, request.top_k),
        )
        items = [
            {**job_summary(r[:10]).model_dump(), "relevance_score": max(0.0, min(1.0, float(r[10])))}
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=len(items), limit=request.top_k, offset=0)


@jobs_router.get("/{job_id}", response_model=JobDetail)
def get_job(job_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "candidate" and row[11] != "published":
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can read only your own unpublished jobs.")
    return job_detail(row)


@jobs_router.patch("/{job_id}", response_model=JobDetail)
def update_job(job_id: int, request: JobRequest, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    row = _get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own jobs.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE job_posts SET
                organization_id = %s, title = %s, requirement = %s, skills = %s,
                location = %s, job_type = %s, seniority = %s, education = %s,
                required_certifications = %s, expires_at = %s, updated_at = now()
            WHERE job_id = %s
            RETURNING """ + JOB_DETAIL_COLS,
            (
                request.organization_id,
                request.title,
                request.requirement,
                request.skills,
                request.location,
                request.job_type,
                request.seniority,
                request.education,
                request.required_certifications,
                request.expires_at,
                job_id,
            ),
        )
        updated = cur.fetchone()
        _upsert_job_embeddings(conn, job_id, request)
    return job_detail(updated)


@jobs_router.post("/{job_id}/publish", response_model=JobDetail)
def publish_job(job_id: int, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    return _set_job_status(job_id, "published", user)


@jobs_router.post("/{job_id}/close", response_model=JobDetail)
def close_job(job_id: int, user: CurrentUser = Depends(require_roles("recruiter", "admin"))):
    return _set_job_status(job_id, "closed", user)


@matching_router.post("/jobs/{job_id}/run", response_model=MatchingResponse)
def run_job_matching(
    job_id: int,
    request: MatchingRequest = Body(default_factory=MatchingRequest),
    user: CurrentUser = Depends(require_roles("recruiter", "admin")),
):
    job = _load_job(job_id)
    if job is None:
        raise business_error(404, "not_found", "Job not found.")
    # Slice 2: recruiters may only match against jobs they own.
    if user.role == "recruiter" and job["row"][2] != user.user_id:
        raise business_error(403, "forbidden", "You can match only against your own jobs.")
    if job["status"] != "published":
        raise business_error(400, "invalid_anchor", "Job anchor must be published.")
    return _run_matching("job", job_id, request)


@matching_router.post("/resumes/{resume_id}/run", response_model=MatchingResponse)
def run_resume_matching(
    resume_id: int,
    request: MatchingRequest = Body(default_factory=MatchingRequest),
    user: CurrentUser = Depends(require_roles("candidate", "admin")),
):
    resume = _load_resume(resume_id)
    if resume is None:
        raise business_error(404, "not_found", "Resume not found.")
    # Slice 2: candidates may only match against resumes they own.
    if user.role == "candidate" and resume["row"][1] != user.user_id:
        raise business_error(403, "forbidden", "You can match only against your own resumes.")
    if resume["status"] != "active":
        raise business_error(400, "invalid_anchor", "Resume anchor must be active.")
    return _run_matching("resume", resume_id, request)


@documents_router.post(
    "",
    response_model=DocumentDetail,
    status_code=201,
    description="Stores document metadata for an already-uploaded file. Accepted MIME types: application/pdf, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document. Max file size: 10 MiB.",
)
def create_document(request: DocumentRequest, user: CurrentUser = Depends(require_active)):
    if request.object_key is None and request.file_url is None:
        raise business_error(422, "missing_storage_ref", "object_key or file_url is required.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO uploaded_documents
                (owner_user_id, document_type, object_key, file_url, original_filename,
                 mime_type, file_size_bytes, resume_id, job_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING document_id, owner_user_id, document_type, object_key, file_url,
                      original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            """,
            (
                user.user_id,
                request.document_type,
                request.object_key,
                request.file_url,
                request.original_filename,
                request.mime_type,
                request.file_size_bytes,
                request.resume_id,
                request.job_id,
            ),
        )
        row = cur.fetchone()
        target_type = request.document_type
        cur.execute(
            """
            INSERT INTO parse_jobs
                (document_id, target_entity_type, resume_id, job_id, parser_version, embedding_version_requested)
            VALUES (%s, %s, %s, %s, 'external-parser-v1', 'hash-v1')
            """,
            (row[0], target_type, request.resume_id, request.job_id),
        )
    return _document_detail(row)


@documents_router.get("", response_model=Paginated)
def list_documents(
    document_type: Optional[Literal["candidate_resume", "job_post"]] = None,
    parse_status: Optional[ParseStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where = ["TRUE"] if user.role == "admin" else ["owner_user_id = %s"]
    params: list[Any] = [] if user.role == "admin" else [user.user_id]
    if document_type:
        where.append("document_type = %s")
        params.append(document_type)
    if parse_status:
        where.append("EXISTS (SELECT 1 FROM parse_jobs p WHERE p.document_id = uploaded_documents.document_id AND p.status = %s)")
        params.append(parse_status)
    sql_where = " AND ".join(where)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM uploaded_documents WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT document_id, owner_user_id, document_type, object_key, file_url,
                   original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            FROM uploaded_documents WHERE {sql_where}
            ORDER BY document_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [_document_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@documents_router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    return _document_detail(row)


@documents_router.get("/{document_id}/download-url")
def get_download_url(document_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    return {"download_url": row[4] or f"object://{row[3]}", "expires_in_seconds": 900}


@documents_router.get("/{document_id}/parse-jobs/{parse_job_id}")
def get_parse_job(document_id: int, parse_job_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                   error_code, error_message, created_at, updated_at
            FROM parse_jobs WHERE document_id = %s AND parse_job_id = %s
            """,
            (document_id, parse_job_id),
        )
        parse = cur.fetchone()
    if parse is None:
        raise business_error(404, "not_found", "Parse job not found.")
    return _parse_job_detail(parse)


@documents_router.post("/{document_id}/parse-jobs", status_code=201)
def create_parse_job(document_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parse_jobs
                (document_id, target_entity_type, resume_id, job_id, parser_version, embedding_version_requested)
            VALUES (%s, %s, %s, %s, 'external-parser-v1', 'hash-v1')
            RETURNING parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                      error_code, error_message, created_at, updated_at
            """,
            (document_id, row[2], row[8], row[9]),
        )
        parse = cur.fetchone()
    return _parse_job_detail(parse)


@applications_router.get("", response_model=Paginated)
def list_applications(
    status: Optional[ApplicationStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where, params = _application_visibility(user, status, job_id, resume_id)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM applications a JOIN job_posts j USING (job_id) WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT a.application_id, a.job_id, a.candidate_user_id, a.resume_id, a.status
            FROM applications a JOIN job_posts j USING (job_id)
            WHERE {where}
            ORDER BY a.application_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [_application_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@applications_router.post("", response_model=ApplicationDetail, status_code=201)
def create_application(request: ApplicationRequest, user: CurrentUser = Depends(require_roles("candidate"))):
    row = _create_application(request.job_id, request.resume_id, user.user_id, user.user_id, request.note)
    return _application_detail(row)


@applications_router.get("/{application_id}", response_model=ApplicationDetail)
def get_application(application_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_application_row(application_id, user)
    if row is None:
        raise business_error(404, "not_found", "Application not found.")
    return _application_detail(row)


@applications_router.post("/{application_id}/status", response_model=ApplicationDetail)
def update_application_status(
    application_id: int,
    request: ApplicationStatusRequest,
    user: CurrentUser = Depends(require_active),
):
    row = _get_application_row(application_id, user)
    if row is None:
        raise business_error(404, "not_found", "Application not found.")
    current = row[4]
    if user.role == "candidate" and request.status != "withdrawn":
        raise business_error(403, "forbidden", "Candidates can only withdraw applications.")
    if user.role == "recruiter" and request.status not in ("shortlisted", "rejected", "hired"):
        raise business_error(403, "forbidden", "Recruiters cannot set this status.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE applications SET status = %s, updated_at = now() WHERE application_id = %s RETURNING application_id, job_id, candidate_user_id, resume_id, status",
            (request.status, application_id),
        )
        updated = cur.fetchone()
        cur.execute(
            "INSERT INTO application_events (application_id, from_status, to_status, actor_user_id, note) VALUES (%s, %s, %s, %s, %s)",
            (application_id, current, request.status, user.user_id, request.note),
        )
        _notify(cur, updated[2], "application_status_changed", "Application status changed", f"Application is now {request.status}.", "application", application_id)
        _audit(cur, user.user_id, "application_status_changed", "application", application_id)
    return _application_detail(updated)


@invites_router.get("", response_model=Paginated)
def list_invites(
    status: Optional[InviteStatus] = None,
    job_id: Optional[int] = None,
    resume_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where, params = _invite_visibility(user, status, job_id, resume_id)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM recruiter_invites i JOIN job_posts j USING (job_id) WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT i.invite_id, i.job_id, i.resume_id, i.candidate_user_id, i.recruiter_user_id, i.status, i.message
            FROM recruiter_invites i JOIN job_posts j USING (job_id)
            WHERE {where}
            ORDER BY i.invite_id ASC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [_invite_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@invites_router.post("", response_model=InviteDetail, status_code=201)
def create_invite(request: InviteRequest, user: CurrentUser = Depends(require_roles("recruiter"))):
    resume = _get_resume_row(request.resume_id)
    job = _get_job_row(request.job_id)
    if resume is None or resume[12] != "active":
        raise business_error(404, "not_found", "Active resume not found.")
    if job is None or job[11] != "published":
        raise business_error(404, "not_found", "Published job not found.")
    if job[2] != user.user_id:
        raise business_error(403, "forbidden", "Recruiters can invite only for their own jobs.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO recruiter_invites
                (job_id, resume_id, candidate_user_id, recruiter_user_id, message)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message
            """,
            (request.job_id, request.resume_id, resume[1], user.user_id, request.message),
        )
        row = cur.fetchone()
        _notify(cur, resume[1], "recruiter_invite_sent", "Recruiter invite sent", "A recruiter invited you to apply.", "invite", row[0])
        _audit(cur, user.user_id, "recruiter_invite_sent", "invite", row[0])
    return _invite_detail(row)


@invites_router.get("/{invite_id}", response_model=InviteDetail)
def get_invite(invite_id: int, user: CurrentUser = Depends(require_active)):
    row = _get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    return _invite_detail(row)


@invites_router.post("/{invite_id}/accept")
def accept_invite(invite_id: int, user: CurrentUser = Depends(require_roles("candidate"))):
    row = _get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    if row[5] != "pending":
        raise business_error(409, "invalid_state", "Invite is not pending.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE recruiter_invites SET status = 'accepted', updated_at = now() WHERE invite_id = %s RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message",
            (invite_id,),
        )
        updated = cur.fetchone()
        _notify(cur, updated[4], "invite_accepted", "Invite accepted", "Candidate accepted your invite.", "invite", invite_id)
        _audit(cur, user.user_id, "invite_accepted", "invite", invite_id)
    app = _create_application(updated[1], updated[2], updated[3], user.user_id, "Accepted invite", allow_existing=True)
    return {"invite": _invite_detail(updated), "application": _application_detail(app)}


@invites_router.post("/{invite_id}/reject", response_model=InviteDetail)
def reject_invite(
    invite_id: int,
    request: InviteRejectRequest = Body(default_factory=InviteRejectRequest),
    user: CurrentUser = Depends(require_roles("candidate")),
):
    row = _get_invite_row(invite_id, user)
    if row is None:
        raise business_error(404, "not_found", "Invite not found.")
    if row[5] != "pending":
        raise business_error(409, "invalid_state", "Invite is not pending.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE recruiter_invites SET status = 'rejected', updated_at = now() WHERE invite_id = %s RETURNING invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message",
            (invite_id,),
        )
        updated = cur.fetchone()
        _notify(cur, updated[4], "invite_rejected", "Invite rejected", request.note or "Candidate rejected your invite.", "invite", invite_id)
        _audit(cur, user.user_id, "invite_rejected", "invite", invite_id)
    return _invite_detail(updated)


@notifications_router.get("", response_model=Paginated)
def list_notifications(
    status: Optional[NotificationStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_active),
):
    where = ["recipient_user_id = %s"]
    params: list[Any] = [user.user_id]
    if status:
        where.append("status = %s")
        params.append(status)
    sql_where = " AND ".join(where)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM notifications WHERE {sql_where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT notification_id, recipient_user_id, type, status, title, body, entity_type, entity_id
            FROM notifications WHERE {sql_where}
            ORDER BY notification_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [_notification_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@notifications_router.post("/{notification_id}/read", response_model=NotificationDetail)
def mark_notification_read(notification_id: int, user: CurrentUser = Depends(require_active)):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE notifications SET status = 'read', updated_at = now()
            WHERE notification_id = %s AND recipient_user_id = %s
            RETURNING notification_id, recipient_user_id, type, status, title, body, entity_type, entity_id
            """,
            (notification_id, user.user_id),
        )
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "Notification not found.")
    return _notification_detail(row)


@notifications_router.post("/read-all")
def mark_all_notifications_read(user: CurrentUser = Depends(require_active)):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE notifications SET status = 'read', updated_at = now() WHERE recipient_user_id = %s AND status = 'unread'",
            (user.user_id,),
        )
        count = cur.rowcount
    return {"updated": count}


@admin_router.get("/users", response_model=Paginated)
def admin_users(
    role: Optional[Role] = None,
    status: Optional[UserStatus] = None,
    q: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    where, params = _admin_filters(role=role, status=status, q=q)
    with get_connection() as conn, conn.cursor() as cur:
        _audit(cur, user.user_id, "admin_monitoring_access", "users", None)
        cur.execute(f"SELECT COUNT(*) FROM users WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT user_id, email, role, status, created_at FROM users WHERE {where} ORDER BY user_id ASC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [user_summary(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/users/{user_id}", response_model=UserSummary)
def admin_user_detail(user_id: int, user: CurrentUser = Depends(require_roles("admin"))):
    with get_connection() as conn, conn.cursor() as cur:
        _audit(cur, user.user_id, "admin_monitoring_access", "user", user_id)
        cur.execute("SELECT user_id, email, role, status, created_at FROM users WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    if row is None:
        raise business_error(404, "not_found", "User not found.")
    return user_summary(row)


@admin_router.get("/documents", response_model=Paginated)
def admin_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    with get_connection() as conn, conn.cursor() as cur:
        _audit(cur, user.user_id, "admin_monitoring_access", "documents", None)
        cur.execute("SELECT COUNT(*) FROM uploaded_documents")
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT document_id, owner_user_id, document_type, object_key, file_url,
                   original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            FROM uploaded_documents ORDER BY document_id DESC LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        items = [_document_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/parse-jobs", response_model=Paginated)
def admin_parse_jobs(
    status: Optional[ParseStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(require_roles("admin")),
):
    where = "status = %s" if status else "TRUE"
    params: list[Any] = [status] if status else []
    with get_connection() as conn, conn.cursor() as cur:
        _audit(cur, user.user_id, "admin_monitoring_access", "parse_jobs", None)
        cur.execute(f"SELECT COUNT(*) FROM parse_jobs WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                   error_code, error_message, created_at, updated_at
            FROM parse_jobs WHERE {where} ORDER BY parse_job_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [_parse_job_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/applications", response_model=Paginated)
def admin_applications(
    status: Optional[ApplicationStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("admin")),
):
    where = "status = %s" if status else "TRUE"
    params: list[Any] = [status] if status else []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM applications WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT application_id, job_id, candidate_user_id, resume_id, status FROM applications WHERE {where} ORDER BY application_id DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [_application_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/invites", response_model=Paginated)
def admin_invites(
    status: Optional[InviteStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("admin")),
):
    where = "status = %s" if status else "TRUE"
    params: list[Any] = [status] if status else []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM recruiter_invites WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT invite_id, job_id, resume_id, candidate_user_id, recruiter_user_id, status, message FROM recruiter_invites WHERE {where} ORDER BY invite_id DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [_invite_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/notifications", response_model=Paginated)
def admin_notifications(
    status: Optional[NotificationStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("admin")),
):
    where = "status = %s" if status else "TRUE"
    params: list[Any] = [status] if status else []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM notifications WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"SELECT notification_id, recipient_user_id, type, status, title, body, entity_type, entity_id FROM notifications WHERE {where} ORDER BY notification_id DESC LIMIT %s OFFSET %s",
            (*params, limit, offset),
        )
        items = [_notification_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/audit-logs", response_model=Paginated)
def admin_audit_logs(
    event_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: CurrentUser = Depends(require_roles("admin")),
):
    where = "event_type = %s" if event_type else "TRUE"
    params: list[Any] = [event_type] if event_type else []
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM audit_logs WHERE {where}", params)
        total = cur.fetchone()[0]
        cur.execute(
            f"""
            SELECT audit_log_id, actor_user_id, event_type, target_entity_type,
                   target_entity_id, metadata, created_at
            FROM audit_logs WHERE {where} ORDER BY audit_log_id DESC LIMIT %s OFFSET %s
            """,
            (*params, limit, offset),
        )
        items = [
            {
                "audit_log_id": r[0],
                "actor_user_id": r[1],
                "event_type": r[2],
                "target_entity_type": r[3],
                "target_entity_id": r[4],
                "metadata": r[5],
                "created_at": _dt(r[6]),
            }
            for r in cur.fetchall()
        ]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def _public_resume_filters(q: Optional[str], location: Any, job_type: Any, seniority: Any):
    where = ["status = 'active'"]
    params: list[Any] = []
    if q:
        where.append("(title ILIKE %s OR array_to_string(skills, ' ') ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if location:
        where.append("location = %s")
        params.append(location)
    if job_type:
        where.append("job_type = %s")
        params.append(job_type)
    if seniority:
        where.append("seniority = %s")
        params.append(seniority)
    return " AND ".join(where), params


def _visible_job_list_filter(user: CurrentUser, status: Optional[str]):
    if user.role == "candidate":
        where = ["status = 'published'"]
        params: list[Any] = []
    elif user.role == "recruiter":
        where = ["recruiter_user_id = %s"]
        params = [user.user_id]
    else:
        where = ["TRUE"]
        params = []
    if status:
        where.append("status = %s")
        params.append(status)
    return " AND ".join(where), params


def _visible_job_search_filter(user: CurrentUser, q: Optional[str], location: Any, job_type: Any, seniority: Any, status: Any):
    where, params = _visible_job_list_filter(user, status)
    parts = [where]
    if q:
        parts.append("(title ILIKE %s OR array_to_string(skills, ' ') ILIKE %s)")
        params.extend([f"%{q}%", f"%{q}%"])
    if location:
        parts.append("location = %s")
        params.append(location)
    if job_type:
        parts.append("job_type = %s")
        params.append(job_type)
    if seniority:
        parts.append("seniority = %s")
        params.append(seniority)
    return " AND ".join(parts), params


def _recruiter_in_organization(user_id: int, organization_id: int) -> bool:
    """True if `user_id` has a recruiter_profile bound to `organization_id`."""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM recruiter_profiles WHERE user_id = %s AND organization_id = %s",
            (user_id, organization_id),
        )
        return cur.fetchone() is not None


def _get_resume_row(resume_id: int) -> Optional[tuple]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {RESUME_DETAIL_COLS} FROM candidate_resumes WHERE resume_id = %s", (resume_id,))
        return cur.fetchone()


def _get_job_row(job_id: int) -> Optional[tuple]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(f"SELECT {JOB_DETAIL_COLS} FROM job_posts WHERE job_id = %s", (job_id,))
        return cur.fetchone()


def _set_resume_status(resume_id: int, status: str, user: CurrentUser) -> ResumeDetail:
    row = _get_resume_row(resume_id)
    if row is None:
        raise business_error(404, "not_found", "Resume not found.")
    if row[1] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own resumes.")
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE candidate_resumes SET status = %s, updated_at = now() WHERE resume_id = %s RETURNING {RESUME_DETAIL_COLS}",
            (status, resume_id),
        )
        updated = cur.fetchone()
        _audit(cur, user.user_id, f"resume_{status}", "resume", resume_id)
    return resume_detail(updated)


def _set_job_status(job_id: int, status: str, user: CurrentUser) -> JobDetail:
    row = _get_job_row(job_id)
    if row is None:
        raise business_error(404, "not_found", "Job not found.")
    if user.role == "recruiter" and row[2] != user.user_id:
        raise business_error(403, "forbidden", "You can update only your own jobs.")
    published_set = ", published_at = COALESCE(published_at, now())" if status == "published" else ""
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"UPDATE job_posts SET status = %s{published_set}, updated_at = now() WHERE job_id = %s RETURNING {JOB_DETAIL_COLS}",
            (status, job_id),
        )
        updated = cur.fetchone()
        _audit(cur, user.user_id, f"job_{status}", "job", job_id)
    return job_detail(updated)


def _row_to_job_model(row: tuple) -> JobPostMatch:
    return JobPostMatch(
        job_id=row[0],
        title=row[3],
        skills=tuple(row[5] or []),
        requirement=row[4],
        location=row[6],
        job_type=row[7],
        seniority=row[8],
        education=row[9],
        required_certifications=tuple(row[10] or []),
    )


def _row_to_cv_model(row: tuple) -> CandidateProfileMatch:
    return CandidateProfileMatch(
        cv_id=row[0],
        title=row[2],
        skills=tuple(row[5] or []),
        summary=row[3],
        experience=row[4],
        location=row[6],
        job_type=row[7],
        seniority=row[8],
        education=row[9],
        certifications=tuple(row[10] or []),
    )


def _parse_vec(value: Optional[str]) -> Optional[list[float]]:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return [float(x) for x in stripped.strip("[]").split(",")]


def _load_job(job_id: int) -> Optional[dict[str, Any]]:
    row = _get_job_row(job_id)
    if row is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT emb_title::text, emb_skills::text, emb_requirement::text FROM job_post_embeddings WHERE job_id = %s",
            (job_id,),
        )
        emb = cur.fetchone()
    return {
        "row": row,
        "model": _row_to_job_model(row),
        "summary": job_summary((row[0], row[3], row[6], row[7], row[8], row[9], row[5], row[10], row[11], row[12])),
        "status": row[11],
        "emb": JobEmbeddings(job_id, _parse_vec(emb[0]), _parse_vec(emb[1]), _parse_vec(emb[2])) if emb else None,
    }


def _load_resume(resume_id: int) -> Optional[dict[str, Any]]:
    row = _get_resume_row(resume_id)
    if row is None:
        return None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT emb_title::text, emb_skills::text, emb_summary::text, emb_experience::text FROM candidate_resume_embeddings WHERE resume_id = %s",
            (resume_id,),
        )
        emb = cur.fetchone()
    return {
        "row": row,
        "model": _row_to_cv_model(row),
        "summary": resume_summary((row[0], row[2], row[6], row[7], row[8], row[9], row[5], row[10], row[12])),
        "status": row[12],
        "emb": CandidateEmbeddings(resume_id, _parse_vec(emb[0]), _parse_vec(emb[1]), _parse_vec(emb[2]), _parse_vec(emb[3])) if emb else None,
    }


def _score_pair(job: JobPostMatch, job_emb: Optional[JobEmbeddings], cv: CandidateProfileMatch, cv_emb: Optional[CandidateEmbeddings]):
    missing: list[str] = []
    if not job_emb or job_emb.emb_title is None:
        missing.append("job.emb_title")
    if not cv_emb or cv_emb.emb_title is None:
        missing.append("resume.emb_title")
    title = cosine_similarity(job_emb.emb_title if job_emb else None, cv_emb.emb_title if cv_emb else None)
    if not job_emb or job_emb.emb_skills is None:
        missing.append("job.emb_skills")
    if not cv_emb or cv_emb.emb_skills is None:
        missing.append("resume.emb_skills")
    semantic_skills = cosine_similarity(job_emb.emb_skills if job_emb else None, cv_emb.emb_skills if cv_emb else None)
    exact = exact_overlap_ratio(job.skills, cv.skills)
    skills = compute_skills_score(semantic_skills, exact)
    if not job_emb or job_emb.emb_requirement is None:
        missing.append("job.emb_requirement")
    if not cv_emb or cv_emb.emb_experience is None:
        missing.append("resume.emb_experience")
    req_exp = cosine_similarity(job_emb.emb_requirement if job_emb else None, cv_emb.emb_experience if cv_emb else None)
    if not cv_emb or cv_emb.emb_summary is None:
        missing.append("resume.emb_summary")
    req_summary = cosine_similarity(job_emb.emb_requirement if job_emb else None, cv_emb.emb_summary if cv_emb else None)
    return {
        "title_sim": title,
        "skills_sim": skills,
        "req_exp_sim": req_exp,
        "req_summary_sim": req_summary,
        "exact": exact,
        "final_score": compute_final_score(title, skills, req_exp, req_summary),
    }, list(dict.fromkeys(missing))


def _hard_filter_notes(job: JobPostMatch) -> list[str]:
    notes = ["job_type matched", "seniority matched", "education requirement satisfied"]
    if job.job_type == "remote":
        notes.append("remote job skips location hard filter")
    else:
        notes.append("location matched")
    if job.required_certifications:
        notes.append("required certifications satisfied")
    return notes


def _run_matching(anchor_type: str, anchor_id: int, request: MatchingRequest) -> MatchingResponse:
    start = time.perf_counter()
    if anchor_type == "job":
        anchor = _load_job(anchor_id)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {RESUME_DETAIL_COLS} FROM candidate_resumes WHERE status = 'active' ORDER BY resume_id ASC")
            candidates = [_load_resume(r[0]) for r in cur.fetchall()]
        scored = []
        for candidate in candidates:
            if candidate and passes_hard_filter(anchor["model"], candidate["model"]):
                scores, missing = _score_pair(anchor["model"], anchor["emb"], candidate["model"], candidate["emb"])
                scored.append((candidate, scores, missing))
        scored.sort(key=lambda x: (-x[1]["final_score"], x[0]["model"].cv_id))
        scored = [x for x in scored if x[1]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                resume=candidate["summary"],
                final_score=round(scores["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(**{k: round(scores[k], 6) for k in ("title_sim", "skills_sim", "req_exp_sim", "req_summary_sim")}),
                exact_skill_overlap=matched_skills_sorted(anchor["model"].skills, candidate["model"].skills),
                hard_filter_notes=_hard_filter_notes(anchor["model"]),
                reasoning=build_reasoning(
                    title_score=scores["title_sim"],
                    skills_score=scores["skills_sim"],
                    req_exp_score=scores["req_exp_sim"],
                    req_summary_score=scores["req_summary_sim"],
                    matched_skills=matched_skills_sorted(anchor["model"].skills, candidate["model"].skills),
                    missing_emb_fields=missing,
                ),
                missing_embedding_notes=missing,
            )
            for i, (candidate, scores, missing) in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "job", "job_id": anchor_id, "status": anchor["status"]}
    else:
        anchor = _load_resume(anchor_id)
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(f"SELECT {JOB_DETAIL_COLS} FROM job_posts WHERE status = 'published' ORDER BY job_id ASC")
            candidates = [_load_job(r[0]) for r in cur.fetchall()]
        scored = []
        for candidate in candidates:
            if candidate and passes_hard_filter(candidate["model"], anchor["model"]):
                scores, missing = _score_pair(candidate["model"], candidate["emb"], anchor["model"], anchor["emb"])
                scored.append((candidate, scores, missing))
        scored.sort(key=lambda x: (-x[1]["final_score"], x[0]["model"].job_id))
        scored = [x for x in scored if x[1]["final_score"] >= request.min_score][: request.top_k]
        items = [
            MatchingItem(
                rank=i,
                job=candidate["summary"],
                final_score=round(scores["final_score"], 6),
                score_breakdown=MatchingScoreBreakdown(**{k: round(scores[k], 6) for k in ("title_sim", "skills_sim", "req_exp_sim", "req_summary_sim")}),
                exact_skill_overlap=matched_skills_sorted(candidate["model"].skills, anchor["model"].skills),
                hard_filter_notes=_hard_filter_notes(candidate["model"]),
                reasoning=build_reasoning(
                    title_score=scores["title_sim"],
                    skills_score=scores["skills_sim"],
                    req_exp_score=scores["req_exp_sim"],
                    req_summary_score=scores["req_summary_sim"],
                    matched_skills=matched_skills_sorted(candidate["model"].skills, anchor["model"].skills),
                    missing_emb_fields=missing,
                ),
                missing_embedding_notes=missing,
            )
            for i, (candidate, scores, missing) in enumerate(scored, start=1)
        ]
        anchor_payload = {"type": "resume", "resume_id": anchor_id, "status": anchor["status"]}
    return MatchingResponse(anchor=anchor_payload, items=items, runtime={"total_ms": round((time.perf_counter() - start) * 1000, 2), "rerank_ms": 0.0})


def _document_detail(row: tuple) -> DocumentDetail:
    return DocumentDetail(
        document_id=row[0],
        owner_user_id=row[1],
        document_type=row[2],
        object_key=row[3],
        file_url=row[4],
        original_filename=row[5],
        mime_type=row[6],
        file_size_bytes=row[7],
        resume_id=row[8],
        job_id=row[9],
        created_at=_dt(row[10]),
    )


def _get_document_row(document_id: int, user: CurrentUser) -> Optional[tuple]:
    where = "document_id = %s" if user.role == "admin" else "document_id = %s AND owner_user_id = %s"
    params = (document_id,) if user.role == "admin" else (document_id, user.user_id)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT document_id, owner_user_id, document_type, object_key, file_url,
                   original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            FROM uploaded_documents WHERE {where}
            """,
            params,
        )
        return cur.fetchone()


def _parse_job_detail(row: tuple) -> dict[str, Any]:
    return {
        "parse_job_id": row[0],
        "document_id": row[1],
        "target_entity_type": row[2],
        "resume_id": row[3],
        "job_id": row[4],
        "status": row[5],
        "error_code": row[6],
        "error_message": row[7],
        "created_at": _dt(row[8]),
        "updated_at": _dt(row[9]),
    }


def _application_detail(row: tuple) -> ApplicationDetail:
    return ApplicationDetail(application_id=row[0], job_id=row[1], candidate_user_id=row[2], resume_id=row[3], status=row[4])


def _application_visibility(user: CurrentUser, status: Any, job_id: Any, resume_id: Any):
    if user.role == "candidate":
        where = ["a.candidate_user_id = %s"]
        params: list[Any] = [user.user_id]
    elif user.role == "recruiter":
        where = ["j.recruiter_user_id = %s"]
        params = [user.user_id]
    else:
        where = ["TRUE"]
        params = []
    if status:
        where.append("a.status = %s")
        params.append(status)
    if job_id:
        where.append("a.job_id = %s")
        params.append(job_id)
    if resume_id:
        where.append("a.resume_id = %s")
        params.append(resume_id)
    return " AND ".join(where), params


def _get_application_row(application_id: int, user: CurrentUser) -> Optional[tuple]:
    where, params = _application_visibility(user, None, None, None)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT a.application_id, a.job_id, a.candidate_user_id, a.resume_id, a.status
            FROM applications a JOIN job_posts j USING (job_id)
            WHERE {where} AND a.application_id = %s
            """,
            (*params, application_id),
        )
        return cur.fetchone()


def _create_application(job_id: int, resume_id: int, candidate_user_id: int, actor_user_id: int, note: Optional[str], allow_existing: bool = False) -> tuple:
    resume = _get_resume_row(resume_id)
    job = _get_job_row(job_id)
    if resume is None or resume[12] != "active" or resume[1] != candidate_user_id:
        raise business_error(404, "not_found", "Active owned resume not found.")
    if job is None or job[11] != "published":
        raise business_error(404, "not_found", "Published job not found.")
    with get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """
                INSERT INTO applications (job_id, candidate_user_id, resume_id)
                VALUES (%s, %s, %s)
                RETURNING application_id, job_id, candidate_user_id, resume_id, status
                """,
                (job_id, candidate_user_id, resume_id),
            )
            row = cur.fetchone()
            cur.execute(
                "INSERT INTO application_events (application_id, from_status, to_status, actor_user_id, note) VALUES (%s, NULL, 'submitted', %s, %s)",
                (row[0], actor_user_id, note),
            )
            _notify(cur, job[2], "application_submitted", "Application submitted", "A candidate applied to your job.", "application", row[0])
            _audit(cur, actor_user_id, "candidate_applied", "application", row[0])
            return row
        except psycopg.errors.UniqueViolation as exc:
            if not allow_existing:
                raise business_error(409, "duplicate_application", "Application already exists.") from exc
            conn.rollback()
            with conn.cursor() as cur2:
                cur2.execute(
                    "SELECT application_id, job_id, candidate_user_id, resume_id, status FROM applications WHERE job_id = %s AND resume_id = %s",
                    (job_id, resume_id),
                )
                return cur2.fetchone()


def _invite_visibility(user: CurrentUser, status: Any, job_id: Any, resume_id: Any):
    if user.role == "candidate":
        where = ["i.candidate_user_id = %s"]
        params: list[Any] = [user.user_id]
    elif user.role == "recruiter":
        where = ["i.recruiter_user_id = %s"]
        params = [user.user_id]
    else:
        where = ["TRUE"]
        params = []
    if status:
        where.append("i.status = %s")
        params.append(status)
    if job_id:
        where.append("i.job_id = %s")
        params.append(job_id)
    if resume_id:
        where.append("i.resume_id = %s")
        params.append(resume_id)
    return " AND ".join(where), params


def _invite_detail(row: tuple) -> InviteDetail:
    return InviteDetail(invite_id=row[0], job_id=row[1], resume_id=row[2], candidate_user_id=row[3], recruiter_user_id=row[4], status=row[5], message=row[6])


def _get_invite_row(invite_id: int, user: CurrentUser) -> Optional[tuple]:
    where, params = _invite_visibility(user, None, None, None)
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT i.invite_id, i.job_id, i.resume_id, i.candidate_user_id, i.recruiter_user_id, i.status, i.message
            FROM recruiter_invites i JOIN job_posts j USING (job_id)
            WHERE {where} AND i.invite_id = %s
            """,
            (*params, invite_id),
        )
        return cur.fetchone()


def _notification_detail(row: tuple) -> NotificationDetail:
    return NotificationDetail(notification_id=row[0], recipient_user_id=row[1], type=row[2], status=row[3], title=row[4], body=row[5], entity_type=row[6], entity_id=row[7])


def _notify(cur: psycopg.Cursor, user_id: int, typ: str, title: str, body: str, entity_type: str, entity_id: int) -> None:
    cur.execute(
        """
        INSERT INTO notifications
            (recipient_user_id, type, title, body, entity_type, entity_id, email_delivery_status)
        VALUES (%s, %s, %s, %s, %s, %s, 'queued')
        """,
        (user_id, typ, title, body, entity_type, entity_id),
    )


def _audit(cur: psycopg.Cursor, actor_id: Optional[int], event: str, entity_type: str, entity_id: Optional[int]) -> None:
    cur.execute(
        """
        INSERT INTO audit_logs (actor_user_id, event_type, target_entity_type, target_entity_id)
        VALUES (%s, %s, %s, %s)
        """,
        (actor_id, event, entity_type, entity_id),
    )


def _admin_filters(**kwargs):
    where = []
    params = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "q":
            where.append("email ILIKE %s")
            params.append(f"%{value}%")
        else:
            where.append(f"{key} = %s")
            params.append(value)
    return " AND ".join(where or ["TRUE"]), params


ALL_API_ROUTERS = [
    auth_router,
    me_router,
    candidate_router,
    recruiter_router,
    organizations_router,
    jobs_router,
    documents_router,
    matching_router,
    applications_router,
    invites_router,
    notifications_router,
    admin_router,
]
