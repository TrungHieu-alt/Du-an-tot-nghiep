from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from fastapi import BackgroundTasks, UploadFile

from jobconnect.modules.api.shared import CurrentUser, Paginated, ParseStatus, _dt, audit, business_error
from jobconnect.modules.documents.schemas import (
    DocumentDetail,
    DocumentDownloadUrlResponse,
    DocumentUploadResponse,
    ParseJobDetail,
)
from jobconnect.modules.documents.worker import run_parse_job

ALLOWED_DOCUMENT_MIME_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

MAX_DOCUMENT_BYTES: int = 10 * 1024 * 1024


def _api():
    from jobconnect.modules.api import router as api_router

    return api_router


def document_detail(row: tuple) -> DocumentDetail:
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


def parse_job_detail(row: tuple) -> ParseJobDetail:
    return ParseJobDetail(
        parse_job_id=row[0],
        document_id=row[1],
        target_entity_type=row[2],
        resume_id=row[3],
        job_id=row[4],
        status=row[5],
        error_code=row[6],
        error_message=row[7],
        created_at=_dt(row[8]),
        updated_at=_dt(row[9]),
    )


def get_document_row(document_id: int, user: CurrentUser) -> Optional[tuple]:
    where = "document_id = %s" if user.role == "admin" else "document_id = %s AND owner_user_id = %s"
    params = (document_id,) if user.role == "admin" else (document_id, user.user_id)
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT document_id, owner_user_id, document_type, object_key, file_url,
                   original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            FROM uploaded_documents WHERE {where}
            """,
            params,
        )
        return cur.fetchone()


def create_document(
    document_type: Literal["candidate_resume", "job_post"],
    file: UploadFile,
    resume_id: Optional[int],
    job_id: Optional[int],
    user: CurrentUser,
    background_tasks: Optional[BackgroundTasks],
) -> DocumentUploadResponse:
    mime_type = (file.content_type or "").lower()
    if mime_type not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise business_error(415, "unsupported_mime_type", f"MIME type {mime_type!r} is not allowed.")

    original_filename = file.filename or "upload"
    try:
        stored = _api().get_storage().save(
            file.file,
            key_hint=original_filename,
            content_type=mime_type,
            max_bytes=_api().MAX_DOCUMENT_BYTES,
        )
    except ValueError as exc:
        raise business_error(413, "file_too_large", str(exc)) from exc
    finally:
        try:
            file.file.close()
        except Exception:
            pass

    parser_version = _api().get_parser().parser_version
    embedding_version = _api().get_embedding_provider().embedding_version

    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO uploaded_documents
                (owner_user_id, document_type, object_key, file_url, original_filename,
                 mime_type, file_size_bytes, resume_id, job_id)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s)
            RETURNING document_id, owner_user_id, document_type, object_key, file_url,
                      original_filename, mime_type, file_size_bytes, resume_id, job_id, created_at
            """,
            (
                user.user_id,
                document_type,
                stored.object_key,
                original_filename,
                mime_type,
                stored.size_bytes,
                resume_id,
                job_id,
            ),
        )
        document_row = cur.fetchone()
        cur.execute(
            """
            INSERT INTO parse_jobs
                (document_id, target_entity_type, resume_id, job_id, parser_version, embedding_version_requested)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                      error_code, error_message, created_at, updated_at
            """,
            (document_row[0], document_type, resume_id, job_id, parser_version, embedding_version),
        )
        parse_row = cur.fetchone()
        audit(cur, user.user_id, "document_uploaded", "document", document_row[0])

    parse_job_id: int = parse_row[0]
    if background_tasks is not None:
        background_tasks.add_task(run_parse_job, parse_job_id)

    return DocumentUploadResponse(document=document_detail(document_row), parse_job=parse_job_detail(parse_row))


def list_documents(
    document_type: Optional[Literal["candidate_resume", "job_post"]],
    parse_status: Optional[ParseStatus],
    limit: int,
    offset: int,
    user: CurrentUser,
) -> Paginated:
    where = ["TRUE"] if user.role == "admin" else ["owner_user_id = %s"]
    params: list[Any] = [] if user.role == "admin" else [user.user_id]
    if document_type:
        where.append("document_type = %s")
        params.append(document_type)
    if parse_status:
        where.append("EXISTS (SELECT 1 FROM parse_jobs p WHERE p.document_id = uploaded_documents.document_id AND p.status = %s)")
        params.append(parse_status)
    sql_where = " AND ".join(where)

    with _api().get_connection() as conn, conn.cursor() as cur:
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
        items = [document_detail(r) for r in cur.fetchall()]
    return Paginated(items=items, total=total, limit=limit, offset=offset)


def get_document(document_id: int, user: CurrentUser) -> DocumentDetail:
    row = get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                   error_code, error_message, created_at, updated_at
              FROM parse_jobs
             WHERE document_id = %s
             ORDER BY parse_job_id ASC
            """,
            (document_id,),
        )
        parse_jobs = [parse_job_detail(r) for r in cur.fetchall()]
    detail = document_detail(row)
    return detail.model_copy(update={"parse_jobs": parse_jobs})


def get_download_url(document_id: int, user: CurrentUser) -> DocumentDownloadUrlResponse:
    row = get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    object_key = row[3]
    if object_key:
        link = _api().get_storage().download_url(object_key)
        return DocumentDownloadUrlResponse(download_url=link.download_url, expires_at=link.expires_at)

    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=900)).isoformat()
    return DocumentDownloadUrlResponse(download_url=row[4] or "", expires_at=expires_at)


def get_parse_job(document_id: int, parse_job_id: int, user: CurrentUser) -> ParseJobDetail:
    row = get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")

    with _api().get_connection() as conn, conn.cursor() as cur:
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
    return parse_job_detail(parse)


def create_parse_job(document_id: int, user: CurrentUser, background_tasks: Optional[BackgroundTasks]) -> ParseJobDetail:
    row = get_document_row(document_id, user)
    if row is None:
        raise business_error(404, "not_found", "Document not found.")
    parser_version = _api().get_parser().parser_version
    embedding_version = _api().get_embedding_provider().embedding_version

    with _api().get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parse_jobs
                (document_id, target_entity_type, resume_id, job_id, parser_version, embedding_version_requested)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING parse_job_id, document_id, target_entity_type, resume_id, job_id, status,
                      error_code, error_message, created_at, updated_at
            """,
            (document_id, row[2], row[8], row[9], parser_version, embedding_version),
        )
        parse = cur.fetchone()
        audit(cur, user.user_id, "parse_job_retried", "parse_job", parse[0])

    parse_job_id: int = parse[0]
    if background_tasks is not None:
        background_tasks.add_task(run_parse_job, parse_job_id)
    return parse_job_detail(parse)
