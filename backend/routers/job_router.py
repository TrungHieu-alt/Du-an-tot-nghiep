"""Normal Job APIs backed by PostgreSQL.

This router is intentionally separate from Matching V2. It owns normal
recruiter job/recruitment-requirement CRUD and public multi-industry search.
"""

from __future__ import annotations

import math
import re
import unicodedata
from collections.abc import Iterable
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Response, status
from fastapi.encoders import jsonable_encoder
from jose import JWTError, jwt
from psycopg.types.json import Jsonb

from routers.auth import (
    AuthUser,
    get_current_user,
    get_db_connection,
    _get_user_by_id,
    _jwt_algorithm,
    _jwt_secret_key,
)
from schemas.normal_job_schema import (
    JobCreateRequest,
    JobResponse,
    JobSearchFiltersResponse,
    JobSearchListItem,
    JobSearchListResponse,
    JobUpdateRequest,
)


router = APIRouter(prefix="/job", tags=["normal-job"])
employer_requests_router = APIRouter(
    prefix="/employer/requests",
    tags=["normal-employer-request-management"],
)

DbConnection = Annotated[psycopg.Connection, Depends(get_db_connection)]
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]

JOB_COLUMNS = [
    "id",
    "created_by",
    "company_id",
    "title",
    "slug",
    "status",
    "visibility",
    "company_name",
    "company_logo_url",
    "company_website",
    "company_location",
    "company_size",
    "company_industry",
    "department",
    "location",
    "employment_type",
    "seniority",
    "team_size",
    "description",
    "responsibilities",
    "requirements",
    "nice_to_have",
    "skills",
    "experience_years",
    "education_level",
    "salary",
    "benefits",
    "bonus",
    "equity",
    "apply_url",
    "apply_email",
    "recruiter",
    "how_to_apply",
    "application_deadline",
    "tags",
    "categories",
    "remote",
    "views",
    "applications_count",
    "pre_screen_questions",
    "required_docs",
    "published_by",
    "approved_at",
    "approved_by",
    "archived",
    "version",
    "created_at",
    "updated_at",
]

INSERTABLE_JOB_COLUMNS = [
    "created_by",
    "company_id",
    "title",
    "slug",
    "status",
    "visibility",
    "company_name",
    "company_logo_url",
    "company_website",
    "company_location",
    "company_size",
    "company_industry",
    "department",
    "location",
    "employment_type",
    "seniority",
    "team_size",
    "description",
    "responsibilities",
    "requirements",
    "nice_to_have",
    "skills",
    "experience_years",
    "education_level",
    "salary",
    "benefits",
    "bonus",
    "equity",
    "apply_url",
    "apply_email",
    "recruiter",
    "how_to_apply",
    "application_deadline",
    "tags",
    "categories",
    "remote",
    "pre_screen_questions",
    "required_docs",
    "published_by",
    "approved_at",
    "approved_by",
    "archived",
    "version",
]

JSON_COLUMNS = {"location", "skills", "salary", "recruiter", "pre_screen_questions"}


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


def _json_value(value: Any) -> Any:
    return Jsonb(value if value is not None else {})


def _json_array_value(value: Any) -> Any:
    return Jsonb(value if value is not None else [])


def _dump_payload(payload: JobCreateRequest | JobUpdateRequest, *, partial: bool) -> dict[str, Any]:
    data = payload.model_dump(mode="json", exclude_unset=partial)
    for field in ("location", "salary", "recruiter"):
        if field in data and data[field] is None:
            data[field] = {}
    for field in ("skills", "pre_screen_questions"):
        if field in data and data[field] is None:
            data[field] = []
    return data


def _apply_create_defaults(data: dict[str, Any]) -> None:
    data["status"] = data.get("status") or "published"
    data["visibility"] = data.get("visibility") or "public"
    data["archived"] = bool(data.get("archived", False))


def _encode_column_value(column: str, value: Any) -> Any:
    if column in {"location", "salary", "recruiter"}:
        return _json_value(value)
    if column in {"skills", "pre_screen_questions"}:
        return _json_array_value(value)
    return value


def _row_to_dict(row: tuple[Any, ...]) -> dict[str, Any]:
    data = dict(zip(JOB_COLUMNS, row, strict=True))
    data["id"] = str(data["id"])
    data["created_by"] = str(data["created_by"])
    data["employment_type"] = _as_list(data.get("employment_type"))
    data["responsibilities"] = _as_list(data.get("responsibilities"))
    data["requirements"] = _as_list(data.get("requirements"))
    data["nice_to_have"] = _as_list(data.get("nice_to_have"))
    data["benefits"] = _as_list(data.get("benefits"))
    data["tags"] = _as_list(data.get("tags"))
    data["categories"] = _as_list(data.get("categories"))
    data["required_docs"] = _as_list(data.get("required_docs"))
    data["location"] = data.get("location") or {}
    data["skills"] = data.get("skills") or []
    data["salary"] = data.get("salary") or {}
    data["recruiter"] = data.get("recruiter") or {}
    data["pre_screen_questions"] = data.get("pre_screen_questions") or []
    if data.get("experience_years") is not None:
        data["experience_years"] = float(data["experience_years"])
    return data


CAMEL_TO_SNAKE = {
    "companyId": "company_id",
    "createdBy": "created_by",
    "companyName": "company_name",
    "companyLogoUrl": "company_logo_url",
    "companyWebsite": "company_website",
    "companyLocation": "company_location",
    "companySize": "company_size",
    "companyIndustry": "company_industry",
    "remoteType": "remote_type",
    "employmentType": "employment_type",
    "teamSize": "team_size",
    "niceToHave": "nice_to_have",
    "experienceYears": "experience_years",
    "educationLevel": "education_level",
    "applyUrl": "apply_url",
    "applyEmail": "apply_email",
    "howToApply": "how_to_apply",
    "applicationDeadline": "application_deadline",
    "applicationsCount": "applications_count",
    "preScreenQuestions": "pre_screen_questions",
    "requiredDocs": "required_docs",
    "publishedBy": "published_by",
    "approvedAt": "approved_at",
    "approvedBy": "approved_by",
    "createdAt": "created_at",
    "updatedAt": "updated_at",
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


def _job_to_camel(job: JobResponse | dict[str, Any]) -> dict[str, Any]:
    raw = job.model_dump(mode="json") if isinstance(job, JobResponse) else job
    return _camelize(jsonable_encoder(raw))


def _select_sql() -> str:
    return ", ".join(f"{column}" for column in JOB_COLUMNS)


def _fetch_job(conn: psycopg.Connection, job_id: str) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM jobs
            WHERE id = %s::uuid
            """,
            (job_id,),
        )
        row = cur.fetchone()
    return _row_to_dict(row) if row else None


def _is_public_job(job: dict[str, Any]) -> bool:
    return (
        job.get("status") == "published"
        and job.get("visibility") == "public"
        and not job.get("archived")
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


def _can_read_job(job: dict[str, Any], user: AuthUser | None) -> bool:
    if _is_public_job(job):
        return True
    if user is None:
        return False
    return job["created_by"] == user.id or user.role == "admin"


def _require_owner(job: dict[str, Any], user: AuthUser) -> None:
    if job["created_by"] != user.id and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


def _matches_query(search_text: str, query: str | None) -> bool:
    normalized = _normalize_text(query)
    if not normalized:
        return True
    compact_query = normalized.replace(" ", "")
    compact_text = search_text.replace(" ", "")
    if compact_query and compact_query in compact_text:
        return True
    return all(token in search_text for token in normalized.split())


def _contains_any(values: Iterable[str], wanted: list[str]) -> bool:
    if not wanted:
        return True
    normalized_values = {_normalize_text(value) for value in values}
    return any(
        any(term in value or value in term for value in normalized_values)
        for term in wanted
    )


def _skill_names(skills: Any) -> list[str]:
    names: list[str] = []
    if isinstance(skills, list):
        for item in skills:
            if isinstance(item, dict):
                name = item.get("name")
                if name:
                    names.append(str(name))
            elif item:
                names.append(str(item))
    return names


def _location_city(job: dict[str, Any]) -> str:
    location = job.get("location") or {}
    if isinstance(location, dict):
        city = location.get("city")
        if city:
            return str(city)
        remote_type = location.get("remote_type")
        if remote_type:
            return str(remote_type)
    if job.get("remote"):
        return "Remote"
    return job.get("company_location") or ""


def _working_model(job: dict[str, Any]) -> str | None:
    location = job.get("location") or {}
    if isinstance(location, dict) and location.get("remote_type"):
        return str(location["remote_type"])
    return "remote" if job.get("remote") else None


def _job_type(job: dict[str, Any]) -> str:
    if job.get("remote"):
        return "remote"
    employment = job.get("employment_type") or []
    return employment[0] if employment else ""


def _search_text(job: dict[str, Any]) -> str:
    skill_names = _skill_names(job.get("skills"))
    values: list[Any] = [
        job.get("title"),
        job.get("company_name"),
        job.get("company_industry"),
        job.get("department"),
        job.get("description"),
        job.get("requirements"),
        job.get("responsibilities"),
        skill_names,
        job.get("tags"),
        job.get("categories"),
        job.get("company_location"),
        _location_city(job),
    ]
    joined: list[str] = []
    for value in values:
        if isinstance(value, (list, tuple)):
            joined.extend(str(item) for item in value if str(item).strip())
        elif value is not None and str(value).strip():
            joined.append(str(value))
    return _normalize_text(" ".join(joined))


def _salary_number(salary: dict[str, Any], key: str) -> float | None:
    value = salary.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _matches_salary(job: dict[str, Any], salary_min: float | None, salary_max: float | None) -> bool:
    if salary_min is None and salary_max is None:
        return True
    salary = job.get("salary") or {}
    if not isinstance(salary, dict):
        return False
    job_min = _salary_number(salary, "min")
    job_max = _salary_number(salary, "max")
    if job_min is None and job_max is None:
        return False
    effective_min = job_min if job_min is not None else job_max
    effective_max = job_max if job_max is not None else job_min
    if salary_min is not None and effective_max is not None and effective_max < salary_min:
        return False
    if salary_max is not None and effective_min is not None and effective_min > salary_max:
        return False
    return True


def _matches_job_filters(
    job: dict[str, Any],
    *,
    keyword: str | None,
    title: str | None,
    company_name: str | None,
    company_industry: str | None,
    department: str | None,
    location_city: str | None,
    location_country: str | None,
    remote: bool | None,
    remote_type: str | None,
    employment_type: str | None,
    seniority: str | None,
    skills: str | None,
    categories: str | None,
    tags: str | None,
    salary_min: float | None,
    salary_max: float | None,
) -> bool:
    search_text = _search_text(job)
    location = job.get("location") if isinstance(job.get("location"), dict) else {}

    if not _matches_query(search_text, keyword):
        return False
    if title and not _matches_query(_normalize_text(job.get("title")), title):
        return False
    if company_name and not _matches_query(_normalize_text(job.get("company_name")), company_name):
        return False
    if company_industry and not _matches_query(_normalize_text(job.get("company_industry")), company_industry):
        return False
    if department and not _matches_query(_normalize_text(job.get("department")), department):
        return False
    if location_city and not _matches_query(_normalize_text(location.get("city") or job.get("company_location")), location_city):
        return False
    if location_country and not _matches_query(_normalize_text(location.get("country")), location_country):
        return False
    if remote is not None and bool(job.get("remote")) is not remote:
        return False
    if remote_type and not _matches_query(_normalize_text(location.get("remote_type")), remote_type):
        return False
    if not _contains_any(job.get("employment_type") or [], _split_values(employment_type)):
        return False
    if seniority and not _matches_query(_normalize_text(job.get("seniority")), seniority):
        return False
    if not _contains_any(_skill_names(job.get("skills")), _split_values(skills)):
        return False
    if not _contains_any(job.get("categories") or [], _split_values(categories)):
        return False
    if not _contains_any(job.get("tags") or [], _split_values(tags)):
        return False
    if not _matches_salary(job, salary_min, salary_max):
        return False
    return True


def _relevance(job: dict[str, Any], keyword: str | None) -> int:
    text = _search_text(job)
    score = 0
    for token in _normalize_text(keyword).split():
        if token in text:
            score += 2
    if _normalize_text(job.get("title")) and _matches_query(_normalize_text(job.get("title")), keyword):
        score += 3
    return score


def _sort_jobs(items: list[dict[str, Any]], sort: str | None, keyword: str | None) -> list[dict[str, Any]]:
    key = _normalize_text(sort or "newest")
    if key == "oldest":
        return sorted(items, key=lambda item: item["created_at"])
    if key in {"most relevant", "most_relevant", "relevant"}:
        return sorted(items, key=lambda item: (-_relevance(item, keyword), item["created_at"]), reverse=False)
    if key in {"salary high to low", "salary_high_to_low"}:
        return sorted(
            items,
            key=lambda item: _salary_number(item.get("salary") or {}, "max") or -1,
            reverse=True,
        )
    if key in {"salary low to high", "salary_low_to_high"}:
        return sorted(
            items,
            key=lambda item: _salary_number(item.get("salary") or {}, "min") or math.inf,
        )
    return sorted(items, key=lambda item: item["created_at"], reverse=True)


def _paginate(items: list[Any], page: int, limit: int) -> tuple[list[Any], int]:
    total = len(items)
    start = (page - 1) * limit
    return items[start : start + limit], total


def _total_pages(total: int, limit: int) -> int:
    return math.ceil(total / limit) if total else 0


def _to_search_item(job: dict[str, Any]) -> JobSearchListItem:
    skill_names = _skill_names(job.get("skills"))
    location_value = _location_city(job)
    return JobSearchListItem(
        id=job["id"],
        job_id=job["id"],
        title=job["title"],
        company_name=job.get("company_name"),
        company_industry=job.get("company_industry"),
        department=job.get("department"),
        location=location_value,
        location_detail=job.get("location") or {},
        job_type=_job_type(job),
        employment_type=job.get("employment_type") or [],
        working_model=_working_model(job),
        seniority=job.get("seniority"),
        education=job.get("education_level"),
        education_level=job.get("education_level"),
        skills=skill_names,
        requirement="\n".join(job.get("requirements") or []),
        requirements=job.get("requirements") or [],
        responsibilities=job.get("responsibilities") or [],
        categories=job.get("categories") or [],
        tags=job.get("tags") or [],
        salary=job.get("salary") or {},
        remote=bool(job.get("remote")),
    )


def _load_public_jobs(conn: psycopg.Connection) -> list[dict[str, Any]]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM jobs
            WHERE status = 'published'
              AND visibility = 'public'
              AND archived = false
            """
        )
        rows = cur.fetchall()
    return [_row_to_dict(row) for row in rows]


def search_jobs_response(
    conn: psycopg.Connection,
    *,
    keyword: str | None = None,
    q: str | None = None,
    title: str | None = None,
    company_name: str | None = None,
    company_industry: str | None = None,
    industry: str | None = None,
    category: str | None = None,
    department: str | None = None,
    location_city: str | None = None,
    location: str | None = None,
    location_country: str | None = None,
    remote: bool | None = None,
    remote_type: str | None = None,
    working_model: str | None = None,
    employment_type: str | None = None,
    seniority: str | None = None,
    skills: str | None = None,
    categories: str | None = None,
    tags: str | None = None,
    salary_min: float | None = None,
    salary_max: float | None = None,
    page: int = 1,
    limit: int = 10,
    sort: str | None = "newest",
) -> JobSearchListResponse:
    selected_keyword = keyword or q
    selected_industry = company_industry or industry
    selected_categories = categories or category
    selected_location_city = location_city or location
    selected_remote_type = remote_type or working_model

    jobs = [
        job
        for job in _load_public_jobs(conn)
        if _is_public_job(job)
        and _matches_job_filters(
            job,
            keyword=selected_keyword,
            title=title,
            company_name=company_name,
            company_industry=selected_industry,
            department=department,
            location_city=selected_location_city,
            location_country=location_country,
            remote=remote,
            remote_type=selected_remote_type,
            employment_type=employment_type,
            seniority=seniority,
            skills=skills,
            categories=selected_categories,
            tags=tags,
            salary_min=salary_min,
            salary_max=salary_max,
        )
    ]
    ordered = _sort_jobs(jobs, sort, selected_keyword)
    paged, total = _paginate(ordered, page, limit)
    return JobSearchListResponse(
        items=[_to_search_item(job) for job in paged],
        total=total,
        page=page,
        limit=limit,
        totalPages=_total_pages(total, limit),
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreateRequest, conn: DbConnection, user: CurrentUser) -> JobResponse:
    data = _dump_payload(payload, partial=False)
    _apply_create_defaults(data)
    data["created_by"] = user.id
    columns = INSERTABLE_JOB_COLUMNS
    values = [_encode_column_value(column, data.get(column)) for column in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO jobs ({", ".join(columns)})
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
    return JobResponse(**_row_to_dict(row))


@router.get("/my", response_model=list[JobResponse])
def list_my_jobs(conn: DbConnection, user: CurrentUser) -> list[JobResponse]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT {_select_sql()}
            FROM jobs
            WHERE created_by = %s::uuid
            ORDER BY created_at DESC
            """,
            (user.id,),
        )
        rows = cur.fetchall()
    return [JobResponse(**_row_to_dict(row)) for row in rows]


@router.get("/search", response_model=JobSearchListResponse)
def search_jobs(
    conn: DbConnection,
    keyword: str | None = Query(default=None, max_length=200),
    q: str | None = Query(default=None, max_length=200),
    title: str | None = None,
    company_name: str | None = None,
    company_industry: str | None = None,
    industry: str | None = None,
    category: str | None = None,
    department: str | None = None,
    location_city: str | None = Query(default=None, alias="location.city"),
    location: str | None = None,
    location_country: str | None = Query(default=None, alias="location.country"),
    remote: bool | None = None,
    remote_type: str | None = None,
    working_model: str | None = Query(default=None, alias="workingModel"),
    employment_type: str | None = Query(default=None, alias="employmentType"),
    employment_type_snake: str | None = Query(default=None, alias="employment_type"),
    seniority: str | None = None,
    experience_level: str | None = Query(default=None, alias="experienceLevel"),
    skills: str | None = None,
    categories: str | None = None,
    tags: str | None = None,
    salary_min: float | None = Query(default=None, alias="salaryMin", ge=0),
    salary_max: float | None = Query(default=None, alias="salaryMax", ge=0),
    salary_min_snake: float | None = Query(default=None, alias="salary_min", ge=0),
    salary_max_snake: float | None = Query(default=None, alias="salary_max", ge=0),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    sort: str | None = "newest",
) -> JobSearchListResponse:
    return search_jobs_response(
        conn,
        keyword=keyword,
        q=q,
        title=title,
        company_name=company_name,
        company_industry=company_industry,
        industry=industry,
        category=category,
        department=department,
        location_city=location_city,
        location=location,
        location_country=location_country,
        remote=remote,
        remote_type=remote_type,
        working_model=working_model,
        employment_type=employment_type or employment_type_snake,
        seniority=seniority or experience_level,
        skills=skills,
        categories=categories,
        tags=tags,
        salary_min=salary_min if salary_min is not None else salary_min_snake,
        salary_max=salary_max if salary_max is not None else salary_max_snake,
        page=page,
        limit=limit,
        sort=sort,
    )


@router.get("/search/filters", response_model=JobSearchFiltersResponse)
def get_job_search_filters(conn: DbConnection) -> JobSearchFiltersResponse:
    jobs = _load_public_jobs(conn)
    industries: set[str] = set()
    categories: set[str] = set()
    tags: set[str] = set()
    skills: set[str] = set()
    departments: set[str] = set()
    employment_types: set[str] = set()
    seniorities: set[str] = set()
    locations: set[str] = set()
    for job in jobs:
        if job.get("company_industry"):
            industries.add(str(job["company_industry"]))
        categories.update(job.get("categories") or [])
        tags.update(job.get("tags") or [])
        skills.update(_skill_names(job.get("skills")))
        if job.get("department"):
            departments.add(str(job["department"]))
        employment_types.update(job.get("employment_type") or [])
        if job.get("seniority"):
            seniorities.add(str(job["seniority"]))
        city = _location_city(job)
        if city:
            locations.add(city)
    return JobSearchFiltersResponse(
        industries=sorted(industries),
        categories=sorted(categories),
        tags=sorted(tags),
        skills=sorted(skills),
        departments=sorted(departments),
        employmentTypes=sorted(employment_types),
        seniorities=sorted(seniorities),
        locations=sorted(locations),
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    conn: DbConnection,
    authorization: Annotated[str | None, Header()] = None,
) -> JobResponse:
    job = _fetch_job(conn, job_id)
    user = _optional_user_from_authorization(authorization, conn)
    if job is None or not _can_read_job(job, user):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**job)


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: str,
    payload: JobUpdateRequest,
    conn: DbConnection,
    user: CurrentUser,
) -> JobResponse:
    job = _fetch_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    _require_owner(job, user)

    data = _dump_payload(payload, partial=True)
    if not data:
        return JobResponse(**job)

    allowed = [column for column in data if column in INSERTABLE_JOB_COLUMNS and column != "created_by"]
    assignments = ", ".join(f"{column} = %s" for column in allowed)
    values = [_encode_column_value(column, data[column]) for column in allowed]
    values.extend([job_id, user.id])
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE jobs
                SET {assignments}
                WHERE id = %s::uuid
                  AND (created_by = %s::uuid)
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return JobResponse(**_row_to_dict(row))


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_job(job_id: str, conn: DbConnection, user: CurrentUser) -> None:
    job = _fetch_job(conn, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    _require_owner(job, user)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM jobs
                WHERE id = %s::uuid
                  AND created_by = %s::uuid
                """,
                (job_id, user.id),
            )
        conn.commit()
    except psycopg.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@employer_requests_router.post("", status_code=status.HTTP_201_CREATED)
def create_employer_request(
    conn: DbConnection,
    user: CurrentUser,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    request = JobCreateRequest.model_validate(_snakeize(payload))
    return _job_to_camel(create_job(request, conn, user))


@employer_requests_router.get("/my")
def list_my_employer_requests(
    conn: DbConnection,
    user: CurrentUser,
) -> list[dict[str, Any]]:
    return [_job_to_camel(job) for job in list_my_jobs(conn, user)]


@employer_requests_router.get("/{request_id}")
def get_employer_request(
    request_id: str,
    conn: DbConnection,
    user: CurrentUser,
) -> dict[str, Any]:
    job = _fetch_job(conn, request_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    _require_owner(job, user)
    return _job_to_camel(JobResponse(**job))


@employer_requests_router.put("/{request_id}")
def update_employer_request(
    request_id: str,
    conn: DbConnection,
    user: CurrentUser,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    request = JobUpdateRequest.model_validate(_snakeize(payload))
    return _job_to_camel(update_job(request_id, request, conn, user))


@employer_requests_router.delete(
    "/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
def delete_employer_request(
    request_id: str,
    conn: DbConnection,
    user: CurrentUser,
) -> None:
    delete_job(request_id, conn, user)
