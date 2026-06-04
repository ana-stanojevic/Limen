import re
from typing import Iterable

from app.domain.models import JobDescription, ProfileMatchResult, UserProfile

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset({"and", "the", "for", "with", "or"})
_GENERIC_TOKENS = frozenset(
    {
        "engineer",
        "engineering",
        "developer",
        "development",
        "systems",
        "system",
        "senior",
        "junior",
        "lead",
        "staff",
        "manager",
        "experience",
        "product",
        "role",
        "roles",
    }
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in _TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _profile_corpus(profile: UserProfile) -> str:
    parts = [
        *profile.skills,
        *profile.target_roles,
        *profile.work_preferences,
        profile.experience_summary or "",
    ]
    return " ".join(parts).lower()


def _profile_sources(profile: UserProfile) -> list[str]:
    return [
        *profile.skills,
        *profile.target_roles,
        *profile.work_preferences,
        profile.experience_summary or "",
    ]


def _specific_tokens(tokens: set[str]) -> set[str]:
    return tokens - _GENERIC_TOKENS


def _skill_matches_in_text(text: str, skill: str) -> bool:
    normalized_text = text.lower().strip()
    normalized_skill = skill.lower().strip()
    if not normalized_skill:
        return False

    if normalized_skill in normalized_text:
        return True

    skill_tokens = _tokens(normalized_skill)
    if not skill_tokens:
        return False

    text_tokens = _tokens(normalized_text)
    overlap = skill_tokens & text_tokens
    if not overlap:
        return False

    if len(skill_tokens) == 1:
        return True

    specific_skill = _specific_tokens(skill_tokens)
    specific_overlap = _specific_tokens(overlap)
    if specific_skill:
        return len(specific_overlap) / len(specific_skill) >= 0.5

    return len(overlap) == len(skill_tokens)


def _skill_matches(profile: UserProfile, skill: str) -> bool:
    for source in _profile_sources(profile):
        if source and _skill_matches_in_text(source, skill):
            return True
    #return _skill_matches_in_text(_profile_corpus(profile), skill)


def _partition_skills(
    profile: UserProfile, skills: Iterable[str]
) -> tuple[list[str], list[str]]:
    matched: list[str] = []
    missing: list[str] = []

    for skill in skills:
        if _skill_matches(profile, skill):
            matched.append(skill)
        else:
            missing.append(skill)

    return matched, missing


def _role_aligned(profile: UserProfile, job: JobDescription) -> bool:
    job_text = f"{job.title} {job.description}".lower()
    job_title_tokens = _specific_tokens(_tokens(job.title))

    for role in profile.target_roles:
        role_lower = role.lower().strip()
        if not role_lower:
            continue

        if role_lower in job_text:
            return True

        role_tokens = _specific_tokens(_tokens(role_lower))
        if role_tokens and role_tokens & job_title_tokens:
            return True

    profile_tokens = _specific_tokens(_tokens(_profile_corpus(profile)))
    shared_title_tokens = profile_tokens & job_title_tokens
    return len(shared_title_tokens) >= 2


def _coverage_ratio(matched_count: int, total_count: int) -> float:
    if total_count == 0:
        return 1.0
    return matched_count / total_count


def match_profile_to_job(
    user_profile: UserProfile, job_description: JobDescription
) -> ProfileMatchResult:
    required_matched, required_missing = _partition_skills(
        user_profile, job_description.required_skills
    )
    nice_matched, _ = _partition_skills(
        user_profile, job_description.nice_to_have_skills
    )

    required_ratio = _coverage_ratio(
        len(required_matched), len(job_description.required_skills)
    )
    nice_ratio = _coverage_ratio(
        len(nice_matched), len(job_description.nice_to_have_skills)
    )
    role_aligned = _role_aligned(user_profile, job_description)

    role_component = 0.15 if role_aligned else 0.0
    score = min(1.0, 0.75 * required_ratio + 0.10 * nice_ratio + role_component)

    reasons: list[str] = []
    risks: list[str] = []

    if required_matched:
        reasons.append(
            f"Matched {len(required_matched)} of {len(job_description.required_skills)} required skills."
        )
    if nice_matched:
        reasons.append(
            f"Matched {len(nice_matched)} nice-to-have skills."
        )
    if role_aligned:
        reasons.append("Job aligns with target role.")
    else:
        risks.append("Job title or description does not clearly align with target roles.")

    if required_missing:
        risks.append(
            f"Missing required skills: {', '.join(required_missing)}."
        )

    return ProfileMatchResult(
        score=round(score, 2),
        required_skills_matched=required_matched,
        required_skills_missing=required_missing,
        nice_to_have_skills_matched=nice_matched,
        role_aligned=role_aligned,
        reasons=reasons,
        risks=risks,
    )
