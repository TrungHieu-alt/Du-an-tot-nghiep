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
    # Prefer explicit "Skills:" lines, then fallback to keyword scan.
    skills_line = _extract_first(
        [r"(?:^|\n)\s*skills?\s*[:\-]\s*(.+?)(?:\n|$)"],
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


def _mock_parse_resume(preprocessed_text: str):
    summary = _extract_first(
        [r"(?:^|\n)\s*(?:summary|profile)\s*[:\-]\s*(.+?)(?:\n|$)"],
        preprocessed_text,
    )
    experience = _extract_first(
        [r"(?:^|\n)\s*(?:experience|work experience)\s*[:\-]\s*(.+?)(?:\n|$)"],
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
        "summary": summary,
        "experience": experience,
        "job_title": job_title,
        "skills": _extract_skills(preprocessed_text),
        "full_text": preprocessed_text,
        "location": location,
    }

# ------------------------------------
# Parse resume into 5 final fields
# ------------------------------------
def parse_resume(preprocessed_text: str):
    if AI_MODE != "live":
        return _mock_parse_resume(preprocessed_text)

    prompt = f"""
You are a strict CV/Resume parser.
Extract ONLY what exists in the text.
Return JSON EXACTLY in this structure:

{{
  "summary": "",
  "experience": "",
  "job_title": "",
  "skills": [],
  "full_text": "",
  "location": ""
}}

Rules:
- "skills" MUST be a list of strings.
- job_title must be SHORT and directly extracted (engineer, developer, marketer…).
- Do NOT hallucinate. If absent → return "" or [].
- full_text = entire preprocessed text.

TEXT:
{preprocessed_text}
"""

    try:
        out = generate_text(prompt, model=MODEL)
    except Exception as e:
        log_quota_limit_if_detected(logger, e, stage="resume_parse", model=MODEL)
        raise

    # Remove accidental ```json or ```
    out = re.sub(r"```json|```", "", out).strip()

    # Safe JSON parse
    try:
        print("---- Resume Parsed JSON ----", out[:100])
        return json.loads(out)
    except Exception:
        print("\n❌ INVALID JSON FROM RESUME PARSER:\n", out)
        raise
