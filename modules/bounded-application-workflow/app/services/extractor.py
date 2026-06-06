import re
from typing import Iterable

from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription

PatternLabel = tuple[re.Pattern[str], str | None]

_YEARS_EXPERIENCE_PATTERN = re.compile(
    r"\b(\d+\s*-\s*\d+|\d+\+?)\s*(?:years?|yrs?)"
    r"(?:\s+of\s+(?:[\w-]+\s+)*experience)?\b",
    re.IGNORECASE,
)
_SENIORITY_LEVEL_PATTERN = re.compile(
    r"\b("
    r"junior|mid[- ]level|mid[- ]senior|senior|staff|principal|"
    r"(?:team\s+)?lead|director"
    r")\b",
    re.IGNORECASE,
)
_OWNERSHIP_PATTERNS: list[PatternLabel] = [
    (re.compile(r"\bproduct ownership\b", re.IGNORECASE), "product ownership"),
    (
        re.compile(r"\bend[- ]to[- ]end ownership\b", re.IGNORECASE),
        "end-to-end ownership",
    ),
    (re.compile(r"\btechnical ownership\b", re.IGNORECASE), "technical ownership"),
    (
        re.compile(
            r"\b(?:own|drive|lead)\s+(?:and\s+)?(?:[\w-]+\s+){0,4}"
            r"(?:product|workflows?|systems?|initiatives?|roadmap|delivery)\b",
            re.IGNORECASE,
        ),
        None,
    ),
]
_PRODUCTION_PATTERNS: list[PatternLabel] = [
    (re.compile(r"\bon[- ]call(?:\s+rotation)?\b", re.IGNORECASE), "on-call rotation"),
    (
        re.compile(r"\blarge[- ]scale(?:\s+[\w-]+)?\b", re.IGNORECASE),
        None,
    ),
    (re.compile(r"\bproduction[- ]ready\b", re.IGNORECASE), "production readiness"),
    (
        re.compile(
            r"\b(?:deploy(?:ment)?|operating|running)\s+in\s+production\b",
            re.IGNORECASE,
        ),
        "production deployment",
    ),
    (
        re.compile(
            r"\b(?:monitoring|observability|reliability|incident response|sla)\b",
            re.IGNORECASE,
        ),
        None,
    ),
]


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


def _job_corpus(job: JobDescription) -> str:
    return "\n".join(part for part in [job.title, job.description] if part)


def _signals_from_labeled_patterns(
    corpus: str, patterns: list[PatternLabel]
) -> list[str]:
    signals: list[str] = []

    for pattern, label in patterns:
        for match in pattern.finditer(corpus):
            signals.append(label or _normalize_skill(match.group(0)))

    return signals


def _seniority_signals_from_job(job: JobDescription) -> list[str]:
    signals: list[str] = []

    if job.seniority:
        signals.append(job.seniority)

    corpus = _job_corpus(job)
    for match in _YEARS_EXPERIENCE_PATTERN.finditer(corpus):
        signals.append(_normalize_skill(match.group(0)))

    for match in _SENIORITY_LEVEL_PATTERN.finditer(corpus):
        signals.append(_normalize_skill(match.group(0)))

    for skill in [*job.required_skills, *job.nice_to_have_skills]:
        if "ownership" in skill.casefold():
            signals.append(skill)

    signals.extend(_signals_from_labeled_patterns(corpus, _OWNERSHIP_PATTERNS))

    return _dedupe_skills(signals)


def _production_expectations_from_job(job: JobDescription) -> list[str]:
    return _dedupe_skills(
        _signals_from_labeled_patterns(_job_corpus(job), _PRODUCTION_PATTERNS)
    )


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
        seniority_signals=_seniority_signals_from_job(job),
        production_expectations=_production_expectations_from_job(job),
    )
