"""Pure utility helpers for the hybrid matcher.

Personal/contact/metadata fields such as name, email, phone, user_id,
recruiter_id, created_at, updated_at, pdf_url, status, and visibility must not
be used in hybrid scoring or future embedding-text construction.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from difflib import SequenceMatcher
from typing import Any


def is_empty_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, dict):
        return len(value) == 0
    if isinstance(value, (list, tuple, set, frozenset)):
        return all(is_empty_value(item) for item in value)
    return False


def has_value(value: Any) -> bool:
    return not is_empty_value(value)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    return re.sub(r"\s+", " ", text)


def normalize_array(value: Any) -> tuple[str, ...]:
    if is_empty_value(value):
        return ()
    raw_items: Iterable[Any]
    if isinstance(value, str):
        raw_items = re.split(r"[,;\n]", value)
    elif isinstance(value, Iterable):
        raw_items = value
    else:
        raw_items = (value,)

    result: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = normalize_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return tuple(result)


def safe_join(values: Iterable[Any], separator: str = " ") -> str:
    parts: list[str] = []
    for value in values:
        if is_empty_value(value):
            continue
        if isinstance(value, (list, tuple, set, frozenset)):
            joined = ", ".join(str(item).strip() for item in value if has_value(item))
            if joined:
                parts.append(joined)
        else:
            text = str(value).strip()
            if text:
                parts.append(text)
    return normalize_text(separator.join(parts))


def should_skip_group(job_value: Any, cv_value: Any) -> bool:
    """Skip when there is no JD-side requirement to compare.

    This covers both-empty fields and JD-empty/CV-present fields. The latter
    should not penalize candidates because the job did not ask for that signal.
    """
    return is_empty_value(job_value)


def normalize_weights(valid_groups: dict[str, float]) -> dict[str, float]:
    total = sum(weight for weight in valid_groups.values() if weight > 0)
    if total <= 0:
        return {}
    return {
        group: weight / total
        for group, weight in valid_groups.items()
        if weight > 0
    }


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def text_similarity(job_text: str, cv_text: str) -> float:
    """Deterministic fallback text similarity on a 0..100 scale."""
    left = normalize_text(job_text)
    right = normalize_text(cv_text)
    if not left or not right:
        return 0.0

    left_tokens = set(re.findall(r"[\w.+#]+", left))
    right_tokens = set(re.findall(r"[\w.+#]+", right))
    if left_tokens and right_tokens:
        jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    else:
        jaccard = 0.0
    sequence = SequenceMatcher(None, left, right).ratio()
    return clamp_score(((jaccard * 0.7) + (sequence * 0.3)) * 100.0)
