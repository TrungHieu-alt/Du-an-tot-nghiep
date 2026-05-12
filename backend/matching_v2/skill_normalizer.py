"""Skill normalization and alias handling for hybrid matching."""

from __future__ import annotations

import re
from typing import Iterable

from .hybrid_utils import normalize_text


SKILL_ALIASES = {
    "js": "javascript",
    "javascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    "express.js": "express.js",
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "ai": "artificial intelligence",
    "ml": "machine learning",
    "reactjs": "react",
    "react": "react",
    "nextjs": "next.js",
    "next.js": "next.js",
    "vuejs": "vue.js",
    "vue.js": "vue.js",
}


def _alias_key(value: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", "", value.lower())


def normalize_skill(value: str) -> str:
    text = normalize_text(value)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip(" .,;:/\\|")
    if not text:
        return ""
    direct = SKILL_ALIASES.get(text)
    if direct:
        return direct
    compact = _alias_key(text)
    return SKILL_ALIASES.get(compact, text)


def normalize_skills(values: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        skill = normalize_skill(value)
        if not skill or skill in seen:
            continue
        seen.add(skill)
        result.append(skill)
    return tuple(result)


def skill_coverage(job_skills: Iterable[str], cv_skills: Iterable[str]) -> tuple[float, list[str]]:
    """Return JD-skill coverage and sorted matched canonical skills."""
    job_set = set(normalize_skills(job_skills))
    cv_set = set(normalize_skills(cv_skills))
    if not job_set:
        return 0.0, []
    matched = sorted(job_set & cv_set)
    return len(matched) / len(job_set), matched
