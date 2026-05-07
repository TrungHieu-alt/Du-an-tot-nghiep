"""Score computation helpers for Matching V2.

All functions are pure (no I/O, no side effects) and directly unit-testable.

Formula source: docs/REQUIREMENTS.md §3 (FR3).
"""

from __future__ import annotations

from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def cosine_similarity(
    a: Optional[list[float]],
    b: Optional[list[float]],
) -> float:
    """Return cosine similarity clamped to [0, 1].

    Returns 0.0 if either vector is None, empty, or has zero magnitude.
    Negative cosine means no positive semantic match in this prototype, so it
    is clamped to 0.0 to keep score components inside the API contract.
    """
    if a is None or b is None:
        return 0.0
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    if va.size == 0 or vb.size == 0:
        return 0.0
    na = float(np.linalg.norm(va))
    nb = float(np.linalg.norm(vb))
    if na == 0.0 or nb == 0.0:
        return 0.0
    raw = float(np.dot(va, vb) / (na * nb))
    return max(0.0, min(1.0, raw))


# ---------------------------------------------------------------------------
# Exact skill overlap
# ---------------------------------------------------------------------------

def exact_overlap_ratio(
    skills_a: tuple[str, ...] | list[str],
    skills_b: tuple[str, ...] | list[str],
) -> float:
    """Normalised exact overlap ratio in [0, 1].

    Normalisation: |intersection| / max(|A|, |B|).
    Skills are normalised to lowercase + stripped before comparison.
    Returns 0.0 when either set is empty.
    """
    set_a = {s.lower().strip() for s in skills_a if s.strip()}
    set_b = {s.lower().strip() for s in skills_b if s.strip()}
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    return len(intersection) / max(len(set_a), len(set_b))


def matched_skills_sorted(
    skills_a: tuple[str, ...] | list[str],
    skills_b: tuple[str, ...] | list[str],
) -> list[str]:
    """Return sorted list of skill tokens present in both sets (normalised)."""
    set_a = {s.lower().strip() for s in skills_a if s.strip()}
    set_b = {s.lower().strip() for s in skills_b if s.strip()}
    return sorted(set_a & set_b)


# ---------------------------------------------------------------------------
# Component formulas
# ---------------------------------------------------------------------------

def compute_skills_score(semantic: float, exact: float) -> float:
    """skills_score = 0.6 * semantic_skills + 0.4 * exact_overlap_ratio"""
    return 0.6 * semantic + 0.4 * exact


def compute_final_score(
    title: float,
    skills: float,
    req_exp: float,
    req_summary: float,
) -> float:
    """final_score = 0.35*title + 0.35*skills + 0.20*req_exp + 0.10*req_summary.

    bonus_exact_skill = 0 and penalty_missing_required = 0 per REQUIREMENTS.md §9.
    """
    return 0.35 * title + 0.35 * skills + 0.20 * req_exp + 0.10 * req_summary
