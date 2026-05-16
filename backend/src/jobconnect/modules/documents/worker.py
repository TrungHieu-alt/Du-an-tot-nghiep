"""Parse Worker V1 — deterministic local pipeline.

Slice 5 orchestration:
  queued parse_job
  -> mark processing
  -> extract text from storage object
  -> preprocess text
  -> local parse into structured fields
  -> create/update draft entity (candidate_resume or job_post)
  -> upsert provider-backed embeddings
  -> mark succeeded / failed
  -> on failure: create notification + audit

Slice 6 swaps the local_parser calls for an LLM adapter without changing
the surrounding pipeline structure.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from jobconnect.core.database import get_connection
from jobconnect.integrations.embedding import EmbeddingError, get_embedding_provider
from jobconnect.integrations.llm import ParserError, get_parser
from jobconnect.integrations.pgvector import vector_to_pg_literal
from jobconnect.integrations.storage import get_storage
from jobconnect.modules.documents.extractor import extract_text
from jobconnect.modules.documents.local_parser import ParsedJob, ParsedResume
from jobconnect.modules.documents.preprocessor import preprocess_text

logger = logging.getLogger(__name__)

# Slice 6/7: parser_version + embedding_version come from the active adapters.
# These module-level constants are retained as defaults for backward
# compatibility with callers/tests; live values flow through _mark_succeeded
# and the upsert helpers.
PARSER_VERSION = "local-v1"
EMBEDDING_VERSION = "hash-v1"


@dataclass
class _ParseJobInfo:
    parse_job_id: int
    document_id: int
    target_entity_type: str
    existing_resume_id: Optional[int]
    existing_job_id: Optional[int]
    status: str
    object_key: str
    mime_type: str
    original_filename: str
    owner_user_id: int


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_parse_job(parse_job_id: int) -> None:
    """Execute the full parse pipeline for one queued parse job.

    Designed to be called from a FastAPI BackgroundTask or a test directly.
    All exceptions are caught at the top level to prevent background task
    crashes from surfacing to the client after the 201 response was sent.
    """
    try:
        _execute(parse_job_id)
    except Exception:
        logger.exception("Critical worker error for parse_job_id=%d", parse_job_id)


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------


def _execute(parse_job_id: int) -> None:
    info = _load_parse_job(parse_job_id)
    if info is None or info.status != "queued":
        return

    _mark_processing(parse_job_id)

    # Text extraction
    try:
        stream = get_storage().open(info.object_key)
        try:
            raw_text = extract_text(stream, info.mime_type)
        finally:
            stream.close()
    except Exception as exc:
        _fail(info, "extraction_failed", f"Text extraction error: {exc}")
        return

    if not raw_text.strip():
        _fail(info, "empty_extraction", "No text could be extracted from the file.")
        return

    text = preprocess_text(raw_text)

    # Slice 6: structured parsing through the LLM adapter (local fallback by default).
    parser = get_parser()

    # Parse + entity creation
    try:
        if info.target_entity_type == "candidate_resume":
            parsed_resume = parser.parse_resume(text, filename=info.original_filename)
            entity_id, embedding_version = _upsert_resume(info, parsed_resume)
        else:
            org_id = _get_organization_id(info.owner_user_id)
            if org_id is None:
                _fail(info, "recruiter_profile_missing", "Recruiter profile or organization not found.")
                return
            parsed_job = parser.parse_job(text, filename=info.original_filename)
            entity_id, embedding_version = _upsert_job(info, org_id, parsed_job)
    except ParserError as exc:
        _fail(info, "llm_parse_failed", f"LLM parser error: {exc}")
        return
    except EmbeddingError as exc:
        _fail(info, "embedding_failed", f"Embedding provider error: {exc}")
        return
    except Exception as exc:
        _fail(info, "parse_failed", f"Parsing error: {exc}")
        return

    _mark_succeeded(
        info,
        entity_id,
        text,
        parser_version=parser.parser_version,
        embedding_version=embedding_version,
    )


def _load_parse_job(parse_job_id: int) -> Optional[_ParseJobInfo]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT pj.parse_job_id, pj.document_id, pj.target_entity_type,
                   pj.resume_id, pj.job_id, pj.status,
                   ud.object_key, ud.mime_type, ud.original_filename,
                   ud.owner_user_id
              FROM parse_jobs pj
              JOIN uploaded_documents ud ON ud.document_id = pj.document_id
             WHERE pj.parse_job_id = %s
            """,
            (parse_job_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return _ParseJobInfo(
        parse_job_id=row[0],
        document_id=row[1],
        target_entity_type=row[2],
        existing_resume_id=row[3],
        existing_job_id=row[4],
        status=row[5],
        object_key=row[6],
        mime_type=row[7],
        original_filename=row[8] or "",
        owner_user_id=row[9],
    )


def _mark_processing(parse_job_id: int) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE parse_jobs
               SET status = 'processing', started_at = now(), updated_at = now()
             WHERE parse_job_id = %s
            """,
            (parse_job_id,),
        )


def _mark_succeeded(
    info: _ParseJobInfo,
    entity_id: int,
    extracted_text: str,
    parser_version: str = PARSER_VERSION,
    embedding_version: str = EMBEDDING_VERSION,
) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE parse_jobs
               SET status = 'succeeded',
                   extracted_text = %s,
                   parser_version = %s,
                   embedding_version_requested = %s,
                   finished_at = now(),
                   updated_at = now()
             WHERE parse_job_id = %s
            """,
            (extracted_text[:10000], parser_version, embedding_version, info.parse_job_id),
        )
        if info.target_entity_type == "candidate_resume":
            cur.execute(
                "UPDATE uploaded_documents SET resume_id = %s WHERE document_id = %s AND resume_id IS NULL",
                (entity_id, info.document_id),
            )
            cur.execute(
                "UPDATE parse_jobs SET resume_id = %s WHERE parse_job_id = %s AND resume_id IS NULL",
                (entity_id, info.parse_job_id),
            )
        else:
            cur.execute(
                "UPDATE uploaded_documents SET job_id = %s WHERE document_id = %s AND job_id IS NULL",
                (entity_id, info.document_id),
            )
            cur.execute(
                "UPDATE parse_jobs SET job_id = %s WHERE parse_job_id = %s AND job_id IS NULL",
                (entity_id, info.parse_job_id),
            )
        _write_audit(cur, info.owner_user_id, "parse_job_succeeded", "parse_job", info.parse_job_id)


def _fail(info: _ParseJobInfo, error_code: str, error_message: str) -> None:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE parse_jobs
               SET status = 'failed',
                   error_code = %s,
                   error_message = %s,
                   finished_at = now(),
                   updated_at = now()
             WHERE parse_job_id = %s
            """,
            (error_code, error_message[:1000], info.parse_job_id),
        )
        cur.execute(
            """
            INSERT INTO notifications
                (recipient_user_id, type, title, body, entity_type, entity_id, email_delivery_status)
            VALUES (%s, 'parse_failed', 'Document parsing failed', %s, 'parse_job', %s, 'queued')
            """,
            (
                info.owner_user_id,
                f"Your document could not be parsed: {error_message[:200]}",
                info.parse_job_id,
            ),
        )
        _write_audit(cur, info.owner_user_id, "parse_job_failed", "parse_job", info.parse_job_id)


# ---------------------------------------------------------------------------
# Entity upsert helpers
# ---------------------------------------------------------------------------


def _upsert_resume(info: _ParseJobInfo, parsed: ParsedResume) -> tuple[int, str]:
    with get_connection() as conn, conn.cursor() as cur:
        if info.existing_resume_id is not None:
            cur.execute(
                """
                UPDATE candidate_resumes
                   SET title = %s, summary = %s, experience = %s, skills = %s,
                       location = %s, job_type = %s, seniority = %s, education = %s,
                       certifications = %s, updated_at = now()
                 WHERE resume_id = %s AND candidate_user_id = %s
                RETURNING resume_id
                """,
                (
                    parsed.title, parsed.summary, parsed.experience, parsed.skills,
                    parsed.location, parsed.job_type, parsed.seniority, parsed.education,
                    parsed.certifications, info.existing_resume_id, info.owner_user_id,
                ),
            )
            row = cur.fetchone()
            resume_id: int = row[0] if row else info.existing_resume_id
        else:
            cur.execute(
                """
                INSERT INTO candidate_resumes
                    (candidate_user_id, title, summary, experience, skills,
                     location, job_type, seniority, education, certifications, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft')
                RETURNING resume_id
                """,
                (
                    info.owner_user_id, parsed.title, parsed.summary, parsed.experience,
                    parsed.skills, parsed.location, parsed.job_type, parsed.seniority,
                    parsed.education, parsed.certifications,
                ),
            )
            resume_id = cur.fetchone()[0]

        embedding_version = _upsert_resume_embeddings(cur, resume_id, parsed)
        return resume_id, embedding_version


def _upsert_job(info: _ParseJobInfo, organization_id: int, parsed: ParsedJob) -> tuple[int, str]:
    with get_connection() as conn, conn.cursor() as cur:
        if info.existing_job_id is not None:
            cur.execute(
                """
                UPDATE job_posts
                   SET title = %s, requirement = %s, skills = %s,
                       location = %s, job_type = %s, seniority = %s, education = %s,
                       required_certifications = %s, updated_at = now()
                 WHERE job_id = %s AND recruiter_user_id = %s
                RETURNING job_id
                """,
                (
                    parsed.title, parsed.requirement, parsed.skills,
                    parsed.location, parsed.job_type, parsed.seniority, parsed.education,
                    parsed.required_certifications, info.existing_job_id, info.owner_user_id,
                ),
            )
            row = cur.fetchone()
            job_id: int = row[0] if row else info.existing_job_id
        else:
            cur.execute(
                """
                INSERT INTO job_posts
                    (organization_id, recruiter_user_id, title, requirement, skills,
                     location, job_type, seniority, education, required_certifications, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft')
                RETURNING job_id
                """,
                (
                    organization_id, info.owner_user_id, parsed.title, parsed.requirement,
                    parsed.skills, parsed.location, parsed.job_type, parsed.seniority,
                    parsed.education, parsed.required_certifications,
                ),
            )
            job_id = cur.fetchone()[0]

        embedding_version = _upsert_job_embeddings(cur, job_id, parsed)
        return job_id, embedding_version


def _get_organization_id(user_id: int) -> Optional[int]:
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT organization_id FROM recruiter_profiles WHERE user_id = %s",
            (user_id,),
        )
        row = cur.fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------


def _upsert_resume_embeddings(cur, resume_id: int, parsed: ParsedResume) -> str:
    provider = get_embedding_provider()
    cur.execute(
        """
        INSERT INTO candidate_resume_embeddings
            (resume_id, emb_title, emb_skills, emb_summary, emb_experience, embedding_version)
        VALUES (%s, %s::vector, %s::vector, %s::vector, %s::vector, %s)
        ON CONFLICT (resume_id) DO UPDATE
           SET emb_title = EXCLUDED.emb_title,
               emb_skills = EXCLUDED.emb_skills,
               emb_summary = EXCLUDED.emb_summary,
               emb_experience = EXCLUDED.emb_experience,
               embedding_version = EXCLUDED.embedding_version,
               updated_at = now()
        """,
        (
            resume_id,
            vector_to_pg_literal(provider.embed(parsed.title)),
            vector_to_pg_literal(provider.embed(" ".join(parsed.skills))),
            vector_to_pg_literal(provider.embed(parsed.summary)),
            vector_to_pg_literal(provider.embed(parsed.experience)),
            provider.embedding_version,
        ),
    )
    return provider.embedding_version


def _upsert_job_embeddings(cur, job_id: int, parsed: ParsedJob) -> str:
    provider = get_embedding_provider()
    cur.execute(
        """
        INSERT INTO job_post_embeddings
            (job_id, emb_title, emb_skills, emb_requirement, embedding_version)
        VALUES (%s, %s::vector, %s::vector, %s::vector, %s)
        ON CONFLICT (job_id) DO UPDATE
           SET emb_title = EXCLUDED.emb_title,
               emb_skills = EXCLUDED.emb_skills,
               emb_requirement = EXCLUDED.emb_requirement,
               embedding_version = EXCLUDED.embedding_version,
               updated_at = now()
        """,
        (
            job_id,
            vector_to_pg_literal(provider.embed(parsed.title)),
            vector_to_pg_literal(provider.embed(" ".join(parsed.skills))),
            vector_to_pg_literal(provider.embed(parsed.requirement)),
            provider.embedding_version,
        ),
    )
    return provider.embedding_version


# ---------------------------------------------------------------------------
# Shared audit helper
# ---------------------------------------------------------------------------


def _write_audit(cur, actor_user_id: int, event_type: str, target_type: str, target_id: Optional[int]) -> None:
    cur.execute(
        """
        INSERT INTO audit_logs (actor_user_id, event_type, target_entity_type, target_entity_id)
        VALUES (%s, %s, %s, %s)
        """,
        (actor_user_id, event_type, target_type, target_id),
    )
