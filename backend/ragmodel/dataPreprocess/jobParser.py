import google.generativeai as genai
import json
import re
from ragmodel.config import GEMINI_API_KEY, MODEL

genai.configure(api_key=GEMINI_API_KEY)

def parse_jd(preprocessed_text: str):
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

    resp = genai.GenerativeModel(MODEL).generate_content(prompt)
    out = resp.text.strip()

    # Remove accidental ```json or ```
    out = re.sub(r"```json|```", "", out).strip()

    # Parse safely
    try:
        return json.loads(out)
    except Exception:
        print("\n❌ INVALID JSON FROM JD PARSER:\n", out)
        raise
