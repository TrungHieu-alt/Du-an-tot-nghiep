import json
import re
import logging
from ragmodel.config import MODEL, AI_MODE
from ragmodel.logics.ai_error_utils import log_quota_limit_if_detected
from ragmodel.logics.gemini_client import generate_text

# Set up logging
logger = logging.getLogger(__name__)


def _strip_json_fence(output: str) -> str:
    return re.sub(r"```json\s*|```\s*", "", output).strip()

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
    if AI_MODE != "live":
        raise RuntimeError("LLM evaluation disabled when AI_MODE is not 'live'")

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
        output = generate_text(prompt, model=MODEL)
        output = _strip_json_fence(output)

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
        log_quota_limit_if_detected(logger, e, stage="matching_llm_evaluate", model=MODEL)
        logger.error(f"LLM evaluation failed: {e}")
        raise


def evaluate_match_batch(
    anchor_text: str,
    candidate_texts: list[str],
    anchor_label: str = "JOB_DESCRIPTION",
    candidate_label: str = "CANDIDATE",
) -> list[dict]:
    """
    Evaluate multiple CV/JD texts against one JD text using a single LLM prompt.
    Returns one result per candidate in the same order.
    """
    if AI_MODE != "live":
        raise RuntimeError("LLM evaluation disabled when AI_MODE is not 'live'")
    if not candidate_texts:
        return []

    candidates_block = "\n\n".join(
        [f"[CANDIDATE_{idx}]\n{text}" for idx, text in enumerate(candidate_texts)]
    )
    prompt = f"""
Evaluate how well each {candidate_label} matches the {anchor_label}.

Return JSON ONLY in this exact shape:
{{
  "results": [
    {{"index": 0, "score": 0, "reason": ""}}
  ]
}}

Rules:
- score: 0..100
- include one result for every candidate index from 0 to {len(candidate_texts) - 1}
- reason must be concise and specific
- do not omit or reorder indexes

{anchor_label}:
{anchor_text}

CANDIDATES:
{candidates_block}
"""
    try:
        output = _strip_json_fence(generate_text(prompt, model=MODEL))
        parsed = json.loads(output)
        results = parsed.get("results")
        if not isinstance(results, list):
            raise ValueError("Missing 'results' list in batch response")

        indexed = {}
        for row in results:
            if not isinstance(row, dict) or "index" not in row:
                continue
            idx = int(row["index"])
            indexed[idx] = {
                "score": float(row.get("score", 0)),
                "reason": str(row.get("reason", "")),
            }

        normalized = []
        for i in range(len(candidate_texts)):
            item = indexed.get(i, {"score": 0.0, "reason": "Missing batch item"})
            score = max(0.0, min(100.0, float(item["score"])))
            normalized.append({"score": score, "reason": item["reason"]})
        return normalized
    except Exception as e:
        log_quota_limit_if_detected(logger, e, stage="matching_llm_evaluate_batch", model=MODEL)
        logger.error(f"LLM batch evaluation failed: {e}")
        raise
