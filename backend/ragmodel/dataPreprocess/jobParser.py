import json
import re
import logging
from ragmodel.config import MODEL, AI_MODE
from ragmodel.logics.ai_error_utils import log_quota_limit_if_detected
from ragmodel.logics.gemini_client import generate_text

logger = logging.getLogger(__name__)


def _extract_first(patterns, text):
    for pat in patterns:
        match = re.search(pat, text, flags=re.I)
        if match:
            return match.group(1).strip()
    return ""


def _extract_skills(text):
    skills_line = _extract_first(
        [r"(?:^|\n)\s*(?:skills?|requirements?)\s*[:\-]\s*(.+?)(?:\n|$)"],
        text,
    )
    if skills_line:
        items = [s.strip(" .,-") for s in re.split(r"[,;/|]", skills_line) if s.strip()]
        return list(dict.fromkeys(items))[:20]

    common = [
        "python", "java", "javascript", "typescript", "react", "node", "sql", "mongodb",
        "docker", "kubernetes", "aws", "git", "fastapi", "django", "flask", "pandas",
    ]
    low = text.lower()
    found = [s for s in common if re.search(rf"\b{re.escape(s)}\b", low)]
    return found[:20]


def _mock_parse_jd(preprocessed_text: str):
    job_description = _extract_first(
        [r"(?:^|\n)\s*(?:job description|about the role)\s*[:\-]\s*(.+?)(?:\n|$)"],
        preprocessed_text,
    )
    job_requirement = _extract_first(
        [r"(?:^|\n)\s*(?:requirements?|required skills?)\s*[:\-]\s*(.+?)(?:\n|$)"],
        preprocessed_text,
    )
    job_title = _extract_first(
        [r"(?:^|\n)\s*(?:title|job title|role|position)\s*[:\-]\s*(.+?)(?:\n|$)"],
        preprocessed_text,
    )
    location = _extract_first(
        [r"(?:^|\n)\s*(?:location|address)\s*[:\-]\s*(.+?)(?:\n|$)"],
        preprocessed_text,
    )

    return {
        "job_description": job_description,
        "job_requirement": job_requirement,
        "job_title": job_title,
        "skills": _extract_skills(preprocessed_text),
        "full_text": preprocessed_text,
        "location": location,
    }

def parse_jd(preprocessed_text: str):
    if AI_MODE != "live":
        return _mock_parse_jd(preprocessed_text)

    prompt = f"""
Strictly parse the JOB POSTING into the following JSON format:

{{
  "job_description": "",
  "job_requirement": "",
  "job_title": "",
  "skills": [],
  "full_text": "",
  "location": ""
}}

Rules:
- "skills" MUST be a list of strings.
- Do NOT hallucinate. If something does not appear in the text, return "" or [].
- Use EXACTLY these keys.
- full_text = the entire input text.
- Job title must be short and taken exactly from the text.

TEXT:
{preprocessed_text}
"""

    try:
        out = generate_text(prompt, model=MODEL)
    except Exception as e:
        log_quota_limit_if_detected(logger, e, stage="job_parse", model=MODEL)
        raise

    # Remove accidental ```json or ```
    out = re.sub(r"```json|```", "", out).strip()

    # Parse safely
    try:
        return json.loads(out)
    except Exception:
        print("\n❌ INVALID JSON FROM JD PARSER:\n", out)
        raise
