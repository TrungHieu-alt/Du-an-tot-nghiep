"""Skill alias normalization — maps common variants to canonical labels.

~80 high-impact entries per REQUIREMENTS.md §5.3.
Matching uses normalized labels; raw extracted text is preserved elsewhere.
"""
from __future__ import annotations

import re

# Alias → canonical label mapping (lowercase keys, original-case values)
_ALIAS_MAP: dict[str, str] = {
    # JavaScript / TypeScript
    "javascript": "javascript",
    "js": "javascript",
    "typescript": "typescript",
    "ts": "typescript",
    # React
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "react": "react",
    # Vue
    "vuejs": "vue",
    "vue.js": "vue",
    "vue js": "vue",
    "vue": "vue",
    # Angular
    "angularjs": "angular",
    "angular.js": "angular",
    "angular": "angular",
    # Node.js
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "node js": "nodejs",
    # Python
    "python": "python",
    "python3": "python",
    # Django / Flask / FastAPI
    "django": "django",
    "flask": "flask",
    "fastapi": "fastapi",
    # Java / JVM
    "java": "java",
    "spring": "spring framework",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "kotlin": "kotlin",
    "scala": "scala",
    # C family
    "c++": "c++",
    "cpp": "c++",
    "c#": "c#",
    "csharp": "c#",
    ".net": ".net",
    "dotnet": ".net",
    "asp.net": "asp.net",
    # PHP / Ruby
    "php": "php",
    "laravel": "laravel",
    "ruby": "ruby",
    "ruby on rails": "ruby on rails",
    "rails": "ruby on rails",
    "ror": "ruby on rails",
    # Go / Rust
    "golang": "go",
    "go": "go",
    "rust": "rust",
    # Swift / ObjC
    "swift": "swift",
    "objective-c": "objective-c",
    "objc": "objective-c",
    # Databases
    "postgresql": "postgresql",
    "postgres": "postgresql",
    "mysql": "mysql",
    "mongodb": "mongodb",
    "mongo": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "sqlite": "sqlite",
    "mssql": "mssql",
    "sql server": "mssql",
    "oracle": "oracle",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    # ML / AI
    "pytorch": "pytorch",
    "tensorflow": "tensorflow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "keras": "keras",
    "numpy": "numpy",
    "pandas": "pandas",
    # Cloud
    "aws": "aws",
    "amazon web services": "aws",
    "azure": "azure",
    "gcp": "gcp",
    "google cloud": "gcp",
    # DevOps / Infra
    "docker": "docker",
    "kubernetes": "kubernetes",
    "k8s": "kubernetes",
    "terraform": "terraform",
    "ansible": "ansible",
    "jenkins": "jenkins",
    "github actions": "github actions",
    "ci/cd": "ci/cd",
    "linux": "linux",
    # Mobile
    "android": "android",
    "ios": "ios",
    "react native": "react native",
    "flutter": "flutter",
    "dart": "dart",
    # Testing
    "jest": "jest",
    "pytest": "pytest",
    "selenium": "selenium",
    # APIs
    "rest": "rest api",
    "restful": "rest api",
    "graphql": "graphql",
    "grpc": "grpc",
    # Data / Streaming
    "spark": "apache spark",
    "apache spark": "apache spark",
    "kafka": "apache kafka",
    "apache kafka": "apache kafka",
    "airflow": "apache airflow",
    "apache airflow": "apache airflow",
    # VCS
    "git": "git",
    "github": "github",
    "gitlab": "gitlab",
}


def normalize_skills(skills: list[str]) -> list[str]:
    """Map each skill string to its canonical label, deduplicating."""
    result: list[str] = []
    seen: set[str] = set()
    for raw in skills:
        key = raw.strip().lower()
        canonical = _ALIAS_MAP.get(key, raw.strip())
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def extract_skills(text: str) -> list[str]:
    """Scan text for known skill aliases and return deduplicated canonical labels."""
    text_lower = text.lower()
    found: list[str] = []
    seen: set[str] = set()
    # Sort by descending length so multi-word aliases match before sub-strings
    for alias in sorted(_ALIAS_MAP, key=len, reverse=True):
        # Lookbehind keeps '.' to avoid partial matches inside dotted names (e.g. react.js).
        # Lookahead excludes only alphanumeric/underscore so skills at end-of-sentence match.
        pattern = r"(?<![a-z0-9_.])" + re.escape(alias) + r"(?![a-z0-9_])"
        if re.search(pattern, text_lower):
            canonical = _ALIAS_MAP[alias]
            if canonical not in seen:
                seen.add(canonical)
                found.append(canonical)
    return found
