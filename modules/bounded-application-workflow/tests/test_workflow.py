import pytest

from app.agents import (
    WorkflowOrchestratorInput,
    default_agents,
    evaluate_workflow,
    run_workflow_evaluation,
)
from app.domain.models import DecisionType, JobDescription, UserProfile, WorkflowInput
from app.domain.workflow_run import WorkflowEventType
from app.domain.workflow_state import WorkflowState
from app.parser import parse_job_description
from tests.fixture_helpers import (
    AI_ENGINEER_JOB_TEXT,
    WORKFLOW_FIXTURES,
    expected_decision,
    load_fixture,
    workflow_input,
)


@pytest.mark.parametrize("fixture_name", WORKFLOW_FIXTURES)
def test_fixture_decisions(fixture_name: str):
    output = evaluate_workflow(workflow_input(fixture_name))
    assert output.decision.decision == expected_decision(fixture_name)


def test_parsed_job_description():
    profile = UserProfile(**load_fixture("strong_match.json")["user_profile"])
    job = parse_job_description(AI_ENGINEER_JOB_TEXT)

    output = evaluate_workflow(WorkflowInput(user_profile=profile, job_description=job))

    assert output.decision.decision == DecisionType.PREPARE


def test_severe_seniority_gap_skips():
    output = evaluate_workflow(
        WorkflowInput(
            user_profile=UserProfile(
                name="Ana",
                skills=["Python"],
                seniority="staff",
                experience_summary="Platform leadership.",
                target_roles=["Engineer"],
            ),
            job_description=JobDescription(
                title="Junior Engineer",
                description="Build features.\n\n- Python",
                seniority="junior",
            ),
        )
    )

    assert output.decision.decision == DecisionType.SKIP


def test_risk_posting_escalates_through_human_review():
    fixture = load_fixture("risk_extraction.json")
    profile = workflow_input("ambiguous_match.json").user_profile
    workflow = WorkflowInput(
        user_profile=profile,
        job_description=JobDescription(**fixture["job_description"]),
    )

    output, run = run_workflow_evaluation(workflow)

    assert output.decision.decision == DecisionType.ESCALATE
    assert WorkflowState.HUMAN_REVIEW in run.state_history
    assert run.is_complete is True


def test_prepare_path_state_history():
    _, run = run_workflow_evaluation(workflow_input("strong_match.json"))

    assert run.state_history == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]


def test_escalate_path_state_history():
    fixture = load_fixture("risk_extraction.json")
    profile = workflow_input("ambiguous_match.json").user_profile
    workflow = WorkflowInput(
        user_profile=profile,
        job_description=JobDescription(**fixture["job_description"]),
    )

    _, run = run_workflow_evaluation(workflow)

    assert run.state_history == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.HUMAN_REVIEW,
        WorkflowState.DECISION,
    ]


def test_orchestrator_returns_inspectable_run():
    _, _, _, _, orchestrator = default_agents()
    result = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=workflow_input("strong_match.json"))
    )

    run = result.run
    assert run.is_complete is True
    assert run.output == result.output
    assert run.events[0].event_type == WorkflowEventType.RUN_STARTED
    assert run.events[-1].event_type == WorkflowEventType.RUN_COMPLETED
    assert run.model_dump()["output"]["decision"]["decision"] == result.output.decision.decision.value
