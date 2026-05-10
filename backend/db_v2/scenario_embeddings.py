"""Deterministic local embeddings for the Matching V2 scenario dataset.

The generator is intentionally small and dependency-free. It builds a
field-specific bag-of-features from the scenario JSON, assigns stable feature
dimensions, and emits normalized 384-dimensional vectors.

No network calls. No constant vectors.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections import defaultdict
from typing import Any


EMBEDDING_DIM = 384

TITLE_SPACE = "title"
SKILLS_SPACE = "skills"
NARRATIVE_SPACE = "narrative"

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "for",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "by",
    "from",
    "role",
    "team",
    "work",
    "works",
    "working",
    "years",
    "year",
    "candidate",
    "profile",
    "job",
}

_CONCEPT_ALIASES: dict[str, tuple[str, ...]] = {
    # Backend and DevOps
    "backend": ("backend_platform",),
    "api": ("backend_platform",),
    "apis": ("backend_platform",),
    "fastapi": ("backend_platform",),
    "postgres": ("backend_platform", "database"),
    "python": ("backend_platform", "data_ml"),
    "devops": ("devops_cloud",),
    "sre": ("devops_cloud",),
    "reliability": ("devops_cloud",),
    "platform": ("devops_cloud", "backend_platform"),
    "docker": ("devops_cloud",),
    "kubernetes": ("devops_cloud",),
    "terraform": ("devops_cloud",),
    "aws": ("devops_cloud",),
    "ci": ("devops_cloud",),
    "cd": ("devops_cloud",),
    "observability": ("devops_cloud",),
    "monitoring": ("devops_cloud",),
    "incident": ("devops_cloud",),
    "linux": ("devops_cloud",),
    "cka": ("devops_cloud",),
    "saa": ("devops_cloud",),
    # Frontend
    "frontend": ("frontend_web",),
    "react": ("frontend_web",),
    "typescript": ("frontend_web",),
    "vite": ("frontend_web",),
    "css": ("frontend_web",),
    "ui": ("frontend_web",),
    "ux": ("frontend_web",),
    "web": ("frontend_web",),
    "accessibility": ("frontend_web",),
    "component": ("frontend_web",),
    "components": ("frontend_web",),
    "design": ("frontend_web",),
    "system": ("frontend_web",),
    "performance": ("frontend_web",),
    # AI and data
    "ai": ("data_ml",),
    "ml": ("data_ml",),
    "machine": ("data_ml",),
    "learning": ("data_ml",),
    "data": ("data_ml",),
    "pandas": ("data_ml",),
    "tensorflow": ("data_ml",),
    "pytorch": ("data_ml",),
    "statistics": ("data_ml",),
    "statistical": ("data_ml",),
    "feature": ("data_ml",),
    "model": ("data_ml",),
    "models": ("data_ml",),
    "analytics": ("data_ml",),
    "sql": ("data_ml", "database"),
    "mlops": ("data_ml", "devops_cloud"),
    # Product and BA
    "product": ("product_ba",),
    "business": ("product_ba",),
    "analysis": ("product_ba",),
    "analyst": ("product_ba",),
    "ba": ("product_ba",),
    "roadmap": ("product_ba",),
    "story": ("product_ba",),
    "stories": ("product_ba",),
    "jira": ("product_ba",),
    "stakeholder": ("product_ba",),
    "stakeholders": ("product_ba",),
    "process": ("product_ba",),
    "backlog": ("product_ba",),
    "discovery": ("product_ba",),
    # Sales and marketing
    "sales": ("sales_marketing",),
    "marketing": ("sales_marketing",),
    "growth": ("sales_marketing",),
    "crm": ("sales_marketing",),
    "lead": ("sales_marketing", "frontend_web"),
    "generation": ("sales_marketing",),
    "content": ("sales_marketing",),
    "campaign": ("sales_marketing",),
    "campaigns": ("sales_marketing",),
    "google": ("sales_marketing",),
    "ads": ("sales_marketing",),
    "email": ("sales_marketing",),
    "hubspot": ("sales_marketing",),
    "customer": ("sales_marketing",),
    "success": ("sales_marketing",),
    # Finance, HR, Admin
    "finance": ("finance_hr_admin",),
    "financial": ("finance_hr_admin",),
    "hr": ("finance_hr_admin",),
    "payroll": ("finance_hr_admin",),
    "accounting": ("finance_hr_admin",),
    "invoice": ("finance_hr_admin",),
    "admin": ("finance_hr_admin",),
    "administration": ("finance_hr_admin",),
    "excel": ("finance_hr_admin",),
    "compliance": ("finance_hr_admin",),
    "recruitment": ("finance_hr_admin",),
    "office": ("finance_hr_admin",),
    "operations": ("finance_hr_admin", "product_ba"),
}


def normalize_terms(values: list[str] | tuple[str, ...] | None) -> list[str]:
    """Lowercase, trim, and deduplicate string arrays while preserving order."""
    if not values:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value).strip().lower()
        normalized = re.sub(r"\s+", "_", normalized)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def normalize_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the dataset with skills and cert arrays normalized."""
    normalized: dict[str, Any] = {
        key: value
        for key, value in dataset.items()
        if key not in {"jobs", "candidates"}
    }
    normalized["jobs"] = []
    for job in dataset.get("jobs", []):
        item = dict(job)
        item["skills"] = normalize_terms(item.get("skills", []))
        item["required_certifications"] = normalize_terms(
            item.get("required_certifications", [])
        )
        normalized["jobs"].append(item)

    normalized["candidates"] = []
    for cv in dataset.get("candidates", []):
        item = dict(cv)
        item["skills"] = normalize_terms(item.get("skills", []))
        item["certifications"] = normalize_terms(item.get("certifications", []))
        normalized["candidates"].append(item)
    return normalized


def build_embedding_payload(dataset: dict[str, Any]) -> dict[str, dict[int, dict[str, list[float] | None]]]:
    """Generate job and candidate embeddings for a normalized dataset."""
    spaces = _build_feature_spaces(dataset)
    dim_maps = _build_dimension_maps(spaces)
    partial_case = dataset.get("partial_embedding_case", {})
    missing_embedding_cv_id = (
        int(partial_case["cv_id"])
        if partial_case.get("mode") == "missing_row" and "cv_id" in partial_case
        else None
    )

    job_embeddings: dict[int, dict[str, list[float] | None]] = {}
    for job in dataset["jobs"]:
        job_id = int(job["job_id"])
        job_embeddings[job_id] = {
            "emb_title": _embed_text(job["title"], TITLE_SPACE, dim_maps[TITLE_SPACE]),
            "emb_skills": _embed_skills(job["skills"], dim_maps[SKILLS_SPACE]),
            "emb_requirement": _embed_text(
                job["requirement"], NARRATIVE_SPACE, dim_maps[NARRATIVE_SPACE]
            ),
        }

    candidate_embeddings: dict[int, dict[str, list[float] | None]] = {}
    for cv in dataset["candidates"]:
        cv_id = int(cv["cv_id"])
        if cv_id == missing_embedding_cv_id:
            continue
        fields: dict[str, list[float] | None] = {
            "emb_title": _embed_text(cv["title"], TITLE_SPACE, dim_maps[TITLE_SPACE]),
            "emb_skills": _embed_skills(cv["skills"], dim_maps[SKILLS_SPACE]),
            "emb_summary": _embed_text(
                cv["summary"], NARRATIVE_SPACE, dim_maps[NARRATIVE_SPACE]
            ),
            "emb_experience": _embed_text(
                cv["experience"], NARRATIVE_SPACE, dim_maps[NARRATIVE_SPACE]
            ),
        }
        if partial_case.get("cv_id") == cv_id:
            field = partial_case.get("field")
            if field in fields and partial_case.get("mode") == "null":
                fields[field] = None
        candidate_embeddings[cv_id] = fields

    return {"jobs": job_embeddings, "candidates": candidate_embeddings}


def stable_embedding_hash(
    embeddings: dict[str, dict[int, dict[str, list[float] | None]]]
) -> str:
    """Return a deterministic hash of generated vectors for validation output."""
    parts: list[str] = []
    for section in ("jobs", "candidates"):
        for entity_id in sorted(embeddings[section]):
            fields = embeddings[section][entity_id]
            for field_name in sorted(fields):
                vector = fields[field_name]
                if vector is None:
                    rendered = "null"
                else:
                    rendered = ",".join(f"{value:.8f}" for value in vector)
                parts.append(f"{section}:{entity_id}:{field_name}:{rendered}")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def vector_to_pgvector(vector: list[float] | None) -> str | None:
    """Serialize a vector for pgvector text input."""
    if vector is None:
        return None
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"


def _build_feature_spaces(dataset: dict[str, Any]) -> dict[str, set[str]]:
    spaces: dict[str, set[str]] = {
        TITLE_SPACE: set(),
        SKILLS_SPACE: set(),
        NARRATIVE_SPACE: set(),
    }
    for job in dataset["jobs"]:
        spaces[TITLE_SPACE].update(_features_for_text(job["title"], TITLE_SPACE))
        spaces[SKILLS_SPACE].update(_features_for_skills(job["skills"]))
        spaces[NARRATIVE_SPACE].update(
            _features_for_text(job["requirement"], NARRATIVE_SPACE)
        )
    for cv in dataset["candidates"]:
        spaces[TITLE_SPACE].update(_features_for_text(cv["title"], TITLE_SPACE))
        spaces[SKILLS_SPACE].update(_features_for_skills(cv["skills"]))
        spaces[NARRATIVE_SPACE].update(
            _features_for_text(cv["summary"], NARRATIVE_SPACE)
        )
        spaces[NARRATIVE_SPACE].update(
            _features_for_text(cv["experience"], NARRATIVE_SPACE)
        )
    return spaces


def _build_dimension_maps(spaces: dict[str, set[str]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for space, features in spaces.items():
        if len(features) > EMBEDDING_DIM:
            raise ValueError(
                f"{space} feature count {len(features)} exceeds {EMBEDDING_DIM}"
            )
        ordered = sorted(
            features,
            key=lambda feature: hashlib.sha256(
                f"{space}:{feature}".encode("utf-8")
            ).hexdigest(),
        )
        result[space] = {feature: idx for idx, feature in enumerate(ordered)}
    return result


def _embed_text(text: str, space: str, dim_map: dict[str, int]) -> list[float]:
    return _normalize_vector(_weighted_vector(_features_for_text(text, space), dim_map))


def _embed_skills(skills: list[str], dim_map: dict[str, int]) -> list[float]:
    return _normalize_vector(_weighted_vector(_features_for_skills(skills), dim_map))


def _weighted_vector(features: dict[str, float], dim_map: dict[str, int]) -> list[float]:
    vector = [0.0] * EMBEDDING_DIM
    for feature, weight in features.items():
        idx = dim_map.get(feature)
        if idx is not None:
            vector[idx] += weight
    return vector


def _normalize_vector(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        return vector
    return [value / norm for value in vector]


def _features_for_text(text: str, space: str) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    tokens = _tokens(text)
    token_weight = 1.0 if space == TITLE_SPACE else 0.8
    concept_weight = 0.55 if space == TITLE_SPACE else 0.7
    for token in tokens:
        weights[f"tok:{token}"] += token_weight
        for concept in _concepts_for(token):
            weights[f"concept:{concept}"] += concept_weight
    return dict(weights)


def _features_for_skills(skills: list[str]) -> dict[str, float]:
    weights: dict[str, float] = defaultdict(float)
    for skill in skills:
        normalized = normalize_terms([skill])
        if not normalized:
            continue
        full = normalized[0]
        weights[f"skill:{full}"] += 1.3
        for token in _tokens(full):
            weights[f"tok:{token}"] += 0.8
            for concept in _concepts_for(token):
                weights[f"concept:{concept}"] += 0.9
        for concept in _concepts_for(full):
            weights[f"concept:{concept}"] += 0.9
    return dict(weights)


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower().replace("_", " "))
        if token and token not in _STOPWORDS
    ]


def _concepts_for(token: str) -> tuple[str, ...]:
    return _CONCEPT_ALIASES.get(token, ())
