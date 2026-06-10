import pytest

from app.agents import (
    DefaultWorkflowOrchestrator,
    RecordedHumanReviewGate,
    WorkflowOrchestratorInput,
    default_agents,
    evaluate_workflow,
    run_workflow_evaluation,
)
from app.domain.models import (
    DecisionType,
    JobDescription,
    UserProfile,
    WorkflowDecision,
    WorkflowInput,
)
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


def _escalating_workflow() -> WorkflowInput:
    fixture = load_fixture("risk_extraction.json")
    return WorkflowInput(
        user_profile=workflow_input("ambiguous_match.json").user_profile,
        job_description=JobDescription(**fixture["job_description"]),
    )


def test_risk_posting_escalates_through_human_review():
    output, run = run_workflow_evaluation(_escalating_workflow())

    assert output.decision.decision == DecisionType.ESCALATE
    assert run.is_complete is True
    assert run.state_history == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.HUMAN_REVIEW,
        WorkflowState.DECISION,
    ]
    # The planner pre-scans the risky posting, so review was anticipated.
    assert WorkflowState.HUMAN_REVIEW in run.plan.stages
    assert run.plan_report is not None
    assert run.plan_report.followed_plan is True
    # The passthrough gate approves the escalated decision and stores why.
    assert run.review is not None
    assert run.review.reason.startswith("Escalated for human review")
    assert run.review.approved is True


def test_prepare_path_state_history():
    _, run = run_workflow_evaluation(workflow_input("strong_match.json"))

    assert run.state_history == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]
    assert run.plan.stages == run.state_history
    assert run.plan_report is not None
    assert run.plan_report.followed_plan is True


def test_unplanned_human_review_is_reported():
    # Score lands in the escalate band without any risk indicators, so the
    # planner does not anticipate review but execution still enters it.
    workflow = WorkflowInput(
        user_profile=UserProfile(
            name="Ana",
            target_roles=["Backend Engineer"],
            skills=["Go"],
            seniority="mid-senior",
        ),
        job_description=JobDescription(
            title="Backend Engineer",
            description="Backend role.\n\n- Python\n- Kubernetes\n- Terraform",
            seniority="mid-senior",
        ),
    )

    output, run = run_workflow_evaluation(workflow)

    assert output.decision.decision == DecisionType.ESCALATE
    assert WorkflowState.HUMAN_REVIEW not in run.plan.stages
    report = run.plan_report
    assert report is not None
    assert report.followed_plan is False
    assert report.unplanned_stages == [WorkflowState.HUMAN_REVIEW]
    assert report.skipped_stages == []


def test_recorded_review_revises_escalated_decision():
    revised = WorkflowDecision(decision=DecisionType.QUEUE, score=0.5)
    orchestrator = DefaultWorkflowOrchestrator(
        review_gate=RecordedHumanReviewGate(
            revised_decision=revised,
            reviewer_notes="Scope clarified with recruiter.",
        )
    )

    result = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=_escalating_workflow())
    )

    assert result.output.decision == revised
    assert result.run.review is not None
    assert result.run.review.is_revised is True
    assert result.run.review.reviewer_notes == "Scope clarified with recruiter."


def test_recorded_review_approves_escalated_decision():
    orchestrator = DefaultWorkflowOrchestrator(
        review_gate=RecordedHumanReviewGate()
    )

    result = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=_escalating_workflow())
    )

    assert result.output.decision.decision == DecisionType.ESCALATE
    assert result.run.review is not None
    assert result.run.review.approved is True
    assert result.run.review.is_revised is False


def test_orchestrator_returns_inspectable_run():
    *_, orchestrator = default_agents()
    result = orchestrator.run(
        WorkflowOrchestratorInput(workflow_input=workflow_input("strong_match.json"))
    )

    run = result.run
    assert run.is_complete is True
    assert run.output == result.output
    assert run.events[0].event_type == WorkflowEventType.RUN_STARTED
    assert run.events[-1].event_type == WorkflowEventType.RUN_COMPLETED
    assert run.model_dump()["output"]["decision"]["decision"] == result.output.decision.decision.value


def test_run_logs_planner_decision_and_agent_outputs():
    _, run = run_workflow_evaluation(workflow_input("strong_match.json"))

    assert run.events[1].event_type == WorkflowEventType.PLAN_CREATED
    assert "intake -> signal_extraction" in run.events[1].message

    assert [(trace.stage, trace.agent) for trace in run.traces] == [
        (WorkflowState.SIGNAL_EXTRACTION, "DefaultSignalExtractor"),
        (WorkflowState.PROFILE_MATCHING, "DefaultProfileMatcher"),
        (WorkflowState.POLICY_EVALUATION, "DefaultDecisionPolicy"),
    ]
    matcher_trace, policy_trace = run.traces[1], run.traces[2]
    assert policy_trace.output["decision"]["decision"] == DecisionType.PREPARE
    # The policy decision's score is traceable back to the matcher's output.
    assert policy_trace.output["decision"]["score"] == matcher_trace.output["match"]["score"]


def test_escalated_run_decision_is_traceable():
    output, run = run_workflow_evaluation(_escalating_workflow())

    # execution_trace() chains every agent invocation plus the final decision.
    chain = run.execution_trace()
    assert [trace.stage for trace in chain] == [
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.HUMAN_REVIEW,
        WorkflowState.DECISION,
    ]
    assert chain[3].agent == "PassthroughHumanReviewGate"
    assert chain[-1].agent == "workflow"
    assert chain[-1].output["decision"] == output.decision.decision
    assert chain[-1].timestamp == run.completed_at

    event_types = [event.event_type for event in run.events]
    assert event_types.index(WorkflowEventType.REVIEW_REQUESTED) < event_types.index(
        WorkflowEventType.REVIEW_COMPLETED
    )


def test_workflow_history_serializable_after_execution():
    _, run = run_workflow_evaluation(_escalating_workflow())

    dumped = run.model_dump(mode="json")

    assert dumped["events"][0]["event_type"] == "run_started"
    assert dumped["events"][-1]["event_type"] == "run_completed"
    assert [trace["stage"] for trace in dumped["traces"]] == [
        "signal_extraction",
        "profile_matching",
        "policy_evaluation",
        "human_review",
    ]
    # Traces store only agent outputs; the raw posting lives once on run.input.
    description = run.input.job_description.description
    assert all(description not in str(trace["output"]) for trace in dumped["traces"])
