import google.generativeai as genai
import json
import re
from ragmodel.config import GEMINI_API_KEY, MODEL

genai.configure(api_key=GEMINI_API_KEY)

# ------------------------------------
# Parse resume into 5 final fields
# ------------------------------------
def parse_resume(preprocessed_text: str):
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

    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    out = resp.text.strip()

    # Remove accidental ```json or ```
    out = re.sub(r"```json|```", "", out).strip()

    # Safe JSON parse
    try:
        print("---- Resume Parsed JSON ----", out[:100])
        return json.loads(out)
    except Exception:
        print("\n❌ INVALID JSON FROM RESUME PARSER:\n", out)
        raise
