"""Sync normal Job/CV rows into V2 prototype preparation tables."""

from __future__ import annotations

import logging
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from core.normalizers import normalize_education_level, normalize_skill_name
from core.preprocess import preprocess_text
from core.v2_text_builder import (
    build_candidate_profile_text,
    build_job_post_text,
    prepare_structured_text,
    summarize_candidate_experience,
    summarize_job_requirement,
)
from core.v2_translation import translate_text_to_english_if_needed
from v2_search.minilm import EMBEDDING_DIM, MiniLMUnavailableError, embed_text_minilm


logger = logging.getLogger(__name__)

V2_LOCATIONS = {"Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng"}
V2_JOB_TYPES = {"remote", "fulltime", "parttime"}
V2_SENIORITIES = {"intern", "fresher", "junior", "mid", "senior", "lead"}
V2_EDUCATION = {"high_school", "bachelor", "master", "phd"}


def sync_candidate_profile_v2(cv: dict[str, Any], conn: psycopg.Connection) -> dict[str, Any]:
    """Upsert a linked candidate_profiles_v2 row and refresh its embeddings."""
    result = _prepare_candidate_payload(cv)
    warnings = list(result["preprocess_warnings"]) + list(result["translation_warnings"])
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO candidate_profiles_v2 (
                    normal_cv_id,
                    candidate_id,
                    title,
                    skills,
                    summary,
                    experience,
                    location,
                    job_type,
                    seniority,
                    education,
                    certifications,
                    source_language,
                    prepared_text,
                    prepared_text_en,
                    preprocess_warnings,
                    translation_warnings,
                    text_quality
                )
                VALUES (
                    %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (normal_cv_id) DO UPDATE
                SET candidate_id = EXCLUDED.candidate_id,
                    title = EXCLUDED.title,
                    skills = EXCLUDED.skills,
                    summary = EXCLUDED.summary,
                    experience = EXCLUDED.experience,
                    location = EXCLUDED.location,
                    job_type = EXCLUDED.job_type,
                    seniority = EXCLUDED.seniority,
                    education = EXCLUDED.education,
                    certifications = EXCLUDED.certifications,
                    source_language = EXCLUDED.source_language,
                    prepared_text = EXCLUDED.prepared_text,
                    prepared_text_en = EXCLUDED.prepared_text_en,
                    preprocess_warnings = EXCLUDED.preprocess_warnings,
                    translation_warnings = EXCLUDED.translation_warnings,
                    text_quality = EXCLUDED.text_quality
                RETURNING cv_id
                """,
                (
                    cv["id"],
                    cv["created_by"],
                    result["title"],
                    result["skills"],
                    result["summary"],
                    result["experience"],
                    result["location"],
                    result["job_type"],
                    result["seniority"],
                    result["education"],
                    result["certifications"],
                    result["source_language"],
                    result["prepared_text"],
                    result["prepared_text_en"],
                    Jsonb(result["preprocess_warnings"]),
                    Jsonb(result["translation_warnings"]),
                    Jsonb(result["text_quality"]),
                ),
            )
            row = cur.fetchone()
            profile_id = int(row[0])
            embedding_warnings = _upsert_candidate_embeddings(cur, profile_id, result)
            warnings.extend(embedding_warnings)
        conn.commit()
        return {
            "synced": True,
            "profileId": profile_id,
            "jobPostId": None,
            "warnings": warnings,
        }
    except Exception as exc:
        conn.rollback()
        logger.warning("V2 candidate profile sync failed for normal CV %s: %s", cv.get("id"), exc)
        return {
            "synced": False,
            "profileId": None,
            "jobPostId": None,
            "warnings": ["v2_candidate_sync_failed"],
        }


def sync_job_post_v2(job: dict[str, Any], conn: psycopg.Connection) -> dict[str, Any]:
    """Upsert a linked job_posts_v2 row and refresh its embeddings."""
    result = _prepare_job_payload(job)
    warnings = list(result["preprocess_warnings"]) + list(result["translation_warnings"])
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_posts_v2 (
                    normal_job_id,
                    recruiter_id,
                    title,
                    skills,
                    requirement,
                    location,
                    job_type,
                    seniority,
                    education,
                    required_certifications,
                    source_language,
                    prepared_text,
                    prepared_text_en,
                    preprocess_warnings,
                    translation_warnings,
                    text_quality
                )
                VALUES (
                    %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (normal_job_id) DO UPDATE
                SET recruiter_id = EXCLUDED.recruiter_id,
                    title = EXCLUDED.title,
                    skills = EXCLUDED.skills,
                    requirement = EXCLUDED.requirement,
                    location = EXCLUDED.location,
                    job_type = EXCLUDED.job_type,
                    seniority = EXCLUDED.seniority,
                    education = EXCLUDED.education,
                    required_certifications = EXCLUDED.required_certifications,
                    source_language = EXCLUDED.source_language,
                    prepared_text = EXCLUDED.prepared_text,
                    prepared_text_en = EXCLUDED.prepared_text_en,
                    preprocess_warnings = EXCLUDED.preprocess_warnings,
                    translation_warnings = EXCLUDED.translation_warnings,
                    text_quality = EXCLUDED.text_quality
                RETURNING job_id
                """,
                (
                    job["id"],
                    job["created_by"],
                    result["title"],
                    result["skills"],
                    result["requirement"],
                    result["location"],
                    result["job_type"],
                    result["seniority"],
                    result["education"],
                    result["required_certifications"],
                    result["source_language"],
                    result["prepared_text"],
                    result["prepared_text_en"],
                    Jsonb(result["preprocess_warnings"]),
                    Jsonb(result["translation_warnings"]),
                    Jsonb(result["text_quality"]),
                ),
            )
            row = cur.fetchone()
            job_post_id = int(row[0])
            embedding_warnings = _upsert_job_embeddings(cur, job_post_id, result)
            warnings.extend(embedding_warnings)
        conn.commit()
        return {
            "synced": True,
            "profileId": None,
            "jobPostId": job_post_id,
            "warnings": warnings,
        }
    except Exception as exc:
        conn.rollback()
        logger.warning("V2 job post sync failed for normal job %s: %s", job.get("id"), exc)
        return {
            "synced": False,
            "profileId": None,
            "jobPostId": None,
            "warnings": ["v2_job_sync_failed"],
        }


def _prepare_candidate_payload(cv: dict[str, Any]) -> dict[str, Any]:
    raw_structured_text = build_candidate_profile_text(cv)
    prepared = prepare_structured_text(raw_structured_text)
    translated = translate_text_to_english_if_needed(prepared["prepared_text"])
    summary = preprocess_text(
        "\n".join(
            item
            for item in [
                cv.get("summary"),
                cv.get("target_role"),
                cv.get("headline"),
                translated.text,
            ]
            if item
        )
    )
    experience = summarize_candidate_experience(cv) or translated.text
    return {
        "title": _candidate_title(cv),
        "skills": _skill_names(cv.get("skills")),
        "summary": summary,
        "experience": experience,
        "location": _v2_location(cv.get("location")),
        "job_type": _v2_job_type(cv.get("employment_type"), cv.get("location"), remote_flag=False),
        "seniority": _v2_seniority(cv.get("career_level")),
        "education": _v2_cv_education(cv.get("education")),
        "certifications": _certification_names(cv.get("certifications")),
        "source_language": translated.source_language,
        "prepared_text": prepared["prepared_text"],
        "prepared_text_en": translated.text,
        "preprocess_warnings": prepared["preprocess_warnings"],
        "translation_warnings": translated.warnings,
        "text_quality": prepared["text_quality"],
    }


def _prepare_job_payload(job: dict[str, Any]) -> dict[str, Any]:
    raw_structured_text = build_job_post_text(job)
    prepared = prepare_structured_text(raw_structured_text)
    translated = translate_text_to_english_if_needed(prepared["prepared_text"])
    requirement = summarize_job_requirement(job) or translated.text
    return {
        "title": preprocess_text(job.get("title") or "Job Post"),
        "skills": _skill_names(job.get("skills")),
        "requirement": requirement,
        "location": _v2_location(job.get("location")),
        "job_type": _v2_job_type(job.get("employment_type"), job.get("location"), bool(job.get("remote"))),
        "seniority": _v2_seniority(job.get("seniority")),
        "education": _v2_job_education(job),
        "required_certifications": _as_text_list(job.get("required_certifications")),
        "source_language": translated.source_language,
        "prepared_text": prepared["prepared_text"],
        "prepared_text_en": translated.text,
        "preprocess_warnings": prepared["preprocess_warnings"],
        "translation_warnings": translated.warnings,
        "text_quality": prepared["text_quality"],
    }


def _upsert_candidate_embeddings(cur: psycopg.Cursor, cv_id: int, payload: dict[str, Any]) -> list[str]:
    try:
        title_vec = _embed(payload["title"])
        skills_vec = _embed(" ".join(payload["skills"]))
        summary_vec = _embed(payload["summary"])
        experience_vec = _embed(payload["experience"])
    except MiniLMUnavailableError:
        cur.execute("DELETE FROM candidate_embeddings_v2 WHERE cv_id = %s", (cv_id,))
        return ["embedding_unavailable"]

    cur.execute(
        """
        INSERT INTO candidate_embeddings_v2 (cv_id, emb_title, emb_skills, emb_summary, emb_experience)
        VALUES (%s, %s::vector, %s::vector, %s::vector, %s::vector)
        ON CONFLICT (cv_id) DO UPDATE
        SET emb_title = EXCLUDED.emb_title,
            emb_skills = EXCLUDED.emb_skills,
            emb_summary = EXCLUDED.emb_summary,
            emb_experience = EXCLUDED.emb_experience
        """,
        (
            cv_id,
            _vector_literal(title_vec),
            _vector_literal(skills_vec),
            _vector_literal(summary_vec),
            _vector_literal(experience_vec),
        ),
    )
    return []


def _upsert_job_embeddings(cur: psycopg.Cursor, job_id: int, payload: dict[str, Any]) -> list[str]:
    try:
        title_vec = _embed(payload["title"])
        skills_vec = _embed(" ".join(payload["skills"]))
        requirement_vec = _embed(payload["requirement"])
    except MiniLMUnavailableError:
        cur.execute("DELETE FROM job_embeddings_v2 WHERE job_id = %s", (job_id,))
        return ["embedding_unavailable"]

    cur.execute(
        """
        INSERT INTO job_embeddings_v2 (job_id, emb_title, emb_skills, emb_requirement)
        VALUES (%s, %s::vector, %s::vector, %s::vector)
        ON CONFLICT (job_id) DO UPDATE
        SET emb_title = EXCLUDED.emb_title,
            emb_skills = EXCLUDED.emb_skills,
            emb_requirement = EXCLUDED.emb_requirement
        """,
        (
            job_id,
            _vector_literal(title_vec),
            _vector_literal(skills_vec),
            _vector_literal(requirement_vec),
        ),
    )
    return []


def _embed(text: str) -> list[float] | None:
    vector = embed_text_minilm(text)
    if vector is not None and len(vector) != EMBEDDING_DIM:
        raise MiniLMUnavailableError(f"MiniLM returned {len(vector)} dimensions; expected {EMBEDDING_DIM}.")
    return vector


def _vector_literal(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _candidate_title(cv: dict[str, Any]) -> str:
    return preprocess_text(cv.get("target_role") or cv.get("headline") or "Candidate Profile")


def _skill_names(value: Any) -> list[str]:
    names: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            raw = item.get("normalized_name") or item.get("normalizedName") or item.get("name")
        else:
            raw = item
        normalized = normalize_skill_name(raw).get("normalized_name", "unknown")
        if normalized != "unknown" and normalized not in names:
            names.append(normalized)
    return names


def _certification_names(value: Any) -> list[str]:
    names: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            raw = item.get("name")
        else:
            raw = item
        text = preprocess_text(raw)
        if text:
            names.append(text)
    return names


def _v2_location(value: Any) -> str:
    if isinstance(value, dict):
        raw = " ".join(str(item or "") for item in (value.get("city"), value.get("state"), value.get("country")))
    else:
        raw = str(value or "")
    lookup = _ascii_lookup(raw)
    if "ha noi" in lookup or "hanoi" in lookup:
        return "Hà Nội"
    if "ho chi minh" in lookup or "hcm" in lookup or "sai gon" in lookup or "saigon" in lookup:
        return "TP. Hồ Chí Minh"
    if "da nang" in lookup or "danang" in lookup:
        return "Đà Nẵng"
    return "Hà Nội"


def _v2_job_type(employment_type: Any, location: Any, remote_flag: bool) -> str:
    remote_type = ""
    if isinstance(location, dict):
        remote_type = str(location.get("remote_type") or location.get("remoteType") or "")
    if remote_flag or _ascii_lookup(remote_type) == "remote":
        return "remote"
    employment = {_ascii_lookup(item) for item in _as_list(employment_type)}
    if "parttime" in employment or "part time" in employment:
        return "parttime"
    return "fulltime"


def _v2_seniority(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    mapping = {
        "middle": "mid",
        "manager": "lead",
        "director": "lead",
        "unknown": "junior",
        "": "junior",
    }
    normalized = mapping.get(normalized, normalized)
    return normalized if normalized in V2_SENIORITIES else "junior"


def _v2_cv_education(value: Any) -> str:
    levels: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            levels.append(str(item.get("level") or item.get("degree") or ""))
        else:
            levels.append(str(item))
    return _v2_education(max(levels, key=len) if levels else "")


def _v2_job_education(job: dict[str, Any]) -> str:
    required = job.get("required_education") or job.get("requiredEducation") or {}
    if isinstance(required, dict):
        raw = required.get("level") or required.get("degree")
    else:
        raw = required
    return _v2_education(raw or job.get("education_level") or job.get("educationLevel"))


def _v2_education(value: Any) -> str:
    normalized = normalize_education_level(value)
    mapping = {
        "high_school": "high_school",
        "vocational": "high_school",
        "associate": "bachelor",
        "bachelor": "bachelor",
        "master": "master",
        "phd": "phd",
        "certificate": "high_school",
        "unknown": "high_school",
    }
    return mapping.get(normalized, "high_school")


def _as_text_list(value: Any) -> list[str]:
    return [text for text in (preprocess_text(item) for item in _as_list(value)) if text]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


def _ascii_lookup(value: Any) -> str:
    import unicodedata

    raw = str(value or "").strip().lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", raw)
    ascii_text = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(ascii_text.replace("_", " ").replace("-", " ").split())
