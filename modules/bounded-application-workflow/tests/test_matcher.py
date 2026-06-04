import json
from pathlib import Path

import pytest

from app.domain.models import JobDescription, UserProfile, WorkflowInput
from app.services.matcher import match_profile_to_job

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def _workflow_input(fixture_name: str) -> WorkflowInput:
    data = _load_fixture(fixture_name)
    return WorkflowInput(
        user_profile=UserProfile(**data["user_profile"]),
        job_description=JobDescription(**data["job_description"]),
    )


@pytest.mark.parametrize(
    "fixture_name,min_score,max_score,role_aligned",
    [
        ("strong_match.json", 0.5, 1.0, True),
        ("weak_match.json", 0.0, 0.35, False),
        ("ambiguous_match.json", 0.35, 0.75, True),
    ],
)
def test_match_profile_to_job_fixture_ranges(
    fixture_name: str, min_score: float, max_score: float, role_aligned: bool
):
    workflow_input = _workflow_input(fixture_name)
    result = match_profile_to_job(
        workflow_input.user_profile, workflow_input.job_description
    )

    assert min_score <= result.score <= max_score
    assert result.role_aligned is role_aligned


def test_strong_match_covers_core_required_skills():
    workflow_input = _workflow_input("strong_match.json")
    result = match_profile_to_job(
        workflow_input.user_profile, workflow_input.job_description
    )

    assert "Python" in result.required_skills_matched
    assert "LLM applications" in result.required_skills_matched
    assert len(result.required_skills_missing) <= 3


def test_weak_match_misses_frontend_stack():
    workflow_input = _workflow_input("weak_match.json")
    result = match_profile_to_job(
        workflow_input.user_profile, workflow_input.job_description
    )

    assert result.required_skills_matched == []
    assert len(result.required_skills_missing) == len(
        workflow_input.job_description.required_skills
    )
    assert "React" in result.required_skills_missing


def test_ambiguous_match_is_partial_not_empty():
    workflow_input = _workflow_input("ambiguous_match.json")
    result = match_profile_to_job(
        workflow_input.user_profile, workflow_input.job_description
    )

    assert result.required_skills_matched
    assert result.required_skills_missing
    assert result.reasons
    assert result.risks
