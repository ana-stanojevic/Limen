from typing import Iterable

from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription


def _normalize_skill(skill: str) -> str:
    return " ".join(skill.split())


def _dedupe_skills(skills: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for skill in skills:
        normalized = _normalize_skill(skill)
        if not normalized:
            continue

        key = normalized.casefold()
        if key in seen:
            continue

        seen.add(key)
        result.append(normalized)

    return result


def _skills_from_description(description: str) -> tuple[list[str], list[str]]:
    required: list[str] = []
    preferred: list[str] = []

    for line in description.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            required.append(stripped.lstrip("- ").strip())
        elif stripped.startswith("+"):
            preferred.append(stripped.lstrip("+ ").strip())

    return required, preferred


def extract_job_signals(job: JobDescription) -> JobSignals:
    description_required, description_preferred = _skills_from_description(
        job.description
    )

    required_skills = _dedupe_skills(
        [*job.required_skills, *description_required]
    )
    required_keys = {skill.casefold() for skill in required_skills}

    preferred_skills = [
        skill
        for skill in _dedupe_skills(
            [*job.nice_to_have_skills, *description_preferred]
        )
        if skill.casefold() not in required_keys
    ]

    return JobSignals(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
    )
