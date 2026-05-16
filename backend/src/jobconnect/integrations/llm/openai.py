"""OpenAI-compatible LLM parser adapter.

Calls a chat-completions endpoint with `response_format = json_object` so the
provider returns structured JSON. The adapter then:

1. Parses the JSON.
2. Sanitizes every enum field against the canonical sets (raw unsupported
   values are replaced with safe defaults; they never reach the database).
3. Normalizes skill lists through the Slice 5 alias dictionary so matching
   stays consistent across local/LLM modes.

Failure handling:
- Network/HTTP errors raise `ParserError`.
- JSON decode failures raise `ParserError`.
- Per-field invalid values are quietly defaulted; this is per
  REQUIREMENTS.md §5.4 ("must not invent unsupported enum values").

Configuration (env vars):
- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)
- `OPENAI_TIMEOUT_SECONDS` (default: `30`)
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx

from jobconnect.integrations.llm.base import ParserError
from jobconnect.modules.documents.local_parser import (
    DEFAULT_EDUCATION,
    DEFAULT_JOB_TYPE,
    DEFAULT_LOCATION,
    DEFAULT_SENIORITY,
    EDUCATION_VALUES,
    JOB_TYPE_VALUES,
    LOCATION_VALUES,
    SENIORITY_VALUES,
    ParsedJob,
    ParsedResume,
    validate_enum,
)
from jobconnect.modules.documents.skill_normalizer import normalize_skills

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_DEFAULT_MODEL = "gpt-4o-mini"
_DEFAULT_TIMEOUT = 30


_RESUME_SCHEMA_PROMPT = """You are extracting structured data from a candidate CV.
Return ONLY a JSON object with this exact schema:
{
  "title": string (job title from CV header),
  "summary": string (short professional summary, max 2000 chars),
  "experience": string (work-experience section, max 2000 chars),
  "skills": list of strings (technical skills, lowercase canonical names),
  "location": one of ["ha_noi", "tp_hcm", "da_nang"],
  "job_type": one of ["remote", "fulltime", "parttime"],
  "seniority": one of ["intern", "fresher", "junior", "mid", "senior", "lead"],
  "education": one of ["lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si"],
  "certifications": list of strings (e.g. "AWS Certified Solutions Architect")
}
DO NOT translate the document. DO NOT invent enum values not in the lists above.
If you cannot determine a value, omit the field.
"""

_JOB_SCHEMA_PROMPT = """You are extracting structured data from a job description.
Return ONLY a JSON object with this exact schema:
{
  "title": string (job title),
  "requirement": string (requirements section, max 4000 chars),
  "skills": list of strings (required technical skills, lowercase canonical names),
  "location": one of ["ha_noi", "tp_hcm", "da_nang"],
  "job_type": one of ["remote", "fulltime", "parttime"],
  "seniority": one of ["intern", "fresher", "junior", "mid", "senior", "lead"],
  "education": one of ["lop_9", "lop_12", "dai_hoc", "thac_si", "tien_si"],
  "required_certifications": list of strings
}
DO NOT translate the document. DO NOT invent enum values not in the lists above.
If you cannot determine a value, omit the field.
"""


class OpenAIParser:
    """OpenAI-compatible chat completion adapter for structured CV/JD parsing."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model or os.getenv("OPENAI_MODEL", _DEFAULT_MODEL)
        self._base_url = (base_url or os.getenv("OPENAI_BASE_URL", _DEFAULT_BASE_URL)).rstrip("/")
        self._timeout = float(timeout_seconds if timeout_seconds is not None else os.getenv("OPENAI_TIMEOUT_SECONDS", _DEFAULT_TIMEOUT))
        # parser_version is stable across runs at the same model identifier
        self.parser_version = f"openai-{self._model}-v1"

    # ---- Public Protocol surface -------------------------------------

    def parse_resume(self, text: str, filename: str = "") -> ParsedResume:
        payload = self._call(_RESUME_SCHEMA_PROMPT, text, filename)
        skills = normalize_skills(_string_list(payload.get("skills")))
        return ParsedResume(
            title=_clip(payload.get("title"), filename or "Untitled", 255),
            summary=_clip(payload.get("summary"), text[:2000], 2000),
            experience=_clip(payload.get("experience"), "", 2000),
            skills=skills,
            location=validate_enum(payload.get("location", ""), LOCATION_VALUES, DEFAULT_LOCATION),
            job_type=validate_enum(payload.get("job_type", ""), JOB_TYPE_VALUES, DEFAULT_JOB_TYPE),
            seniority=validate_enum(payload.get("seniority", ""), SENIORITY_VALUES, DEFAULT_SENIORITY),
            education=validate_enum(payload.get("education", ""), EDUCATION_VALUES, DEFAULT_EDUCATION),
            certifications=_string_list(payload.get("certifications"))[:32],
        )

    def parse_job(self, text: str, filename: str = "") -> ParsedJob:
        payload = self._call(_JOB_SCHEMA_PROMPT, text, filename)
        skills = normalize_skills(_string_list(payload.get("skills")))
        return ParsedJob(
            title=_clip(payload.get("title"), filename or "Untitled", 255),
            requirement=_clip(payload.get("requirement"), text[:4000], 4000),
            skills=skills,
            location=validate_enum(payload.get("location", ""), LOCATION_VALUES, DEFAULT_LOCATION),
            job_type=validate_enum(payload.get("job_type", ""), JOB_TYPE_VALUES, DEFAULT_JOB_TYPE),
            seniority=validate_enum(payload.get("seniority", ""), SENIORITY_VALUES, DEFAULT_SENIORITY),
            education=validate_enum(payload.get("education", ""), EDUCATION_VALUES, DEFAULT_EDUCATION),
            required_certifications=_string_list(payload.get("required_certifications"))[:32],
        )

    # ---- HTTP / JSON internals ---------------------------------------

    def _call(self, system_prompt: str, user_text: str, filename: str) -> dict[str, Any]:
        body = {
            "model": self._model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Filename: {filename}\n\n--- DOCUMENT TEXT ---\n{user_text[:12000]}"
                    ),
                },
            ],
            "temperature": 0,
        }
        url = f"{self._base_url}/chat/completions"
        try:
            resp = httpx.post(
                url,
                json=body,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )
        except httpx.HTTPError as exc:
            raise ParserError(f"LLM request failed: {exc}") from exc

        if resp.status_code >= 400:
            raise ParserError(f"LLM returned HTTP {resp.status_code}: {resp.text[:200]}")

        try:
            envelope = resp.json()
            content = envelope["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise ParserError(f"LLM response missing content: {exc}") from exc

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ParserError(f"LLM did not return valid JSON: {exc}") from exc

        if not isinstance(payload, dict):
            raise ParserError("LLM JSON payload must be an object.")
        return payload


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _clip(value: Any, fallback: str, limit: int) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()[:limit]
    return fallback[:limit]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [v.strip() for v in value if isinstance(v, str) and v.strip()]
