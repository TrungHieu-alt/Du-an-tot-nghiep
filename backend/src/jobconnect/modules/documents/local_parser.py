"""Deterministic local parser — maps preprocessed text to canonical schema fields.

Slice 5 implementation: keyword-based enum detection with safe defaults.
Slice 6 replaces _parse_resume / _parse_job internals with an LLM adapter
while keeping the ParsedResume / ParsedJob output contracts unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ParsedResume:
    title: str
    summary: str
    experience: str
    skills: list[str] = field(default_factory=list)
    location: str = "ha_noi"
    job_type: str = "fulltime"
    seniority: str = "junior"
    education: str = "dai_hoc"
    certifications: list[str] = field(default_factory=list)


@dataclass
class ParsedJob:
    title: str
    requirement: str
    skills: list[str] = field(default_factory=list)
    location: str = "ha_noi"
    job_type: str = "fulltime"
    seniority: str = "junior"
    education: str = "dai_hoc"
    required_certifications: list[str] = field(default_factory=list)


# --- Enum detection maps (order matters: more specific first) ---

_LOCATION_MAP: dict[str, str] = {
    "hồ chí minh": "tp_hcm",
    "ho chi minh": "tp_hcm",
    "tp. hcm": "tp_hcm",
    "tp hcm": "tp_hcm",
    "tp.hcm": "tp_hcm",
    "hcm city": "tp_hcm",
    "hcm": "tp_hcm",
    "đà nẵng": "da_nang",
    "da nang": "da_nang",
    "danang": "da_nang",
    "da_nang": "da_nang",
    "hà nội": "ha_noi",
    "ha noi": "ha_noi",
    "hanoi": "ha_noi",
    "ha_noi": "ha_noi",
}

_JOB_TYPE_MAP: dict[str, str] = {
    "work from home": "remote",
    "wfh": "remote",
    "remote": "remote",
    "part-time": "parttime",
    "part time": "parttime",
    "parttime": "parttime",
    "full-time": "fulltime",
    "full time": "fulltime",
    "fulltime": "fulltime",
}

_SENIORITY_MAP: dict[str, str] = {
    "thực tập sinh": "intern",
    "thực tập": "intern",
    "internship": "intern",
    "intern": "intern",
    "fresh graduate": "fresher",
    "entry-level": "fresher",
    "entry level": "fresher",
    "fresher": "fresher",
    "tech lead": "lead",
    "team lead": "lead",
    "lead": "lead",
    "senior": "senior",
    "sr.": "senior",
    "middle": "mid",
    "mid-level": "mid",
    "mid level": "mid",
    "junior": "junior",
    "jr.": "junior",
}

_EDUCATION_MAP: dict[str, str] = {
    "tiến sĩ": "tien_si",
    "tien_si": "tien_si",
    "doctor": "tien_si",
    "ph.d": "tien_si",
    "phd": "tien_si",
    "thạc sĩ": "thac_si",
    "thac_si": "thac_si",
    "master": "thac_si",
    "m.sc": "thac_si",
    "msc": "thac_si",
    "đại học": "dai_hoc",
    "dai_hoc": "dai_hoc",
    "bachelor": "dai_hoc",
    "b.sc": "dai_hoc",
    "bsc": "dai_hoc",
    "university": "dai_hoc",
    "college": "dai_hoc",
    "lớp 12": "lop_12",
    "lop_12": "lop_12",
    "high school": "lop_12",
    "lớp 9": "lop_9",
    "lop_9": "lop_9",
}

_CERT_PATTERNS: list[str] = [
    r"AWS\s+Certified\s+[\w\s]+",
    r"Google\s+(?:Cloud\s+)?Certified\s+[\w\s]+",
    r"Azure\s+[\w\s]+Certificate(?:d)?",
    r"Certified\s+[\w\s]+Professional",
    r"CKA[DS]?",
    r"PMP",
    r"IELTS",
    r"TOEIC",
    r"TOEFL",
]


def _detect_enum(text_lower: str, mapping: dict[str, str], default: str) -> str:
    for keyword, value in mapping.items():
        if keyword in text_lower:
            return value
    return default


def _extract_title(text: str, filename: str = "") -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) > 3:
            return stripped[:255]
    base = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").strip()
    return (base or "Untitled")[:255]


def _extract_certifications(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for pat in _CERT_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            cert = m.group(0).strip()[:128]
            if cert not in seen:
                seen.add(cert)
                found.append(cert)
    return found


def parse_resume(text: str, filename: str = "") -> ParsedResume:
    from jobconnect.modules.documents.skill_normalizer import extract_skills

    text_lower = text.lower()
    return ParsedResume(
        title=_extract_title(text, filename),
        summary=text[:2000],
        experience=text[2000:4000] if len(text) > 2000 else "",
        skills=extract_skills(text),
        location=_detect_enum(text_lower, _LOCATION_MAP, "ha_noi"),
        job_type=_detect_enum(text_lower, _JOB_TYPE_MAP, "fulltime"),
        seniority=_detect_enum(text_lower, _SENIORITY_MAP, "junior"),
        education=_detect_enum(text_lower, _EDUCATION_MAP, "dai_hoc"),
        certifications=_extract_certifications(text),
    )


def parse_job(text: str, filename: str = "") -> ParsedJob:
    from jobconnect.modules.documents.skill_normalizer import extract_skills

    text_lower = text.lower()
    return ParsedJob(
        title=_extract_title(text, filename),
        requirement=text[:4000],
        skills=extract_skills(text),
        location=_detect_enum(text_lower, _LOCATION_MAP, "ha_noi"),
        job_type=_detect_enum(text_lower, _JOB_TYPE_MAP, "fulltime"),
        seniority=_detect_enum(text_lower, _SENIORITY_MAP, "junior"),
        education=_detect_enum(text_lower, _EDUCATION_MAP, "dai_hoc"),
        required_certifications=_extract_certifications(text),
    )
