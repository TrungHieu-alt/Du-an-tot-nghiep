"""Normalization helpers for normal CV/Job extraction, search, and writes."""

from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.enums import (
    CURRENCIES,
    CV_STATUSES,
    EDUCATION_LEVELS,
    EMPLOYMENT_TYPES,
    INDUSTRIES,
    JOB_STATUSES,
    LANGUAGE_LEVELS,
    OCCUPATION_GROUPS,
    PORTFOLIO_MEDIA_TYPES,
    PRE_SCREEN_QUESTION_TYPES,
    REMOTE_TYPES,
    SALARY_PERIODS,
    SENIORITY_LEVELS,
    SKILL_CATEGORIES,
    SKILL_LEVELS,
    VISIBILITY_OPTIONS,
)

REFERENCE_DIR = Path(__file__).resolve().parents[1] / "reference_data"


def normalize_lookup_text(value: Any) -> str:
    if value is None:
        return ""
    raw = str(value).strip().lower().replace("đ", "d")
    decomposed = unicodedata.normalize("NFD", raw)
    ascii_text = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9_+\-.#/]+", " ", ascii_text)
    return re.sub(r"\s+", " ", normalized).strip()


def slugify_key(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", normalize_lookup_text(value)).strip("_")
    return slug or "unknown"


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return True
    return False


def _contains(text: str, phrase: str) -> bool:
    needle = normalize_lookup_text(phrase)
    if not needle:
        return False
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", text) is not None


def _normalize_with_mapping(value: Any, allowed: tuple[str, ...], mapping: list[tuple[str, tuple[str, ...]]]) -> str:
    if _is_missing(value):
        return "unknown"
    raw = str(value).strip()
    if raw in allowed:
        return raw
    lookup = normalize_lookup_text(raw)
    for key in allowed:
        if lookup == normalize_lookup_text(key):
            return key
    for key, phrases in mapping:
        if any(_contains(lookup, phrase) for phrase in phrases):
            return key
    return "unknown"


def as_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;|]", value) if item.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


SKILL_LEVEL_MAPPING = [
    ("expert", ("expert", "specialist", "master", "deep expertise", "chuyên gia", "rất giỏi", "chuyên sâu")),
    ("advanced", ("strong", "proficient", "experienced", "solid", "thành thạo", "kinh nghiệm tốt", "vững")),
    ("intermediate", ("good", "fair", "working knowledge", "can use", "practical experience", "khá", "dùng được", "có kinh nghiệm thực tế")),
    ("beginner", ("basic", "fundamental", "newbie", "fresher", "beginner", "cơ bản", "mới bắt đầu")),
]

SENIORITY_MAPPING = [
    ("director", ("director", "head of engineering", "head of department", "giám đốc", "trưởng bộ phận")),
    ("manager", ("manager", "engineering manager", "project manager", "quản lý")),
    ("lead", ("tech lead", "team lead", "lead developer", "lead engineer", "trưởng nhóm kỹ thuật")),
    ("senior", ("senior", "5+ years experience", "5 years", "6 years", "5 năm kinh nghiệm trở lên")),
    ("middle", ("middle", "mid-level", "mid level", "2-4 years experience", "2 years", "3 years", "4 years", "2-4 năm kinh nghiệm", "3 năm kinh nghiệm")),
    ("junior", ("junior", "1 year experience", "1+ year", "1 năm kinh nghiệm")),
    ("fresher", ("fresh graduate", "fresher", "entry-level", "new graduate", "mới ra trường")),
    ("intern", ("internship", "intern", "thực tập", "thực tập sinh")),
]

EMPLOYMENT_TYPE_MAPPING = [
    ("fulltime", ("full-time", "full time", "permanent", "toàn thời gian", "chính thức")),
    ("parttime", ("part-time", "part time", "bán thời gian")),
    ("contract", ("contract", "fixed-term contract", "hợp đồng", "hợp đồng có thời hạn")),
    ("internship", ("intern", "internship", "thực tập", "thực tập sinh")),
    ("freelance", ("freelance", "freelancer", "tự do")),
    ("temporary", ("temporary", "seasonal", "thời vụ", "tạm thời")),
]

REMOTE_TYPE_MAPPING = [
    ("hybrid", ("hybrid", "2 days office", "3 days remote", "linh hoạt", "kết hợp văn phòng và từ xa")),
    ("remote", ("remote", "work from home", "wfh", "làm từ xa", "làm online")),
    ("onsite", ("on-site", "onsite", "office-based", "work at office", "làm tại văn phòng", "tại công ty")),
]

EDUCATION_LEVEL_MAPPING = [
    ("high_school", ("high school", "THPT", "trung học phổ thông")),
    ("vocational", ("vocational", "college nghề", "trung cấp", "trung cấp nghề")),
    ("associate", ("associate", "cao đẳng")),
    ("bachelor", ("bachelor", "university", "đại học", "cử nhân", "engineer degree", "kỹ sư")),
    ("master", ("master", "thạc sĩ", "MSc", "MBA")),
    ("phd", ("phd", "doctorate", "tiến sĩ")),
    ("certificate", ("certificate", "certification", "chứng chỉ")),
]

LANGUAGE_LEVEL_MAPPING = [
    ("native", ("native", "mother tongue", "bản ngữ", "tiếng mẹ đẻ")),
    ("fluent", ("fluent", "excellent", "C2", "lưu loát", "rất tốt")),
    ("proficient", ("proficient", "professional working proficiency", "C1", "thành thạo")),
    ("intermediate", ("intermediate", "B1", "B2", "trung cấp", "khá")),
    ("conversational", ("conversational", "can communicate", "giao tiếp được", "giao tiếp cơ bản")),
    ("basic", ("basic", "elementary", "A1", "A2", "cơ bản")),
]

PRE_SCREEN_TYPE_MAPPING = [
    ("text", ("text", "paragraph", "short answer", "free text", "tự luận")),
    ("number", ("number", "numeric", "số")),
    ("single-choice", ("single-choice", "single choice", "radio", "one option", "một lựa chọn")),
    ("multi-choice", ("multi-choice", "multiple choice", "checkbox", "many options", "nhiều lựa chọn")),
]

VISIBILITY_MAPPING = [
    ("public", ("public", "visible", "open", "công khai")),
    ("private", ("private", "hidden", "internal", "riêng tư", "nội bộ")),
    ("unlisted", ("unlisted", "link only", "chỉ ai có link")),
]

SKILL_CATEGORY_MAPPING = [
    ("technical", ("technical", "technical skill", "engineering")),
    ("professional", ("professional", "professional skill", "nghiệp vụ")),
    ("soft_skill", ("soft skill", "soft-skill", "soft_skill")),
    ("language", ("language", "ngôn ngữ")),
    ("tool", ("tool", "software", "platform")),
    ("domain_knowledge", ("domain knowledge", "domain_knowledge", "industry knowledge")),
    ("certification", ("certification", "certificate", "chứng chỉ")),
    ("management", ("management", "leadership", "quản lý")),
]

PORTFOLIO_MEDIA_MAPPING = [
    ("website", ("website", "site", "portfolio")),
    ("github", ("github", "git hub")),
    ("linkedin", ("linkedin", "linked in")),
    ("behance", ("behance",)),
    ("dribbble", ("dribbble",)),
    ("youtube", ("youtube", "you tube")),
    ("document", ("document", "pdf", "doc")),
    ("image", ("image", "photo", "picture")),
    ("video", ("video", "clip")),
    ("other", ("other", "url", "link")),
]

SALARY_PERIOD_MAPPING = [
    ("hour", ("hour", "hourly", "per hour")),
    ("day", ("day", "daily", "per day")),
    ("month", ("month", "monthly", "per month")),
    ("year", ("year", "yearly", "annual", "per year")),
    ("project", ("project", "per project")),
]

CURRENCY_MAPPING = [
    ("VND", ("vnd", "vietnamese dong", "dong", "đồng")),
    ("USD", ("usd", "us dollar", "dollar")),
    ("EUR", ("eur", "euro")),
    ("JPY", ("jpy", "yen")),
    ("KRW", ("krw", "won")),
]

INDUSTRY_MAPPING = [
    ("information_technology", ("information technology", "it", "software", "technology", "công nghệ thông tin")),
    ("accounting_finance", ("accounting", "finance", "tax", "kế toán", "tài chính", "thuế")),
    ("sales", ("sales", "business development", "bán hàng", "telesales")),
    ("marketing", ("marketing", "seo", "sem", "brand", "advertising", "quảng cáo")),
    ("human_resources", ("human resources", "hr", "recruitment", "tuyển dụng", "nhân sự")),
    ("education", ("education", "teacher", "lecturer", "giáo dục", "giảng viên")),
    ("healthcare", ("healthcare", "doctor", "nurse", "medical", "y tế")),
    ("engineering_construction", ("construction", "civil", "mechanical", "electrical", "architect", "xây dựng")),
    ("design_creative", ("design", "creative", "graphic", "ui ux", "thiết kế")),
    ("customer_service", ("customer service", "customer support", "cskh", "chăm sóc khách hàng")),
    ("operations", ("operations", "operation", "vận hành")),
    ("logistics_supply_chain", ("logistics", "supply chain", "warehouse", "kho vận")),
    ("hospitality_tourism", ("hospitality", "tourism", "hotel", "restaurant", "du lịch")),
    ("legal", ("legal", "lawyer", "compliance", "pháp lý")),
    ("manufacturing", ("manufacturing", "production", "factory", "sản xuất")),
    ("retail", ("retail", "store", "bán lẻ")),
    ("other", ("other", "khác")),
]

OCCUPATION_GROUP_MAPPING = [
    ("software_engineering", ("software engineering", "software engineer", "software developer", "frontend", "backend", "fullstack", "developer")),
    ("data_ai", ("data", "ai", "machine learning", "ml", "analytics")),
    ("it_support", ("it support", "helpdesk", "system admin")),
    ("cybersecurity", ("cybersecurity", "security")),
    ("devops_cloud", ("devops", "cloud", "sre")),
    ("accountant", ("accountant", "accounting", "kế toán")),
    ("auditor", ("auditor", "audit", "kiểm toán")),
    ("financial_analyst", ("financial analyst", "finance analyst")),
    ("tax_specialist", ("tax", "tax specialist", "thuế")),
    ("sales_executive", ("sales executive", "sales", "telesales", "bán hàng")),
    ("business_development", ("business development", "bd")),
    ("account_manager", ("account manager",)),
    ("digital_marketing", ("digital marketing", "google ads", "meta ads", "facebook ads")),
    ("content_marketing", ("content marketing", "copywriter", "content")),
    ("seo_sem", ("seo", "sem", "search engine optimization")),
    ("brand_marketing", ("brand marketing", "brand")),
    ("hr_recruitment", ("hr recruitment", "recruitment", "hiring", "tuyển dụng")),
    ("teacher", ("teacher", "giáo viên")),
    ("lecturer", ("lecturer", "giảng viên")),
    ("doctor", ("doctor", "bác sĩ")),
    ("nurse", ("nurse", "điều dưỡng")),
    ("civil_engineer", ("civil engineer", "xây dựng")),
    ("graphic_designer", ("graphic designer", "photoshop", "illustrator")),
    ("ui_ux_designer", ("ui ux", "figma", "product designer")),
    ("customer_support", ("customer support", "customer service", "cskh")),
    ("operations_staff", ("operations staff", "operations")),
    ("logistics_staff", ("logistics", "warehouse")),
    ("legal_staff", ("legal staff", "legal")),
    ("production_worker", ("production worker", "production")),
    ("retail_staff", ("retail staff", "retail")),
    ("other", ("other", "khác")),
]


def normalize_skill_level(value: Any) -> str:
    return _normalize_with_mapping(value, SKILL_LEVELS, SKILL_LEVEL_MAPPING)


def normalize_seniority(value: Any) -> str:
    return _normalize_with_mapping(value, SENIORITY_LEVELS, SENIORITY_MAPPING)


def normalize_employment_type(value: Any) -> str:
    return _normalize_with_mapping(value, EMPLOYMENT_TYPES, EMPLOYMENT_TYPE_MAPPING)


def normalize_employment_types(values: Any) -> list[str]:
    normalized: list[str] = []
    for value in as_text_list(values):
        item = normalize_employment_type(value)
        if item not in normalized:
            normalized.append(item)
    filtered = [item for item in normalized if item != "unknown"]
    return filtered or ["unknown"]


def normalize_remote_type(value: Any) -> str:
    return _normalize_with_mapping(value, REMOTE_TYPES, REMOTE_TYPE_MAPPING)


def normalize_education_level(value: Any) -> str:
    return _normalize_with_mapping(value, EDUCATION_LEVELS, EDUCATION_LEVEL_MAPPING)


def normalize_language_level(value: Any) -> str:
    return _normalize_with_mapping(value, LANGUAGE_LEVELS, LANGUAGE_LEVEL_MAPPING)


def normalize_pre_screen_question_type(value: Any) -> str:
    return _normalize_with_mapping(value, PRE_SCREEN_QUESTION_TYPES, PRE_SCREEN_TYPE_MAPPING)


def normalize_status(value: Any, entity_type: str, *, default_for_create: bool = False) -> str:
    if default_for_create and _is_missing(value):
        return "draft"
    allowed = CV_STATUSES if entity_type == "cv" else JOB_STATUSES
    mapping = [(key, (key, key.replace("_", " "))) for key in allowed if key != "unknown"]
    return _normalize_with_mapping(value, allowed, mapping)


def normalize_visibility(value: Any, *, default_for_create: bool = False) -> str:
    if default_for_create and _is_missing(value):
        return "private"
    return _normalize_with_mapping(value, VISIBILITY_OPTIONS, VISIBILITY_MAPPING)


def normalize_skill_category(value: Any) -> str:
    return _normalize_with_mapping(value, SKILL_CATEGORIES, SKILL_CATEGORY_MAPPING)


def normalize_portfolio_media_type(value: Any) -> str:
    return _normalize_with_mapping(value, PORTFOLIO_MEDIA_TYPES, PORTFOLIO_MEDIA_MAPPING)


def normalize_salary_period(value: Any) -> str:
    return _normalize_with_mapping(value, SALARY_PERIODS, SALARY_PERIOD_MAPPING)


def normalize_currency(value: Any) -> str:
    if _is_missing(value):
        return "unknown"
    raw = str(value).strip()
    if raw in CURRENCIES:
        return raw
    upper = raw.upper()
    if upper in CURRENCIES:
        return upper
    lookup = normalize_lookup_text(raw)
    for key, phrases in CURRENCY_MAPPING:
        if any(_contains(lookup, phrase) for phrase in phrases):
            return key
    return "unknown"


def normalize_industry(value: Any) -> str:
    return _normalize_with_mapping(value, INDUSTRIES, INDUSTRY_MAPPING)


def normalize_occupation_group(value: Any) -> str:
    return _normalize_with_mapping(value, OCCUPATION_GROUPS, OCCUPATION_GROUP_MAPPING)


@lru_cache(maxsize=1)
def _skill_alias_entries() -> tuple[dict[str, Any], ...]:
    path = REFERENCE_DIR / "skill-aliases.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    entries: list[dict[str, Any]] = []
    for item in payload.get("skillAliases", []):
        normalized_name = str(item.get("normalizedName") or "").strip()
        if not normalized_name:
            continue
        for alias in item.get("aliases", []):
            alias_text = str(alias).strip()
            if not alias_text:
                continue
            entries.append(
                {
                    "alias": alias_text,
                    "alias_lookup": normalize_lookup_text(alias_text),
                    "normalized_name": normalized_name,
                    "category": normalize_skill_category(item.get("category")),
                    "industry": normalize_industry(item.get("industry")),
                }
            )
    return tuple(sorted(entries, key=lambda item: len(item["alias_lookup"]), reverse=True))


def normalize_skill_name(value: Any) -> dict[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return {"name": "", "normalized_name": "unknown", "category": "unknown", "industry": "unknown"}
    lookup = normalize_lookup_text(raw)
    contained: dict[str, Any] | None = None
    for entry in _skill_alias_entries():
        if lookup == entry["alias_lookup"]:
            return {
                "name": raw,
                "normalized_name": str(entry["normalized_name"]),
                "category": str(entry["category"]),
                "industry": str(entry["industry"]),
            }
        if contained is None and _contains(lookup, entry["alias_lookup"]):
            contained = entry
    if contained:
        return {
            "name": str(contained["alias"]),
            "normalized_name": str(contained["normalized_name"]),
            "category": str(contained["category"]),
            "industry": str(contained["industry"]),
        }
    return {"name": raw, "normalized_name": slugify_key(raw), "category": "unknown", "industry": "unknown"}


def _to_float(value: Any, default: float = 0.0) -> float:
    if _is_missing(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    if _is_missing(value):
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def normalize_skill_payload(
    item: Any,
    *,
    include_years: bool = False,
    default_category: str = "technical",
    default_weight: int | None = None,
) -> dict[str, Any]:
    data = deepcopy(item) if isinstance(item, dict) else {"name": item}
    info = normalize_skill_name(data.get("name") or data.get("normalized_name") or data.get("normalizedName"))
    level_source = data.get("level") if not _is_missing(data.get("level")) else data.get("name")
    category = normalize_skill_category(data.get("category"))
    if category == "unknown" and _is_missing(data.get("category")):
        category = info["category"] if info["category"] != "unknown" else default_category
    normalized: dict[str, Any] = {
        "name": info["name"],
        "normalized_name": info["normalized_name"],
        "level": normalize_skill_level(level_source),
        "category": normalize_skill_category(category),
    }
    if include_years:
        normalized["years"] = _to_float(data.get("years"), 0)
    if default_weight is not None or "weight" in data:
        normalized["weight"] = _to_int(data.get("weight"), default_weight or 0)
    return normalized


def normalize_skills(values: Any, *, include_years: bool = False, default_weight: int | None = None) -> list[dict[str, Any]]:
    if not isinstance(values, list):
        values = as_text_list(values)
    return [
        normalize_skill_payload(value, include_years=include_years, default_weight=default_weight)
        for value in values
        if value and (not isinstance(value, dict) or value.get("name") or value.get("normalized_name") or value.get("normalizedName"))
    ]


def extract_years_of_experience(text: Any) -> float:
    lookup = normalize_lookup_text(text)
    if not lookup:
        return 0
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(?:years?|năm)", lookup)
    if range_match:
        return float(range_match.group(2))
    plus_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|năm)", lookup)
    if plus_match:
        return float(plus_match.group(1))
    return 0


def _infer_industry_occupation(text: str, skills: list[dict[str, Any]]) -> tuple[str, str]:
    lookup = normalize_lookup_text(" ".join([text, " ".join(skill.get("normalized_name", "") for skill in skills)]))
    industry = normalize_industry(lookup)
    occupation = normalize_occupation_group(lookup)
    for skill in skills:
        if industry == "unknown":
            industry = normalize_industry(skill.get("industry"))
        if occupation == "unknown":
            occupation = normalize_occupation_group(skill.get("normalized_name"))
    if industry == "unknown" and occupation in {"software_engineering", "data_ai", "it_support", "cybersecurity", "devops_cloud"}:
        industry = "information_technology"
    if industry == "unknown" and occupation in {"digital_marketing", "content_marketing", "seo_sem", "brand_marketing"}:
        industry = "marketing"
    if industry == "unknown" and occupation in {"accountant", "auditor", "financial_analyst", "tax_specialist"}:
        industry = "accounting_finance"
    if industry == "information_technology" and occupation == "unknown":
        occupation = "software_engineering"
    if industry == "marketing" and occupation == "unknown":
        occupation = "digital_marketing"
    if industry == "accounting_finance" and occupation == "unknown":
        occupation = "accountant"
    if industry == "sales" and occupation == "unknown":
        occupation = "sales_executive"
    return industry, occupation


def _text_from_values(data: dict[str, Any], keys: tuple[str, ...], source_text: str = "") -> str:
    parts = [source_text]
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            parts.extend(str(item) for item in value if str(item).strip())
        elif value:
            parts.append(str(value))
    return " ".join(parts)


def normalize_cv_payload(data: dict[str, Any], *, for_create: bool = False, include_missing: bool = False, source_text: str = "") -> dict[str, Any]:
    result = deepcopy(data)
    text = _text_from_values(result, ("headline", "summary", "target_role", "availability"), source_text)
    if for_create or "status" in result:
        result["status"] = normalize_status(result.get("status"), "cv", default_for_create=for_create)
    if for_create or "visibility" in result:
        result["visibility"] = normalize_visibility(result.get("visibility"), default_for_create=for_create)
    if for_create:
        result["archived"] = bool(result.get("archived", False))
    if include_missing or "employment_type" in result:
        result["employment_type"] = normalize_employment_types(result.get("employment_type"))
    if include_missing or "skills" in result:
        result["skills"] = normalize_skills(result.get("skills") or [], include_years=True)
    inferred_industry, inferred_occupation = _infer_industry_occupation(text, result.get("skills") or [])
    if include_missing or "industry" in result:
        industry = normalize_industry(result.get("industry"))
        result["industry"] = industry if industry != "unknown" else inferred_industry
    if include_missing or "occupation_group" in result:
        occupation = normalize_occupation_group(result.get("occupation_group"))
        result["occupation_group"] = occupation if occupation != "unknown" else inferred_occupation
    if include_missing or "career_level" in result:
        result["career_level"] = normalize_seniority(result.get("career_level") or text)
    if include_missing or "years_of_experience" in result:
        result["years_of_experience"] = _to_float(result.get("years_of_experience"), extract_years_of_experience(text))
    if include_missing or "location" in result:
        result["location"] = result.get("location") if isinstance(result.get("location"), dict) else {}
    if include_missing or "experiences" in result:
        experiences = []
        for item in result.get("experiences") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                normalized["employment_type"] = normalize_employment_type(normalized.get("employment_type"))
                normalized["team_size"] = _to_int(normalized.get("team_size"), 0)
                normalized.setdefault("skills_used", [])
                normalized.setdefault("tools_used", [])
                normalized.setdefault("responsibilities", [])
                normalized.setdefault("achievements", [])
                normalized.setdefault("tags", [])
                experiences.append(normalized)
        result["experiences"] = experiences
    if include_missing or "education" in result:
        education = []
        for item in result.get("education") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                source = normalized.get("level") or " ".join(str(normalized.get(key) or "") for key in ("degree", "major", "school"))
                normalized["level"] = normalize_education_level(source)
                education.append(normalized)
        result["education"] = education
    if include_missing or "languages" in result:
        languages = []
        for item in result.get("languages") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                normalized["level"] = normalize_language_level(normalized.get("level") or normalized.get("name"))
                languages.append(normalized)
        result["languages"] = languages
    if include_missing or "portfolio" in result:
        portfolio = []
        for item in result.get("portfolio") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                normalized["media_type"] = normalize_portfolio_media_type(normalized.get("media_type") or normalized.get("url"))
                portfolio.append(normalized)
        result["portfolio"] = portfolio
    if include_missing or "projects" in result:
        projects = []
        for item in result.get("projects") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                normalized.setdefault("tools", normalized.get("tech_stack") or [])
                normalized.setdefault("skills_used", [])
                normalized.setdefault("outcomes", [])
                projects.append(normalized)
        result["projects"] = projects
    for key in ("tools_and_technologies", "domain_knowledge", "tags"):
        if include_missing or key in result:
            result[key] = as_text_list(result.get(key))
    for key in ("certifications", "references"):
        if include_missing and key not in result:
            result[key] = []
    return result


def normalize_job_payload(data: dict[str, Any], *, for_create: bool = False, include_missing: bool = False, source_text: str = "") -> dict[str, Any]:
    result = deepcopy(data)
    text = _text_from_values(result, ("title", "company_industry", "department", "description", "seniority", "education_level"), source_text)
    if for_create or "status" in result:
        result["status"] = normalize_status(result.get("status"), "job", default_for_create=for_create)
    if for_create or "visibility" in result:
        result["visibility"] = normalize_visibility(result.get("visibility"), default_for_create=for_create)
    if for_create:
        result["archived"] = bool(result.get("archived", False))
    if include_missing or "employment_type" in result:
        result["employment_type"] = normalize_employment_types(result.get("employment_type"))
    if include_missing or "seniority" in result:
        result["seniority"] = normalize_seniority(result.get("seniority") or text)
    if include_missing or "location" in result:
        location = result.get("location") if isinstance(result.get("location"), dict) else {}
        if _is_missing(location.get("remote_type")) and result.get("remote") is True:
            location["remote_type"] = "remote"
        else:
            location["remote_type"] = normalize_remote_type(location.get("remote_type"))
        result["location"] = location
    if include_missing or "skills" in result:
        result["skills"] = normalize_skills(result.get("skills") or [])
    if include_missing or "must_have_skills" in result:
        result["must_have_skills"] = normalize_skills(result.get("must_have_skills") or [], default_weight=10)
    if include_missing or "nice_to_have_skills" in result:
        result["nice_to_have_skills"] = normalize_skills(result.get("nice_to_have_skills") or [], default_weight=5)
    all_skills = (result.get("skills") or []) + (result.get("must_have_skills") or []) + (result.get("nice_to_have_skills") or [])
    inferred_industry, inferred_occupation = _infer_industry_occupation(text, all_skills)
    if include_missing or "industry" in result:
        industry = normalize_industry(result.get("industry"))
        result["industry"] = industry if industry != "unknown" else inferred_industry
    if include_missing or "occupation_group" in result:
        occupation = normalize_occupation_group(result.get("occupation_group"))
        result["occupation_group"] = occupation if occupation != "unknown" else inferred_occupation
    if include_missing or "education_level" in result:
        result["education_level"] = normalize_education_level(result.get("education_level"))
    if include_missing or "required_education" in result:
        required_education = result.get("required_education") if isinstance(result.get("required_education"), dict) else {}
        required_education["level"] = normalize_education_level(required_education.get("level") or result.get("education_level"))
        required_education.setdefault("major", "")
        result["required_education"] = required_education
    if include_missing or "salary" in result:
        salary = result.get("salary") if isinstance(result.get("salary"), dict) else {}
        salary["min"] = _to_float(salary.get("min"), 0)
        salary["max"] = _to_float(salary.get("max"), 0)
        salary["currency"] = normalize_currency(salary.get("currency"))
        salary["period"] = normalize_salary_period(salary.get("period"))
        result["salary"] = salary
    if include_missing or "pre_screen_questions" in result:
        questions = []
        for item in result.get("pre_screen_questions") or []:
            if isinstance(item, dict):
                normalized = deepcopy(item)
                normalized["type"] = normalize_pre_screen_question_type(normalized.get("type"))
                normalized["required"] = bool(normalized.get("required", False))
                normalized.setdefault("options", [])
                questions.append(normalized)
        result["pre_screen_questions"] = questions
    for key in (
        "responsibilities",
        "requirements",
        "nice_to_have",
        "tools_and_technologies",
        "domain_knowledge",
        "required_certifications",
        "tags",
        "categories",
        "benefits",
        "required_docs",
    ):
        if include_missing or key in result:
            result[key] = as_text_list(result.get(key))
    if include_missing or "experience_years" in result:
        result["experience_years"] = _to_float(result.get("experience_years"), extract_years_of_experience(text))
    if include_missing or "team_size" in result:
        result["team_size"] = _to_int(result.get("team_size"), 0)
    return result
