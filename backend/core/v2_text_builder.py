"""Build structured V2 preparation text from normal Job/CV rows.

The builders intentionally exclude private contact fields and normal-only
metadata. They return readable text that can be stored on the V2 rows and used
for V2 embedding generation.
"""

from __future__ import annotations

from typing import Any

from core.preprocess import analyze_text_quality, preprocess_text


def build_candidate_profile_text(cv: dict[str, Any]) -> str:
    lines: list[str] = ["Candidate Profile:"]
    _add_field(lines, "Headline", cv.get("headline"))
    _add_field(lines, "Summary", cv.get("summary"))
    _add_field(lines, "Target role", cv.get("target_role") or cv.get("targetRole"))
    _add_field(lines, "Industry", cv.get("industry"))
    _add_field(lines, "Occupation group", cv.get("occupation_group") or cv.get("occupationGroup"))
    _add_field(lines, "Career level", cv.get("career_level") or cv.get("careerLevel"))
    _add_field(
        lines,
        "Years of experience",
        cv.get("years_of_experience") if cv.get("years_of_experience") is not None else cv.get("yearsOfExperience"),
    )

    _add_skill_section(lines, "Skills", cv.get("skills"))
    _add_list_section(lines, "Tools and technologies", cv.get("tools_and_technologies") or cv.get("toolsAndTechnologies"))
    _add_list_section(lines, "Domain knowledge", cv.get("domain_knowledge") or cv.get("domainKnowledge"))
    _add_experience_section(lines, cv.get("experiences"))
    _add_project_section(lines, cv.get("projects"))
    return preprocess_text("\n".join(lines))


def build_job_post_text(job: dict[str, Any]) -> str:
    lines: list[str] = ["Job Post:"]
    _add_field(lines, "Title", job.get("title"))
    _add_field(lines, "Industry", job.get("industry"))
    _add_field(lines, "Occupation group", job.get("occupation_group") or job.get("occupationGroup"))
    _add_field(lines, "Seniority", job.get("seniority"))
    _add_field(
        lines,
        "Required experience years",
        job.get("experience_years") if job.get("experience_years") is not None else job.get("experienceYears"),
    )

    _add_text_block(lines, "Description", job.get("description"))
    _add_list_section(lines, "Responsibilities", job.get("responsibilities"))
    _add_list_section(lines, "Requirements", job.get("requirements"))
    _add_list_section(lines, "Nice to have", job.get("nice_to_have") or job.get("niceToHave"))
    _add_skill_section(lines, "Skills", job.get("skills"))
    _add_skill_section(lines, "Must-have skills", job.get("must_have_skills") or job.get("mustHaveSkills"))
    _add_skill_section(lines, "Nice-to-have skills", job.get("nice_to_have_skills") or job.get("niceToHaveSkills"))
    _add_list_section(lines, "Tools and technologies", job.get("tools_and_technologies") or job.get("toolsAndTechnologies"))
    _add_list_section(lines, "Domain knowledge", job.get("domain_knowledge") or job.get("domainKnowledge"))
    return preprocess_text("\n".join(lines))


def prepare_structured_text(raw_text: str) -> dict[str, Any]:
    prepared_text = preprocess_text(raw_text)
    quality = analyze_text_quality(raw_text)
    return {
        "prepared_text": prepared_text,
        "preprocess_warnings": list(quality.get("warnings", [])),
        "text_quality": quality,
    }


def summarize_candidate_experience(cv: dict[str, Any]) -> str:
    lines: list[str] = []
    for exp in _as_dict_list(cv.get("experiences")):
        _append(lines, exp.get("title"))
        _extend(lines, exp.get("responsibilities"))
        _extend(lines, exp.get("achievements"))
        _extend(lines, exp.get("skills_used") or exp.get("skillsUsed"))
        _extend(lines, exp.get("tools_used") or exp.get("toolsUsed"))
    for project in _as_dict_list(cv.get("projects")):
        _append(lines, project.get("name"))
        _append(lines, project.get("description"))
        _append(lines, project.get("role"))
        _extend(lines, project.get("tools"))
        _extend(lines, project.get("skills_used") or project.get("skillsUsed"))
        _extend(lines, project.get("outcomes"))
    return preprocess_text("\n".join(lines))


def summarize_job_requirement(job: dict[str, Any]) -> str:
    lines: list[str] = []
    _append(lines, job.get("description"))
    _extend(lines, job.get("responsibilities"))
    _extend(lines, job.get("requirements"))
    _extend(lines, job.get("nice_to_have") or job.get("niceToHave"))
    _extend(lines, _skill_display_values(job.get("skills")))
    _extend(lines, _skill_display_values(job.get("must_have_skills") or job.get("mustHaveSkills")))
    _extend(lines, _skill_display_values(job.get("nice_to_have_skills") or job.get("niceToHaveSkills")))
    _extend(lines, job.get("tools_and_technologies") or job.get("toolsAndTechnologies"))
    _extend(lines, job.get("domain_knowledge") or job.get("domainKnowledge"))
    return preprocess_text("\n".join(lines))


def _add_field(lines: list[str], label: str, value: Any) -> None:
    text = _stringify(value)
    if text:
        lines.append(f"{label}: {text}")


def _add_text_block(lines: list[str], label: str, value: Any) -> None:
    text = _stringify(value)
    if text:
        lines.extend(["", f"{label}:", text])


def _add_list_section(lines: list[str], label: str, value: Any) -> None:
    items = [_stringify(item) for item in _as_list(value)]
    items = [item for item in items if item]
    if not items:
        return
    lines.extend(["", f"{label}:"])
    lines.extend(f"- {item}" for item in items)


def _add_skill_section(lines: list[str], label: str, value: Any) -> None:
    items = _skill_display_values(value)
    if not items:
        return
    lines.extend(["", f"{label}:"])
    lines.extend(f"- {item}" for item in items)


def _add_experience_section(lines: list[str], value: Any) -> None:
    experiences = _as_dict_list(value)
    if not experiences:
        return
    lines.extend(["", "Experience:"])
    for exp in experiences:
        title = _stringify(exp.get("title"))
        if title:
            lines.append(f"- {title}")
        _add_nested_list(lines, "Responsibilities", exp.get("responsibilities"))
        _add_nested_list(lines, "Achievements", exp.get("achievements"))
        _add_nested_list(lines, "Skills used", exp.get("skills_used") or exp.get("skillsUsed"))
        _add_nested_list(lines, "Tools used", exp.get("tools_used") or exp.get("toolsUsed"))


def _add_project_section(lines: list[str], value: Any) -> None:
    projects = _as_dict_list(value)
    if not projects:
        return
    lines.extend(["", "Projects:"])
    for project in projects:
        name = _stringify(project.get("name"))
        if name:
            lines.append(f"- {name}")
        _add_field(lines, "  Role", project.get("role"))
        _add_field(lines, "  Description", project.get("description"))
        _add_nested_list(lines, "Tools", project.get("tools"))
        _add_nested_list(lines, "Skills used", project.get("skills_used") or project.get("skillsUsed"))
        _add_nested_list(lines, "Outcomes", project.get("outcomes"))


def _add_nested_list(lines: list[str], label: str, value: Any) -> None:
    items = [_stringify(item) for item in _as_list(value)]
    items = [item for item in items if item]
    if not items:
        return
    lines.append(f"  {label}:")
    lines.extend(f"  - {item}" for item in items)


def _skill_display_values(value: Any) -> list[str]:
    result: list[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            parts = [
                item.get("name"),
                item.get("normalized_name") or item.get("normalizedName"),
                item.get("level"),
                item.get("category"),
            ]
            if item.get("years") is not None:
                parts.append(f"{item.get('years')} years")
            if item.get("weight") is not None:
                parts.append(f"weight {item.get('weight')}")
            text = " ".join(_stringify(part) for part in parts if _stringify(part))
        else:
            text = _stringify(item)
        if text:
            result.append(text)
    return result


def _as_dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in _as_list(value) if isinstance(item, dict)]


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [value]


def _append(lines: list[str], value: Any) -> None:
    text = _stringify(value)
    if text:
        lines.append(text)


def _extend(lines: list[str], values: Any) -> None:
    for value in _as_list(values):
        _append(lines, value)


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()
