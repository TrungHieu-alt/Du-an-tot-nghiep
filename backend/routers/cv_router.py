"""Normal CV APIs backed by PostgreSQL.

CVs are owned by authenticated users. They can be created manually or via PDF
upload; uploaded PDFs are stored as file metadata in the `cvs.file` JSONB
column. This router does not parse PDFs unless a parser is added later.
"""

from __future__ import annotations

import math
import re
import shutil
import tempfile
import unicodedata
import uuid
from pathlib import Path
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Body, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile, status
from fastapi.encoders import jsonable_encoder
from jose import JWTError, jwt
from psycopg.types.json import Jsonb

from core.normalizers import (
    as_text_list,
    normalize_cv_payload,
    normalize_education_level,
    normalize_employment_types,
    normalize_industry,
    normalize_language_level,
    normalize_occupation_group,
    normalize_seniority,
    normalize_skill_name,
    normalize_status,
)
from routers.auth import (
    AuthUser,
    get_current_user,
    get_db_connection,
    _get_user_by_id,
    _jwt_algorithm,
    _jwt_secret_key,
)
from schemas.normal_cv_schema import (
    CVSearchListItem,
    CVSearchListResponse,
    CvCreateRequest,
    CvExtractPreview,
    CvExtractResponse,
    CvResponse,
    CvUpdateRequest,
)
from schemas.normal_job_schema import LocationPayload


router = APIRouter(prefix="/cv", tags=["normal-cv"])
cvs_router = APIRouter(prefix="/cvs", tags=["normal-cv-management"])

DbConnection = Annotated[psycopg.Connection, Depends(get_db_connection)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

CV_COLUMNS = [
    "id",
    "created_by",
    "avatar_url",
    "fullname",
    "preferred_name",
    "email",
    "phone",
    "location",
    "headline",
    "summary",
    "industry",
    "occupation_group",
    "career_level",
    "years_of_experience",
    "target_role",
    "employment_type",
    "salary_expectation",
    "availability",
    "skills",
    "tools_and_technologies",
    "domain_knowledge",
    "experiences",
    "education",
    "projects",
    "certifications",
    "languages",
    "portfolio",
    "references",
    "status",
    "visibility",
    "tags",
    "version",
    "file",
    "archived",
    "embedding",
    "created_at",
    "updated_at",
]

INSERTABLE_CV_COLUMNS = [
    "created_by",
    "avatar_url",
    "fullname",
    "preferred_name",
    "email",
    "phone",
    "location",
    "headline",
    "summary",
    "industry",
    "occupation_group",
    "career_level",
    "years_of_experience",
    "target_role",
    "employment_type",
    "salary_expectation",
    "availability",
    "skills",
    "tools_and_technologies",
    "domain_knowledge",
    "experiences",
    "education",
    "projects",
    "certifications",
    "languages",
    "portfolio",
    "references",
    "status",
    "visibility",
    "tags",
    "version",
    "file",
    "archived",
    "embedding",
]

JSON_COLUMNS = {
    "location",
    "skills",
    "experiences",
    "education",
    "projects",
    "certifications",
    "languages",
    "portfolio",
    "references",
    "file",
    "embedding",
}

JSON_ARRAY_COLUMNS = {
    "skills",
    "experiences",
    "education",
    "projects",
    "certifications",
    "languages",
    "portfolio",
    "references",
}

UPLOAD_DIR = Path("uploads/cvs")
MAX_EXTRACT_PDF_BYTES = 8 * 1024 * 1024


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    raw = str(value).strip().lower()
    decomposed = unicodedata.normalize("NFD", raw)
    ascii_text = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9_+\-.#]+", " ", ascii_text)
    return re.sub(r"\s+", " ", normalized).strip()


def _split_values(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        _normalize_text(item)
        for item in re.split(r"[,;]", value)
        if _normalize_text(item)
    ]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return []


def _encode_column_value(column: str, value: Any) -> Any:
    if column in JSON_ARRAY_COLUMNS:
        return Jsonb(value if value is not None else [])
    if column in JSON_COLUMNS:
        return Jsonb(value if value is not None else {})
    return value


def _dump_payload(payload: CvCreateRequest | CvUpdateRequest, *, partial: bool) -> dict[str, Any]:
    data = payload.model_dump(
        mode="json",
        exclude_unset=partial,
        by_alias=False,
    )
    for field in JSON_ARRAY_COLUMNS:
        if field in data and data[field] is None:
            data[field] = []
    if "location" in data and data["location"] is None:
        data["location"] = {}
    if "embedding" in data and data["embedding"] is None:
        data["embedding"] = {}
    return data


def _select_sql() -> str:
    return ", ".join(_sql_column(column) for column in CV_COLUMNS)


def _sql_column(column: str) -> str:
    return '"references"' if column == "references" else column


def _row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    data = dict(zip(CV_COLUMNS, row, strict=True))
    data["id"] = str(data["id"])
    data["created_by"] = str(data["created_by"])
    data["employment_type"] = _as_list(data.get("employment_type"))
    data["tags"] = _as_list(data.get("tags"))
    data["tools_and_technologies"] = _as_list(data.get("tools_and_technologies"))
    data["domain_knowledge"] = _as_list(data.get("domain_knowledge"))
    data["location"] = data.get("location") or {}
    data["skills"] = data.get("skills") or []
    data["experiences"] = data.get("experiences") or []
    data["education"] = data.get("education") or []
    data["projects"] = data.get("projects") or []
    data["certifications"] = data.get("certifications") or []
    data["languages"] = data.get("languages") or []
    data["portfolio"] = data.get("portfolio") or []
    data["references"] = data.get("references") or []
    data["file"] = data.get("file") or {}
    data["embedding"] = data.get("embedding") or {}
    data["industry"] = data.get("industry") or "unknown"
    data["occupation_group"] = data.get("occupation_group") or "unknown"
    data["career_level"] = data.get("career_level") or "unknown"
    data["years_of_experience"] = float(data.get("years_of_experience") or 0)
    data["visibility"] = data.get("visibility") or "private"
    data["archived"] = bool(data.get("archived", False))
    return data


CAMEL_TO_SNAKE = {
    "avatarUrl": "avatar_url",
    "preferredName": "preferred_name",
    "createdBy": "created_by",
    "occupationGroup": "occupation_group",
    "careerLevel": "career_level",
    "yearsOfExperience": "years_of_experience",
    "targetRole": "target_role",
    "employmentType": "employment_type",
    "salaryExpectation": "salary_expectation",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
    "companyWebsite": "company_website",
    "normalizedName": "normalized_name",
    "isCurrent": "is_current",
    "teamSize": "team_size",
    "skillsUsed": "skills_used",
    "toolsUsed": "tools_used",
    "techStack": "tech_stack",
    "toolsAndTechnologies": "tools_and_technologies",
    "domainKnowledge": "domain_knowledge",
    "issueDate": "issue_date",
    "expiryDate": "expiry_date",
    "credentialUrl": "credential_url",
    "mediaType": "media_type",
    "uploadedAt": "uploaded_at",
    "remoteType": "remote_type",
    "from": "from_",
}

SNAKE_TO_CAMEL = {value: key for key, value in CAMEL_TO_SNAKE.items()}


def _camelize(value: Any) -> Any:
    if isinstance(value, list):
        return [_camelize(item) for item in value]
    if isinstance(value, dict):
        return {SNAKE_TO_CAMEL.get(key, key): _camelize(item) for key, item in value.items()}
    return value


def _snakeize(value: Any) -> Any:
    if isinstance(value, list):
        return [_snakeize(item) for item in value]
    if isinstance(value, dict):
        return {CAMEL_TO_SNAKE.get(key, key): _snakeize(item) for key, item in value.items()}
    return value


def _cv_to_camel(cv: CvResponse | dict[str, Any]) -> dict[str, Any]:
    raw = cv.model_dump(mode="json") if isinstance(cv, CvResponse) else cv
    return _camelize(jsonable_encoder(raw))


SECTION_ALIASES = {
    "summary": {"summary", "objective", "profile", "about me", "career objective"},
    "skills": {"skills", "technical skills", "core skills", "competencies"},
    "experiences": {"experience", "work experience", "employment", "professional experience"},
    "education": {"education", "academic background"},
    "projects": {"projects", "personal projects"},
    "certifications": {"certifications", "certificates", "licenses"},
    "languages": {"languages", "language"},
    "references": {"references", "reference"},
}


def _validate_pdf_upload(file: UploadFile, content: bytes) -> None:
    filename = file.filename or ""
    content_type = file.content_type or ""
    if len(content) > MAX_EXTRACT_PDF_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="PDF file is too large")
    if content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")


def _extract_text_with_docling(pdf_path: Path) -> str | None:
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
    except Exception:
        return None
    try:
        result = DocumentConverter().convert(str(pdf_path))
        document = getattr(result, "document", None)
        if document and hasattr(document, "export_to_markdown"):
            return str(document.export_to_markdown()).strip()
        if document and hasattr(document, "export_to_text"):
            return str(document.export_to_text()).strip()
    except Exception:
        return None
    return None


def _extract_text_with_pymupdf(pdf_path: Path) -> str | None:
    try:
        import fitz  # type: ignore
    except Exception:
        return None
    try:
        with fitz.open(str(pdf_path)) as doc:
            return "\n".join(page.get_text("text") for page in doc).strip()
    except Exception:
        return None


def _extract_text_with_pdfplumber(pdf_path: Path) -> str | None:
    try:
        import pdfplumber  # type: ignore
    except Exception:
        return None
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages).strip()
    except Exception:
        return None


def _extract_pdf_text(content: bytes) -> tuple[str, list[str]]:
    warnings: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "cv.pdf"
        pdf_path.write_bytes(content)
        for label, extractor in (
            ("Docling", _extract_text_with_docling),
            ("PyMuPDF", _extract_text_with_pymupdf),
            ("pdfplumber", _extract_text_with_pdfplumber),
        ):
            text = extractor(pdf_path)
            if text:
                if label != "Docling":
                    warnings.append(f"Docling unavailable or failed; used local {label} fallback.")
                return text, warnings
        warnings.append("No local PDF text extractor succeeded. Install Docling, PyMuPDF, or pdfplumber for PDF text extraction.")
    return "", warnings


def _clean_lines(text: str) -> list[str]:
    return [line.strip(" \t-•*") for line in text.splitlines() if line.strip(" \t-•*")]


def _detect_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = "header"
    sections[current] = []
    reverse_aliases = {
        alias: section
        for section, aliases in SECTION_ALIASES.items()
        for alias in aliases
    }
    for line in lines:
        normalized = _normalize_text(line).strip(":")
        if normalized in reverse_aliases and len(normalized) <= 32:
            current = reverse_aliases[normalized]
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return match.group(0).strip() if match else ""


def _extract_portfolio(text: str) -> list[dict[str, str]]:
    urls = re.findall(r"https?://[^\s)>\]]+", text)
    return [{"media_type": "other", "url": url.rstrip(".,;"), "description": ""} for url in dict.fromkeys(urls)]


def _extract_skills(section_lines: list[str]) -> list[dict[str, Any]]:
    raw = " ".join(section_lines)
    values = [
        item.strip(" .")
        for item in re.split(r"[,;|•\n]", raw)
        if item.strip(" .") and len(item.strip(" .")) <= 80
    ]
    return [{"name": value, "level": None, "category": None, "years": None} for value in dict.fromkeys(values)]


def _extract_simple_items(section_lines: list[str], key: str) -> list[dict[str, Any]]:
    return [{key: line} for line in section_lines if line]


def _extract_experiences(section_lines: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for line in section_lines:
        if not line:
            continue
        title, _, company = line.partition(" at ")
        items.append(
            {
                "id": "",
                "title": title.strip(),
                "company": company.strip(),
                "company_website": "",
                "location": "",
                "from": None,
                "to": None,
                "is_current": False,
                "employment_type": "",
                "team_size": None,
                "responsibilities": [] if company else [line],
                "achievements": [],
                "skills_used": [],
                "tools_used": [],
                "tags": [],
            }
        )
    return items


def _rule_based_cv_extract(text: str) -> tuple[dict[str, Any], list[str]]:
    lines = _clean_lines(text)
    sections = _detect_sections(lines)
    header = sections.get("header", [])
    full_text = "\n".join(lines)
    email = _first_match(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", full_text)
    phone = _first_match(r"(?:\+?\d[\d\s().-]{7,}\d)", full_text)
    fullname = header[0] if header else ""
    if fullname and ((email and email in fullname) or (phone and phone in fullname) or "http" in fullname.lower()):
        fullname = ""
    skills = _extract_skills(sections.get("skills", []))
    summary_lines = sections.get("summary", [])
    summary = "\n".join(summary_lines[:4])
    headline = ""
    target_role = ""
    for line in header[1:4]:
        if line != email and line != phone and "http" not in line.lower():
            headline = line
            target_role = line
            break
    cv = {
        "avatar_url": "",
        "fullname": fullname,
        "preferred_name": "",
        "email": email,
        "phone": phone,
        "location": {"city": "", "state": "", "country": ""},
        "headline": headline,
        "summary": summary,
        "industry": "",
        "occupation_group": "",
        "career_level": "",
        "years_of_experience": None,
        "target_role": target_role,
        "employment_type": [full_text],
        "salary_expectation": "",
        "availability": "",
        "skills": skills,
        "tools_and_technologies": [],
        "domain_knowledge": [],
        "experiences": _extract_experiences(sections.get("experiences", [])),
        "education": _extract_simple_items(sections.get("education", []), "school"),
        "projects": _extract_simple_items(sections.get("projects", []), "name"),
        "certifications": _extract_simple_items(sections.get("certifications", []), "name"),
        "languages": _extract_simple_items(sections.get("languages", []), "name"),
        "portfolio": _extract_portfolio(full_text),
        "references": _extract_simple_items(sections.get("references", []), "name"),
        "status": "draft",
        "tags": [skill["name"] for skill in skills[:8]],
        "version": 1,
        "file": None,
    }
    warnings = ["Used deterministic rule-based CV parser; review extracted fields before saving."]
    missing_checks = [
        ("fullname", "fullname missing"),
        ("email", "email missing"),
        ("phone", "phone missing"),
    ]
    for key, warning in missing_checks:
        if not cv.get(key):
            warnings.append(warning)
    for key, warning in (
        ("skills", "skills empty"),
        ("experiences", "experiences empty"),
        ("education", "education empty"),
    ):
        if not cv.get(key):
            warnings.append(warning)
    return cv, warnings


def _fetch_cv(conn: psycopg.Connection, cv_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM cvs
            WHERE id = %s::uuid
            """,
            (cv_id,),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def _require_owner(cv: dict[str, Any], user: AuthUser) -> None:
    if cv["created_by"] != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")


def _is_public_cv(cv: dict[str, Any]) -> bool:
    return (
        cv.get("status") == "published"
        and cv.get("visibility") == "public"
        and not cv.get("archived")
    )


def _optional_user_from_authorization(
    authorization: str | None,
    conn: psycopg.Connection,
) -> AuthUser | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = jwt.decode(token, _jwt_secret_key(), algorithms=[_jwt_algorithm()])
        subject = payload.get("sub")
        if not isinstance(subject, str):
            raise JWTError("missing subject")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    user = _get_user_by_id(conn, subject)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _can_read_cv(cv: dict[str, Any], user: AuthUser | None) -> bool:
    if _is_public_cv(cv):
        return True
    if user is None:
        return False
    return cv["created_by"] == user.id or user.role == "admin"


def _skill_names(skills: Any) -> list[str]:
    names: list[str] = []
    if isinstance(skills, list):
        for item in skills:
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    names.append(str(name))
                normalized_name = item.get("normalized_name")
                if normalized_name and normalized_name != name:
                    names.append(str(normalized_name))
            elif item:
                names.append(str(item))
    return names


def _cert_names(certifications: Any) -> list[str]:
    names: list[str] = []
    if isinstance(certifications, list):
        for item in certifications:
            if isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
            elif item:
                names.append(str(item))
    return names


def _experience_text(experiences: Any) -> str:
    parts: list[str] = []
    if isinstance(experiences, list):
        for item in experiences:
            if isinstance(item, dict):
                parts.extend(
                    str(value)
                    for value in [
                        item.get("title"),
                        item.get("company"),
                        " ".join(item.get("responsibilities") or []),
                        " ".join(item.get("achievements") or []),
                    ]
                    if value
                )
            elif item:
                parts.append(str(item))
    return " ".join(parts)


def _education_text(education: Any) -> str:
    parts: list[str] = []
    if isinstance(education, list):
        for item in education:
            if isinstance(item, dict):
                parts.extend(
                    str(value)
                    for value in [
                        item.get("degree"),
                        item.get("major"),
                        item.get("school"),
                    ]
                    if value
                )
            elif item:
                parts.append(str(item))
    return " ".join(parts)


def _project_text(projects: Any) -> str:
    parts: list[str] = []
    if isinstance(projects, list):
        for item in projects:
            if isinstance(item, dict):
                parts.extend(
                    str(value)
                    for value in [
                        item.get("name"),
                        item.get("description"),
                        item.get("role"),
                        " ".join(item.get("techStack") or item.get("tech_stack") or []),
                        " ".join(item.get("tools") or []),
                        " ".join(item.get("skillsUsed") or item.get("skills_used") or []),
                        " ".join(item.get("outcomes") or []),
                        " ".join(item.get("metrics") or []),
                    ]
                    if value
                )
            elif item:
                parts.append(str(item))
    return " ".join(parts)


def _language_text(languages: Any) -> str:
    parts: list[str] = []
    if isinstance(languages, list):
        for item in languages:
            if isinstance(item, dict):
                parts.extend(str(value) for value in [item.get("name"), item.get("level")] if value)
            elif item:
                parts.append(str(item))
    return " ".join(parts)


def _location_city(cv: dict[str, Any]) -> str:
    location = cv.get("location") or {}
    if isinstance(location, dict):
        city = location.get("city")
        if city:
            return str(city)
    return ""


def _job_type(cv: dict[str, Any]) -> str:
    employment = cv.get("employment_type") or []
    return employment[0] if employment else ""


def _working_model(cv: dict[str, Any]) -> str | None:
    location = cv.get("location") or {}
    if isinstance(location, dict) and location.get("remote_type"):
        return str(location["remote_type"])
    return None


def _join_search_values(values: list[Any]) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            parts.append(str(value))
    return _normalize_text(" ".join(parts))


def _search_text(cv: dict[str, Any]) -> str:
    return _join_search_values(
        [
            cv.get("fullname"),
            cv.get("preferred_name"),
            cv.get("headline"),
            cv.get("summary"),
            cv.get("industry"),
            cv.get("occupation_group"),
            cv.get("career_level"),
            cv.get("target_role"),
            cv.get("tools_and_technologies"),
            cv.get("domain_knowledge"),
            _skill_names(cv.get("skills")),
            _experience_text(cv.get("experiences")),
            _education_text(cv.get("education")),
            _project_text(cv.get("projects")),
            _cert_names(cv.get("certifications")),
            _language_text(cv.get("languages")),
            cv.get("tags"),
            _location_city(cv),
        ]
    )


def _matches_query(search_text: str, query: str | None) -> bool:
    normalized = _normalize_text(query)
    if not normalized:
        return True
    compact_query = normalized.replace(" ", "")
    compact_text = search_text.replace(" ", "")
    if compact_query and compact_query in compact_text:
        return True
    return all(token in search_text for token in normalized.split())


def _contains_any(values: list[str], terms: list[str]) -> bool:
    if not terms:
        return True
    normalized_values = {_normalize_text(value) for value in values}
    return any(
        any(term in value or value in term for value in normalized_values)
        for term in terms
    )


def _contains_normalized(values: list[str], terms: list[str]) -> bool:
    if not terms:
        return True
    normalized_values = {_normalize_text(value) for value in values}
    return any(term in normalized_values or any(term in value or value in term for value in normalized_values) for term in terms)


def _matches_number_range(value: Any, minimum: float | None, maximum: float | None) -> bool:
    if minimum is None and maximum is None:
        return True
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    if minimum is not None and number < minimum:
        return False
    if maximum is not None and number > maximum:
        return False
    return True


def _education_values(education: Any, key: str) -> list[str]:
    values: list[str] = []
    if isinstance(education, list):
        for item in education:
            if not isinstance(item, dict):
                continue
            if key == "level":
                source = item.get("level")
                if source:
                    values.append(normalize_education_level(source))
                    continue
                fallback = " ".join(str(item.get(field) or "") for field in ("degree", "major", "school"))
                inferred = normalize_education_level(fallback)
                if inferred != "unknown":
                    values.append(inferred)
                continue
            if item.get(key):
                values.append(str(item[key]))
    return values


def _education_filter_values(value: str | None) -> list[str]:
    return [normalize_education_level(item) for item in as_text_list(value)]


def _skill_filter_values(value: str | None) -> list[str]:
    normalized: list[str] = []
    for item in as_text_list(value):
        skill_key = normalize_skill_name(item).get("normalized_name") or _normalize_text(item)
        if skill_key and skill_key not in normalized:
            normalized.append(skill_key)
    return normalized


def _language_matches(languages: Any, name: str | None, level: str | None) -> bool:
    if not name and not level:
        return True
    wanted_name = _normalize_text(name)
    wanted_level = normalize_language_level(level) if level else None
    if not isinstance(languages, list):
        return False
    for item in languages:
        if not isinstance(item, dict):
            continue
        name_ok = not wanted_name or wanted_name in _normalize_text(item.get("name"))
        level_ok = not wanted_level or item.get("level") == wanted_level
        if name_ok and level_ok:
            return True
    return False


def _matches_cv_filters(
    cv: dict[str, Any],
    *,
    keyword: str | None,
    fullname: str | None,
    headline: str | None,
    target_role: str | None,
    location: str | None,
    location_country: str | None,
    desired_industry: str | None,
    occupation_group: str | None,
    status_filter: str | None,
    experience_level: str | None,
    years_of_experience_min: float | None,
    years_of_experience_max: float | None,
    education_level: str | None,
    education_major: str | None,
    working_model: str | None,
    employment_type: str | None,
    availability: str | None,
    skills: str | None,
    tools_and_technologies: str | None,
    domain_knowledge: str | None,
    certification_name: str | None,
    language_name: str | None,
    language_level: str | None,
    tags: str | None,
) -> bool:
    text = _search_text(cv)
    location_obj = cv.get("location") if isinstance(cv.get("location"), dict) else {}
    if not _matches_query(text, keyword):
        return False
    if fullname and not _matches_query(_normalize_text(cv.get("fullname")), fullname):
        return False
    if headline and not _matches_query(_normalize_text(cv.get("headline")), headline):
        return False
    if target_role and not _matches_query(_normalize_text(cv.get("target_role")), target_role):
        return False
    if location and not _matches_query(_normalize_text(location_obj.get("city")), location):
        return False
    if location_country and not _matches_query(_normalize_text(location_obj.get("country")), location_country):
        return False
    if desired_industry and cv.get("industry") != normalize_industry(desired_industry):
        return False
    if occupation_group and cv.get("occupation_group") != normalize_occupation_group(occupation_group):
        return False
    if status_filter and cv.get("status") != normalize_status(status_filter, "cv"):
        return False
    if experience_level and cv.get("career_level") not in [normalize_seniority(item) for item in as_text_list(experience_level)]:
        return False
    if not _matches_number_range(cv.get("years_of_experience"), years_of_experience_min, years_of_experience_max):
        return False
    education_filters = _education_filter_values(education_level)
    if education_filters and not set(education_filters).intersection(_education_values(cv.get("education"), "level")):
        return False
    if education_major and not _contains_normalized(_education_values(cv.get("education"), "major"), _split_values(education_major)):
        return False
    if working_model and not _matches_query(_normalize_text(location_obj.get("remote_type")), working_model):
        return False
    if not _contains_normalized(cv.get("employment_type") or [], normalize_employment_types(employment_type) if employment_type else []):
        return False
    if availability and not _matches_query(_normalize_text(cv.get("availability")), availability):
        return False
    if not _contains_normalized(_skill_names(cv.get("skills")), _skill_filter_values(skills)):
        return False
    if not _contains_normalized(cv.get("tools_and_technologies") or [], _split_values(tools_and_technologies)):
        return False
    if not _contains_normalized(cv.get("domain_knowledge") or [], _split_values(domain_knowledge)):
        return False
    if not _contains_normalized(_cert_names(cv.get("certifications")), _split_values(certification_name)):
        return False
    if not _language_matches(cv.get("languages"), language_name, language_level):
        return False
    if not _contains_any(cv.get("tags") or [], _split_values(tags)):
        return False
    return True


def _to_search_item(cv: dict[str, Any]) -> CVSearchListItem:
    title = cv.get("target_role") or cv.get("headline") or cv.get("fullname") or "CV"
    return CVSearchListItem(
        id=cv["id"],
        cv_id=cv["id"],
        title=title,
        fullname=cv.get("fullname") or "",
        industry=cv.get("industry") or "unknown",
        occupation_group=cv.get("occupation_group") or "unknown",
        career_level=cv.get("career_level") or "unknown",
        years_of_experience=float(cv.get("years_of_experience") or 0),
        location=_location_city(cv),
        location_detail=cv.get("location") or {},
        job_type=_job_type(cv),
        employment_type=cv.get("employment_type") or [],
        working_model=_working_model(cv),
        seniority=cv.get("career_level"),
        education=_join_search_values([cv.get("education")]),
        skills=_skill_names(cv.get("skills")),
        summary=cv.get("summary") or "",
        experience=_experience_text(cv.get("experiences")),
        certifications=_cert_names(cv.get("certifications")),
        target_role=cv.get("target_role"),
        availability=cv.get("availability"),
        tools_and_technologies=cv.get("tools_and_technologies") or [],
        domain_knowledge=cv.get("domain_knowledge") or [],
        file=cv.get("file") or {},
    )


def _load_searchable_cvs(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM cvs
            WHERE status = 'published'
              AND visibility = 'public'
              AND archived = false
            """
        )
        rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]


def search_cvs_response(
    conn: psycopg.Connection,
    *,
    keyword: str | None = None,
    q: str | None = None,
    fullname: str | None = None,
    headline: str | None = None,
    target_role: str | None = None,
    targetRole: str | None = None,
    location: str | None = None,
    location_city: str | None = None,
    location_country: str | None = None,
    desired_industry: str | None = None,
    desiredIndustry: str | None = None,
    occupation_group: str | None = None,
    status_filter: str | None = None,
    experience_level: str | None = None,
    experienceLevel: str | None = None,
    years_of_experience_min: float | None = None,
    years_of_experience_max: float | None = None,
    education_level: str | None = None,
    educationLevel: str | None = None,
    education_major: str | None = None,
    working_model: str | None = None,
    workingModel: str | None = None,
    employment_type: str | None = None,
    employmentType: str | None = None,
    availability: str | None = None,
    skills: str | None = None,
    tools_and_technologies: str | None = None,
    domain_knowledge: str | None = None,
    certification_name: str | None = None,
    language_name: str | None = None,
    language_level: str | None = None,
    tags: str | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str | None = "newest",
) -> CVSearchListResponse:
    selected_keyword = keyword or q
    selected_industry = desired_industry or desiredIndustry
    selected_experience = experience_level or experienceLevel
    selected_education = education_level or educationLevel
    selected_working_model = working_model or workingModel
    selected_target_role = target_role or targetRole
    selected_location = location_city or location
    selected_employment_type = employment_type or employmentType
    cvs = [
        cv
        for cv in _load_searchable_cvs(conn)
        if _is_public_cv(cv)
        and _matches_cv_filters(
            cv,
            keyword=selected_keyword,
            fullname=fullname,
            headline=headline,
            target_role=selected_target_role,
            location=selected_location,
            location_country=location_country,
            desired_industry=selected_industry,
            occupation_group=occupation_group,
            status_filter=status_filter,
            experience_level=selected_experience,
            years_of_experience_min=years_of_experience_min,
            years_of_experience_max=years_of_experience_max,
            education_level=selected_education,
            education_major=education_major,
            working_model=selected_working_model,
            employment_type=selected_employment_type,
            availability=availability,
            skills=skills,
            tools_and_technologies=tools_and_technologies,
            domain_knowledge=domain_knowledge,
            certification_name=certification_name,
            language_name=language_name,
            language_level=language_level,
            tags=tags,
        )
    ]
    key = _normalize_text(sort or "createdAt_desc")
    if key in {"createdat_asc", "oldest"}:
        ordered = sorted(cvs, key=lambda item: item["created_at"])
    elif key == "updatedat_asc":
        ordered = sorted(cvs, key=lambda item: item["updated_at"])
    elif key == "updatedat_desc":
        ordered = sorted(cvs, key=lambda item: item["updated_at"], reverse=True)
    elif key == "yearsofexperience_desc":
        ordered = sorted(cvs, key=lambda item: float(item.get("years_of_experience") or 0), reverse=True)
    elif key == "yearsofexperience_asc":
        ordered = sorted(cvs, key=lambda item: float(item.get("years_of_experience") or 0))
    elif key == "fullname_asc":
        ordered = sorted(cvs, key=lambda item: _normalize_text(item.get("fullname")))
    elif key == "fullname_desc":
        ordered = sorted(cvs, key=lambda item: _normalize_text(item.get("fullname")), reverse=True)
    else:
        ordered = sorted(cvs, key=lambda item: item["created_at"], reverse=True)
    total = len(ordered)
    start = (page - 1) * limit
    paged = ordered[start : start + limit]
    total_pages = math.ceil(total / limit) if total else 0
    return CVSearchListResponse(
        items=[_to_search_item(cv) for cv in paged],
        total=total,
        page=page,
        limit=limit,
        totalPages=total_pages,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages,
        },
    )


def _insert_cv(conn: psycopg.Connection, data: dict[str, Any]) -> CvResponse:
    columns = INSERTABLE_CV_COLUMNS
    values = [_encode_column_value(column, data.get(column)) for column in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO cvs ({", ".join(_sql_column(column) for column in columns)})
                VALUES ({placeholders})
                RETURNING {_select_sql()}
                """,
                tuple(values),
            )
            row = cur.fetchone()
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return CvResponse(**_row_to_dict(row))


@router.post("", response_model=CvResponse, status_code=status.HTTP_201_CREATED)
def create_cv(payload: CvCreateRequest, conn: DbConnection, user: CurrentUser) -> CvResponse:
    data = _dump_payload(payload, partial=False)
    data = normalize_cv_payload(data, for_create=True, include_missing=True)
    data["created_by"] = user.id
    data["file"] = {}
    return _insert_cv(conn, data)


@router.post("/upload", response_model=CvResponse, status_code=status.HTTP_201_CREATED)
def upload_cv_pdf(
    conn: DbConnection,
    user: CurrentUser,
    file: UploadFile = File(...),
    fullname: str | None = Form(default=None),
) -> CvResponse:
    filename = file.filename or ""
    content_type = file.content_type or ""
    if content_type != "application/pdf" or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    head = file.file.read(4)
    file.file.seek(0)
    if head != b"%PDF":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF files are accepted")

    target_dir = UPLOAD_DIR / user.id
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4()}.pdf"
    target_path = target_dir / safe_name
    with target_path.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)
    size = target_path.stat().st_size

    metadata = {
        "filename": safe_name,
        "originalname": filename,
        "path": str(target_path),
        "mimetype": content_type,
        "size": size,
        "uploaded_at": None,
    }
    data: dict[str, Any] = {
        "created_by": user.id,
        "fullname": (fullname or "").strip(),
        "location": LocationPayload().model_dump(mode="json"),
        "industry": "",
        "occupation_group": "",
        "career_level": "",
        "years_of_experience": None,
        "employment_type": [],
        "skills": [],
        "tools_and_technologies": [],
        "domain_knowledge": [],
        "experiences": [],
        "education": [],
        "projects": [],
        "certifications": [],
        "languages": [],
        "portfolio": [],
        "references": [],
        "status": "draft",
        "visibility": "private",
        "tags": [],
        "version": 1,
        "file": metadata,
        "archived": False,
    }
    data = normalize_cv_payload(data, for_create=True, include_missing=True)
    cv = _insert_cv(conn, data)
    cv.file["uploaded_at"] = cv.created_at.isoformat()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE cvs
                SET file = %s
                WHERE id = %s::uuid
                RETURNING {_select_sql()}
                """,
                (Jsonb(cv.file), cv.id),
            )
            row = cur.fetchone()
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return CvResponse(**_row_to_dict(row))


@router.get("/my", response_model=list[CvResponse])
def list_my_cvs(conn: DbConnection, user: CurrentUser) -> list[CvResponse]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM cvs
            WHERE created_by = %s::uuid
            ORDER BY created_at DESC
            """,
            (user.id,),
        )
        rows = cur.fetchall()
    return [CvResponse(**_row_to_dict(row)) for row in rows]


@router.get("/search", response_model=CVSearchListResponse)
def search_cvs(
    conn: DbConnection,
    q: str | None = Query(default=None, max_length=200),
    keyword: str | None = Query(default=None, max_length=200),
    fullname: str | None = None,
    headline: str | None = None,
    target_role: str | None = None,
    targetRole: str | None = None,
    city: str | None = None,
    location_city: str | None = Query(default=None, alias="location.city"),
    location: str | None = None,
    country: str | None = None,
    locationCountry: str | None = None,
    location_country: str | None = Query(default=None, alias="location.country"),
    desiredIndustry: str | None = None,
    industry: str | None = None,
    occupationGroup: str | None = None,
    occupation_group: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    experienceLevel: str | None = None,
    careerLevel: str | None = None,
    years_of_experience_min: float | None = Query(default=None, alias="yearsOfExperienceMin", ge=0),
    years_of_experience_max: float | None = Query(default=None, alias="yearsOfExperienceMax", ge=0),
    educationLevel: str | None = None,
    education_level_alias: str | None = Query(default=None, alias="education.level"),
    educationMajor: str | None = None,
    education_major: str | None = Query(default=None, alias="education.major"),
    workingModel: str | None = None,
    employmentType: str | None = None,
    employment_type: str | None = None,
    availability: str | None = None,
    skills: str | None = None,
    toolsAndTechnologies: str | None = None,
    domainKnowledge: str | None = None,
    certifications: str | None = None,
    certification_name_alias: str | None = Query(default=None, alias="certifications.name"),
    certificationName: str | None = None,
    language_name_alias: str | None = Query(default=None, alias="languages.name"),
    languageName: str | None = None,
    language_level_alias: str | None = Query(default=None, alias="languages.level"),
    languageLevel: str | None = None,
    tags: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort: str | None = "newest",
) -> CVSearchListResponse:
    return search_cvs_response(
        conn,
        q=q,
        keyword=keyword,
        fullname=fullname,
        headline=headline,
        target_role=target_role,
        targetRole=targetRole,
        location_city=location_city or city,
        location=location,
        location_country=location_country or locationCountry or country,
        desiredIndustry=desiredIndustry or industry,
        occupation_group=occupationGroup or occupation_group,
        status_filter=status_value,
        experienceLevel=careerLevel or experienceLevel,
        years_of_experience_min=years_of_experience_min,
        years_of_experience_max=years_of_experience_max,
        educationLevel=educationLevel or education_level_alias,
        education_major=education_major or educationMajor,
        workingModel=workingModel,
        employmentType=employmentType,
        employment_type=employment_type,
        availability=availability,
        skills=skills,
        tools_and_technologies=toolsAndTechnologies,
        domain_knowledge=domainKnowledge,
        certification_name=certificationName or certification_name_alias or certifications,
        language_name=languageName or language_name_alias,
        language_level=languageLevel or language_level_alias,
        tags=tags,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/{cv_id}", response_model=CvResponse)
def get_cv(
    cv_id: str,
    conn: DbConnection,
    authorization: Annotated[str | None, Header()] = None,
) -> CvResponse:
    cv = _fetch_cv(conn, cv_id)
    user = _optional_user_from_authorization(authorization, conn)
    if cv is None or not _can_read_cv(cv, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    return CvResponse(**cv)


@router.patch("/{cv_id}", response_model=CvResponse)
def update_cv(cv_id: str, payload: CvUpdateRequest, conn: DbConnection, user: CurrentUser) -> CvResponse:
    cv = _fetch_cv(conn, cv_id)
    if cv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    _require_owner(cv, user)
    data = _dump_payload(payload, partial=True)
    if not data:
        return CvResponse(**cv)
    data = normalize_cv_payload(data, for_create=False, include_missing=False)
    allowed = [column for column in data if column in INSERTABLE_CV_COLUMNS and column != "created_by"]
    assignments = ", ".join(f"{_sql_column(column)} = %s" for column in allowed)
    values = [_encode_column_value(column, data[column]) for column in allowed]
    values.extend([cv_id, user.id])
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE cvs
                SET {assignments}
                WHERE id = %s::uuid
                  AND created_by = %s::uuid
                RETURNING {_select_sql()}
                """,
                tuple(values),
            )
            row = cur.fetchone()
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    return CvResponse(**_row_to_dict(row))


@router.delete(
    "/{cv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_cv(cv_id: str, conn: DbConnection, user: CurrentUser) -> None:
    cv = _fetch_cv(conn, cv_id)
    if cv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    _require_owner(cv, user)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM cvs
                WHERE id = %s::uuid
                  AND created_by = %s::uuid
                """,
                (cv_id, user.id),
            )
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@cvs_router.post("", status_code=status.HTTP_201_CREATED)
def create_cv_management(
    conn: DbConnection,
    user: CurrentUser,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    request = CvCreateRequest.model_validate(_snakeize(payload))
    return _cv_to_camel(create_cv(request, conn, user))


@cvs_router.post("/extract-pdf", response_model=CvExtractResponse)
async def extract_cv_pdf_preview(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> CvExtractResponse:
    content = await file.read()
    _validate_pdf_upload(file, content)
    extracted_text, extraction_warnings = _extract_pdf_text(content)
    if not extracted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Could not extract text from this PDF with local extractors.",
                "warnings": extraction_warnings,
            },
        )
    cv_data, parser_warnings = _rule_based_cv_extract(extracted_text)
    cv_data["created_by"] = user.id
    cv_data["file"] = {
        "filename": file.filename or "",
        "originalname": file.filename or "",
        "path": "",
        "mimetype": file.content_type or "application/pdf",
        "size": len(content),
        "uploaded_at": None,
    }
    cv_data = normalize_cv_payload(cv_data, include_missing=True, source_text=extracted_text)
    preview = CvExtractPreview.model_validate(cv_data)
    return CvExtractResponse(
        extractedText=extracted_text,
        cv=_camelize(preview.model_dump(mode="json")),
        warnings=extraction_warnings + parser_warnings,
    )


@cvs_router.get("/my")
def list_my_cvs_management(
    conn: DbConnection,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    return [_cv_to_camel(cv) for cv in list_my_cvs(conn, user)]


@cvs_router.get("/{cv_id}")
def get_cv_management(
    cv_id: str,
    conn: DbConnection,
    user: CurrentUser,
) -> dict[str, Any]:
    cv = _fetch_cv(conn, cv_id)
    if cv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CV not found")
    _require_owner(cv, user)
    return _cv_to_camel(CvResponse(**cv))


@cvs_router.put("/{cv_id}")
def update_cv_management(
    cv_id: str,
    conn: DbConnection,
    user: CurrentUser,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    request = CvUpdateRequest.model_validate(_snakeize(payload))
    return _cv_to_camel(update_cv(cv_id, request, conn, user))


@cvs_router.delete(
    "/{cv_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_cv_management(
    cv_id: str,
    conn: DbConnection,
    user: CurrentUser,
) -> None:
    delete_cv(cv_id, conn, user)
