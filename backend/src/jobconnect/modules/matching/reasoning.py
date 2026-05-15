"""Deterministic, rule-based reasoning builder for production matching.

No LLM. Reasoning is assembled from score components, skill overlaps,
and a list of fields whose embeddings were missing.

Source: docs/REQUIREMENTS.md §3 (FR4).
"""

from __future__ import annotations


def build_reasoning(
    title_score: float,
    skills_score: float,
    req_exp_score: float,
    req_summary_score: float,
    matched_skills: list[str],
    missing_emb_fields: list[str],
) -> str:
    """Build a human-readable reasoning string deterministically.

    Args:
        title_score: Computed title similarity component.
        skills_score: Computed blended skills component.
        req_exp_score: Computed requirement-vs-experience component.
        req_summary_score: Computed requirement-vs-summary component.
        matched_skills: Sorted list of exact-matched skill tokens.
        missing_emb_fields: Names of embedding fields that were None (scored 0).

    Returns:
        A single string composed of 2-4 deterministic sentences.
    """
    parts: list[str] = []

    # 1. Identify the dominant score component.
    components = [
        ("title", title_score),
        ("skills", skills_score),
        ("requirement↔experience", req_exp_score),
        ("requirement↔summary", req_summary_score),
    ]
    best_name, best_val = max(components, key=lambda x: x[1])
    parts.append(
        f"Strongest signal: '{best_name}' (score {best_val:.3f})."
    )

    # 2. Exact skill overlap.
    if matched_skills:
        skill_list = ", ".join(matched_skills)
        parts.append(
            f"Exact skill matches ({len(matched_skills)}): {skill_list}."
        )
    else:
        parts.append("No exact skill overlap between JD and CV.")

    # 3. Missing embeddings — required by spec when any field scored 0 due to absence.
    if missing_emb_fields:
        field_list = ", ".join(missing_emb_fields)
        parts.append(
            f"Missing embeddings for: {field_list} — those components defaulted to 0."
        )

    return " ".join(parts)
