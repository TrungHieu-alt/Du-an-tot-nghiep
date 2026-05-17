from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any, Literal, Optional

from fastapi import Depends, Header, HTTPException
from psycopg.types.json import Jsonb
from pydantic import BaseModel, ConfigDict

from jobconnect.core.database import get_connection as _get_connection
from jobconnect.integrations.email import EmailSendError, get_email_sender as _get_email_sender
from jobconnect.integrations.embedding import get_embedding_provider as _get_embedding_provider
from jobconnect.integrations.llm import get_parser as _get_parser
from jobconnect.integrations.storage import get_storage as _get_storage

logger = logging.getLogger(__name__)

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


class Paginated(APIModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    email: str
    role: Role
    status: UserStatus


def business_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def to_error_envelope(detail: Any, status_code: int) -> dict[str, Any]:
    if isinstance(detail, dict) and "code" in detail and "message" in detail:
        return {"error": detail}
    if isinstance(detail, str):
        return {"error": {"code": f"http_{status_code}", "message": detail}}
    return {"error": {"code": f"http_{status_code}", "message": "Unexpected error."}}


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_json(data: dict[str, Any]) -> str:
    return _b64(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _unb64_json(data: str) -> dict[str, Any]:
    padded = data + "=" * (-len(data) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def _jwt_secret() -> bytes:
    return os.getenv("JWT_SECRET", "dev-secret-change-me").encode("utf-8")


def _jwt_ttl_seconds() -> int:
    try:
        return max(1, int(os.getenv("JWT_TTL_SECONDS", "86400")))
    except ValueError:
        return 86400


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds, salt_hex, digest_hex = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(rounds),
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> tuple[str, int]:
    now = int(time.time())
    ttl = _jwt_ttl_seconds()
    payload = {"sub": user_id, "role": role, "iat": now, "exp": now + ttl}
    header = _b64_json({"alg": "HS256", "typ": "JWT"})
    body = _b64_json(payload)
    signed = f"{header}.{body}".encode("ascii")
    sig = _b64(hmac.new(_jwt_secret(), signed, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}", ttl


def parse_token(token: str) -> dict[str, Any]:
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise business_error(401, "invalid_token", "Malformed JWT.") from exc
    signed = f"{header_b64}.{body_b64}".encode("ascii")
    expected_sig = _b64(hmac.new(_jwt_secret(), signed, hashlib.sha256).digest())
    if not hmac.compare_digest(expected_sig, sig_b64):
        raise business_error(401, "invalid_token", "Invalid token signature.")
    payload = _unb64_json(body_b64)
    exp = payload.get("exp")
    if exp is None or int(exp) < int(time.time()):
        raise business_error(401, "expired_token", "Token has expired.")
    return payload


# Compatibility-callable dependency providers.
get_connection = _get_connection
get_embedding_provider = _get_embedding_provider
get_parser = _get_parser
get_storage = _get_storage
get_email_sender = _get_email_sender


def current_user(authorization: Optional[str] = Header(default=None)) -> CurrentUser:
    if authorization is None or not authorization.lower().startswith("bearer "):
        raise business_error(401, "invalid_token", "Missing or invalid JWT.")
    payload = parse_token(authorization.split(" ", 1)[1])
    user_id = int(payload.get("sub", 0))
    # Resolve through the compatibility router module so monkeypatching
    # `jobconnect.modules.api.router.get_connection` keeps working in tests.
    from jobconnect.modules.api import router as api_router

    with api_router.get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT user_id, email, role, status FROM users WHERE user_id = %s",
            (user_id,),
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


def public_resume_filters(q: Optional[str], location: Any, job_type: Any, seniority: Any):
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


def visible_job_list_filter(user: CurrentUser, status: Optional[str]):
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


def visible_job_search_filter(
    user: CurrentUser,
    q: Optional[str],
    location: Any,
    job_type: Any,
    seniority: Any,
    status: Any,
):
    where, params = visible_job_list_filter(user, status)
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


JOB_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "published": {"draft"},
    "closed": {"draft", "published"},
}

RESUME_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "active": {"draft", "archived"},
    "archived": {"draft", "active"},
}

APPLICATION_STATUS_TRANSITIONS: dict[str, dict[str, set[str]]] = {
    "candidate": {
        "withdrawn": {"submitted", "shortlisted"},
    },
    "recruiter": {
        "shortlisted": {"submitted"},
        "rejected": {"submitted", "shortlisted"},
        "hired": {"submitted", "shortlisted"},
    },
}
APPLICATION_TERMINAL_STATUSES = {"rejected", "hired", "withdrawn"}


def validate_application_transition(current: str, target: str, role: str) -> None:
    if current in APPLICATION_TERMINAL_STATUSES:
        raise business_error(
            409,
            "invalid_transition",
            f"Terminal application status {current} cannot transition further.",
        )
    role_transitions = APPLICATION_STATUS_TRANSITIONS.get(role)
    if not role_transitions or target not in role_transitions:
        if role == "candidate":
            raise business_error(403, "forbidden", "Candidates can only withdraw applications.")
        if role == "recruiter":
            raise business_error(403, "forbidden", "Recruiters cannot set this status.")
        raise business_error(403, "forbidden", "Role is not allowed to change application status.")
    if current not in role_transitions[target]:
        raise business_error(
            409,
            "invalid_transition",
            f"Application cannot transition from {current} to {target}.",
        )


def _jsonb(value: Optional[dict[str, Any]]) -> Jsonb:
    return Jsonb(value or {})


def _notification_metadata(
    typ: str,
    actor_id: Optional[int],
    entity_type: str,
    entity_id: Optional[int],
    metadata: Optional[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(metadata or {})
    payload.setdefault("event_type", typ)
    payload.setdefault("target_type", entity_type)
    payload.setdefault("target_id", entity_id)
    if actor_id is not None:
        payload.setdefault("actor_id", actor_id)
    return payload


def notify(
    cur: Any,
    user_id: int,
    typ: str,
    title: str,
    body: str,
    entity_type: str,
    entity_id: Optional[int],
    *,
    actor_id: Optional[int] = None,
    metadata: Optional[dict[str, Any]] = None,
    email_subject: Optional[str] = None,
    email_body: Optional[str] = None,
) -> None:
    payload = _notification_metadata(typ, actor_id, entity_type, entity_id, metadata)
    cur.execute(
        """
        INSERT INTO notifications
            (recipient_user_id, type, title, body, entity_type, entity_id, email_delivery_status, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, 'queued', %s)
        RETURNING notification_id
        """,
        (user_id, typ, title, body, entity_type, entity_id, _jsonb(payload)),
    )
    row = cur.fetchone()
    notification_id = row[0] if row else None

    cur.execute("SELECT email FROM users WHERE user_id = %s", (user_id,))
    email_row = cur.fetchone()
    recipient_email = email_row[0] if email_row else None

    provider = "unknown"
    status = "failed"
    error_message: Optional[str] = None
    subject = email_subject or title
    message_body = email_body or body
    try:
        from jobconnect.modules.api import router as api_router

        result = api_router.get_email_sender().send_email(
            recipient_email,
            subject,
            message_body,
            metadata=payload,
        )
        status = result.status
        provider = result.provider
    except EmailSendError as exc:
        provider = exc.provider
        error_message = str(exc)[:1000]
        logger.warning("Email send failed for notification_id=%s: %s", notification_id, exc)
    except Exception as exc:
        error_message = str(exc)[:1000]
        logger.warning("Email send failed for notification_id=%s: %s", notification_id, exc)

    attempt_metadata = dict(payload)
    attempt_metadata["notification_id"] = notification_id
    cur.execute(
        """
        INSERT INTO email_attempts
            (recipient_email, recipient_user_id, subject, body_preview, event_type, status,
             provider, error_message, entity_type, entity_id, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING email_attempt_id
        """,
        (
            recipient_email,
            user_id,
            subject,
            message_body[:1000],
            typ,
            status,
            provider,
            error_message,
            entity_type,
            entity_id,
            _jsonb(attempt_metadata),
        ),
    )
    attempt_row = cur.fetchone()
    attempt_id = attempt_row[0] if attempt_row else None
    cur.execute(
        "UPDATE notifications SET email_delivery_status = %s, updated_at = now() WHERE notification_id = %s",
        (status, notification_id),
    )
    email_audit_event = "email_send_failed" if status == "failed" else "email_attempt_recorded"
    audit(
        cur,
        actor_id,
        email_audit_event,
        "notification",
        notification_id,
        metadata={
            "email_attempt_id": attempt_id,
            "notification_type": typ,
            "recipient_user_id": user_id,
            "status": status,
            "provider": provider,
            "error_message": error_message,
            "target_type": entity_type,
            "target_id": entity_id,
        },
    )


def audit(
    cur: Any,
    actor_id: Optional[int],
    event: str,
    entity_type: str,
    entity_id: Optional[int],
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    cur.execute(
        """
        INSERT INTO audit_logs (actor_user_id, event_type, target_entity_type, target_entity_id, metadata)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (actor_id, event, entity_type, entity_id, _jsonb(metadata)),
    )


def dispatch_email(notification_id: int) -> None:
    """Attempt to send an email for a committed notification row.

    Uses a separate DB connection so any failure cannot affect the caller's
    already-committed business transaction. All exceptions are swallowed and
    logged — email delivery is best-effort.
    """
    if notification_id <= 0:
        return
    import logging as _logging
    _log = _logging.getLogger(__name__)
    try:
        from jobconnect.integrations.email import get_email_sender
        from jobconnect.modules.api import router as _api

        with _api.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT n.recipient_user_id, n.title, n.body,
                       u.email
                  FROM notifications n
                  JOIN users u ON u.user_id = n.recipient_user_id
                 WHERE n.notification_id = %s
                """,
                (notification_id,),
            )
            row = cur.fetchone()
        if row is None:
            return
        _recipient_id, title, body, to_email = row
        sender = get_email_sender()
        sender.send_email(to_email, title, body)
        with _api.get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE notifications SET email_delivery_status = 'sent', updated_at = now() WHERE notification_id = %s",
                (notification_id,),
            )
    except Exception:
        _log.exception("Email dispatch failed for notification_id=%d", notification_id)
        try:
            from jobconnect.modules.api import router as _api2
            with _api2.get_connection() as conn, conn.cursor() as cur:
                cur.execute(
                    "UPDATE notifications SET email_delivery_status = 'failed', updated_at = now() WHERE notification_id = %s",
                    (notification_id,),
                )
        except Exception:
            _log.exception("Could not mark email_delivery_status=failed for notification_id=%d", notification_id)


def admin_filters(**kwargs):
    where = []
    params = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "q":
            where.append("email ILIKE %s")
            params.append(f"%{value}%")
        elif key == "parse_status":
            where.append(
                "EXISTS (SELECT 1 FROM parse_jobs p WHERE p.document_id = uploaded_documents.document_id AND p.status = %s)"
            )
            params.append(value)
        else:
            where.append(f"{key} = %s")
            params.append(value)
    return " AND ".join(where or ["TRUE"]), params


def admin_user_ops_summary(cur: Any, user_id: int) -> dict[str, int]:
    queries = {
        "resumes": "SELECT COUNT(*) FROM candidate_resumes WHERE candidate_user_id = %s",
        "jobs": "SELECT COUNT(*) FROM job_posts WHERE recruiter_user_id = %s",
        "applications": "SELECT COUNT(*) FROM applications WHERE candidate_user_id = %s",
        "invites": "SELECT COUNT(*) FROM recruiter_invites WHERE candidate_user_id = %s OR recruiter_user_id = %s",
        "documents": "SELECT COUNT(*) FROM uploaded_documents WHERE owner_user_id = %s",
        "parse_failures": """
            SELECT COUNT(*)
              FROM parse_jobs pj
              JOIN uploaded_documents ud USING (document_id)
             WHERE ud.owner_user_id = %s AND pj.status = 'failed'
        """,
    }
    summary: dict[str, int] = {}
    for key, sql in queries.items():
        params = (user_id, user_id) if key == "invites" else (user_id,)
        cur.execute(sql, params)
        row = cur.fetchone()
        summary[key] = int(row[0]) if row else 0
    return summary
