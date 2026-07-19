import pytest
from fastapi.testclient import TestClient
from pydantic_ai.exceptions import ModelHTTPError

from app.agents import WorkflowOrchestratorInput
from app.agents.wiring import create_agents
from app.api.main import create_app
from app.domain.models import WorkflowOutput
from tests.conftest import (
    WORKFLOW_FIXTURES,
    RecordingSignalModel,
    load_fixture,
    load_signal_fixture,
    runtime_config,
    workflow_input,
)


def test_health(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_workflow_rejects_invalid_payload(api_client):
    assert api_client.post("/workflow/run", json={}).status_code == 422


@pytest.mark.parametrize("fixture_name", WORKFLOW_FIXTURES)
def test_run_workflow_response_parity(fixture_name):
    """POST /workflow/run returns the same WorkflowOutput as the graph orchestrator.

    Pins runtime config to v1 so local `.env` (e.g. v2/LLM) cannot change the path.
    """
    fixture = load_fixture(fixture_name)
    orchestrator = create_agents(runtime_config=runtime_config(version="v1"))[-1]
    expected = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=workflow_input(fixture_name))
    ).output
    api = TestClient(create_app(orchestrator=orchestrator))

    response = api.post(
        "/workflow/run",
        json={
            "user_profile": fixture["user_profile"],
            "job_description": fixture["job_description"],
        },
    )

    assert response.status_code == 200
    body = WorkflowOutput.model_validate(response.json())
    assert body == expected
    assert body.decision.decision == fixture["expected_decision"]
    assert body.input_summary
    assert body.job_signals is not None
    assert isinstance(body.recommended_next_steps, list)


def test_run_workflow_with_llm_orchestrator():
    llm_config = runtime_config(version="v2")
    skill_fixture = load_signal_fixture("skill_extraction.json")
    strong_fixture = load_fixture("strong_match.json")

    recording_model = RecordingSignalModel(skill_fixture["expected_signals"])
    api = TestClient(
        create_app(
            orchestrator=create_agents(
                model=recording_model.as_model(), runtime_config=llm_config
            )[-1]
        )
    )
    response = api.post(
        "/workflow/run",
        json={
            "user_profile": strong_fixture["user_profile"],
            "job_description": skill_fixture["job_description"],
        },
    )

    assert response.status_code == 200
    assert recording_model.call_count == 1
    assert (
        response.json()["job_signals"]["required_skills"]
        == skill_fixture["expected_signals"]["required_skills"]
    )

    failing_model = RecordingSignalModel(
        ModelHTTPError(status_code=503, model_name="test", body="offline")
    )
    api = TestClient(
        create_app(
            orchestrator=create_agents(
                model=failing_model.as_model(), runtime_config=llm_config
            )[-1]
        )
    )
    response = api.post(
        "/workflow/run",
        json={
            "user_profile": strong_fixture["user_profile"],
            "job_description": strong_fixture["job_description"],
        },
    )

    assert response.status_code == 200
    assert response.json()["decision"]["decision"] == strong_fixture["expected_decision"]
