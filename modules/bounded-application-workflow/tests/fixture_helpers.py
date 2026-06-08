import json
from pathlib import Path

from app.domain.models import DecisionType, JobDescription, UserProfile, WorkflowInput

FIXTURES_DIR = Path(__file__).parent / "fixtures"

WORKFLOW_FIXTURES = (
    "strong_match.json",
    "weak_match.json",
    "ambiguous_match.json",
)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def expected_decision(fixture_name: str) -> DecisionType:
    return DecisionType(load_fixture(fixture_name)["expected_decision"])


def workflow_input(fixture_name: str) -> WorkflowInput:
    data = load_fixture(fixture_name)
    return WorkflowInput(
        user_profile=UserProfile(**data["user_profile"]),
        job_description=JobDescription(**data["job_description"]),
    )
