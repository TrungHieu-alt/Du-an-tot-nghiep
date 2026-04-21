import google.generativeai as genai
import json
import re
import logging
from ragmodel.config import GEMINI_API_KEY, MODEL

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Set up logging
logger = logging.getLogger(__name__)

def evaluate_match(jd_text: str, cv_text: str) -> dict:
    """
    Evaluate how well a CV matches a Job Description using LLM.
    
    Args:
        jd_text: Full text of the Job Description
        cv_text: Full text of the CV
    
    Returns:
        Dictionary with:
        - score (int): Match score from 0-100
        - reason (str): Explanation of the match
    
    Raises:
        ValueError: If LLM returns invalid JSON
        Exception: If API call fails
    """
    prompt = f"""
Evaluate how well the CV matches the Job Description.

Return JSON ONLY (no markdown, no code blocks):

{{
  "score": 0,
  "reason": ""
}}

Score rule:
- 0–100, where higher = better match
- Consider: skills match, experience level, job title relevance, location compatibility
- Be specific in your reasoning

TEXT_JD:
{jd_text}

TEXT_CV:
{cv_text}
"""

    try:
        # Call Gemini API
        response = genai.GenerativeModel(MODEL).generate_content(prompt)
        output = response.text.strip()

        # Remove markdown code blocks if present
        output = re.sub(r"```json\s*|```\s*", "", output).strip()

        # Parse JSON
        result = json.loads(output)
        
        # Validate structure
        if "score" not in result or "reason" not in result:
            raise ValueError("Missing required fields: score or reason")
        
        # Validate score is a number
        score = float(result["score"])
        if not (0 <= score <= 100):
            logger.warning(f"LLM returned score outside [0,100]: {score}")
        
        return {
            "score": score,
            "reason": str(result["reason"])
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from LLM: {output[:200]}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    
    except Exception as e:
        logger.error(f"LLM evaluation failed: {e}")
        raise