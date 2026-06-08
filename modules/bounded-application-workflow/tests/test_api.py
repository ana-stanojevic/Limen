import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from tests.fixture_helpers import WORKFLOW_FIXTURES, expected_decision, load_fixture

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_workflow_returns_structured_output():
    fixture = load_fixture("strong_match.json")
    response = client.post(
        "/workflow/run",
        json={
            "user_profile": fixture["user_profile"],
            "job_description": fixture["job_description"],
        },
    )

    assert response.status_code == 200
    assert "decision" in response.json()


@pytest.mark.parametrize("fixture_name", WORKFLOW_FIXTURES)
def test_run_workflow_fixture_decisions(fixture_name: str):
    fixture = load_fixture(fixture_name)
    response = client.post(
        "/workflow/run",
        json={
            "user_profile": fixture["user_profile"],
            "job_description": fixture["job_description"],
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["decision"]["decision"]
        == expected_decision(fixture_name).value
    )


def test_run_workflow_rejects_invalid_payload():
    response = client.post("/workflow/run", json={})
    assert response.status_code == 422
