import pytest

from app.agents import (
    DecisionPolicyInput,
    DefaultDecisionPolicy,
    DefaultProfileMatcher,
    DefaultSignalExtractor,
    DefaultWorkflowOrchestrator,
    DefaultWorkflowPlanner,
    HumanReviewGateInput,
    PassthroughHumanReviewGate,
    ProfileMatcherInput,
    SignalExtractorInput,
    WorkflowOrchestratorInput,
    WorkflowPlannerInput,
    build_evaluation_brief,
    build_workflow_plan,
    default_agents,
    evaluate_workflow,
    run_workflow_evaluation,
)
from app.domain.job_signals import SignalCategory
from app.domain.models import DecisionType, JobDescription, UserProfile, WorkflowInput
from app.domain.workflow_run import WorkflowEventType
from app.domain.workflow_state import WorkflowState
from app.parser import parse_job_description
from tests.fixture_helpers import (
    AI_ENGINEER_JOB_TEXT,
    WORKFLOW_FIXTURES,
    expected_decision,
    load_fixture,
    workflow_input as load_workflow_input,
)


@pytest.mark.parametrize("fixture_name", WORKFLOW_FIXTURES)
def test_evaluate_workflow_fixture_decisions(fixture_name):
    assert (
        evaluate_workflow(load_workflow_input(fixture_name)).decision.decision
        == expected_decision(fixture_name)
    )


def test_evaluate_workflow_from_parsed_job_description():
    profile = UserProfile(**load_fixture("strong_match.json")["user_profile"])
    output = evaluate_workflow(
        WorkflowInput(user_profile=profile, job_description=parse_job_description(AI_ENGINEER_JOB_TEXT))
    )
    assert output.decision.decision == expected_decision("strong_match.json")


def test_evaluate_workflow_edge_cases(ambiguous_input):
    assert "Job posting missing signal: remote policy" in evaluate_workflow(
        ambiguous_input
    ).decision.missing_information

    staff_vs_junior = evaluate_workflow(
        WorkflowInput(
            user_profile=UserProfile(
                name="Ana", skills=["Python"], seniority="staff", target_roles=["Engineer"]
            ),
            job_description=JobDescription(
                title="Junior Engineer", description="Build features.\n\n- Python", seniority="junior"
            ),
        )
    )
    assert staff_vs_junior.decision.decision == DecisionType.SKIP

    risk_job = JobDescription(**load_fixture("risk_extraction.json")["job_description"])
    assert (
        evaluate_workflow(
            WorkflowInput(user_profile=ambiguous_input.user_profile, job_description=risk_job)
        ).decision.decision
        == DecisionType.ESCALATE
    )


def test_default_agents_and_stage_contracts(pipeline_stages, strong_input, ambiguous_input):
    extractor, matcher, policy, review_gate, planner, orchestrator = default_agents()
    assert all(
        isinstance(x, cls)
        for x, cls in [
            (extractor, DefaultSignalExtractor),
            (matcher, DefaultProfileMatcher),
            (policy, DefaultDecisionPolicy),
            (review_gate, PassthroughHumanReviewGate),
            (planner, DefaultWorkflowPlanner),
            (orchestrator, DefaultWorkflowOrchestrator),
        ]
    )
    assert orchestrator._planner is planner

    match, decision = pipeline_stages["match"], pipeline_stages["decision"]
    assert 0.0 <= match.score <= 1.0 and decision.decision == DecisionType.PREPARE

    plan = build_workflow_plan(ambiguous_input)
    brief = build_evaluation_brief(plan, match, decision, pipeline_stages["signals"])
    gate = PassthroughHumanReviewGate().run(
        HumanReviewGateInput(evaluation_brief=brief, decision=decision)
    )
    assert gate.approved and gate.decision == decision

    planner_result = DefaultWorkflowPlanner().run(
        WorkflowPlannerInput(workflow_input=strong_input)
    )
    assert planner_result.plan.stages and planner_result.plan.evaluation_focus


def test_workflow_planning(strong_input, ambiguous_input):
    clear = build_workflow_plan(strong_input)
    assert clear.stages == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]
    assert clear.requires_human_review is False
    assert clear.requires_risk_guardrail is False

    ambiguous = build_workflow_plan(ambiguous_input)
    assert WorkflowState.HUMAN_REVIEW in ambiguous.stages
    assert ambiguous.requires_human_review is True
    assert "posting risk and ambiguity" in ambiguous.evaluation_focus
    assert SignalCategory.RISK_INDICATORS.value in ambiguous.required_signals
    assert ambiguous.requires_risk_guardrail is True


def test_run_workflow_trace_and_completion(strong_input, ambiguous_input):
    output, run = run_workflow_evaluation(strong_input)
    assert run.state_history == run.plan.stages == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]
    assert run.is_complete and output.evaluation_brief.findings

    _, ambiguous_run = run_workflow_evaluation(ambiguous_input)
    assert WorkflowState.HUMAN_REVIEW in ambiguous_run.plan.stages
    assert WorkflowState.HUMAN_REVIEW not in run.state_history

    risk_job = JobDescription(**load_fixture("risk_extraction.json")["job_description"])
    escalate_output, escalate_run = run_workflow_evaluation(
        WorkflowInput(user_profile=ambiguous_input.user_profile, job_description=risk_job)
    )
    assert escalate_output.decision.decision == DecisionType.ESCALATE
    assert WorkflowState.HUMAN_REVIEW in escalate_run.state_history

    assert run.completed_at and run.workflow_id
    assert run.events[0].event_type == WorkflowEventType.RUN_STARTED
    assert run.events[-1].event_type == WorkflowEventType.RUN_COMPLETED

    result = default_agents()[-1].run(
        WorkflowOrchestratorInput(workflow_input=strong_input)
    )
    assert result.run.is_complete and result.run.current_state == WorkflowState.DECISION
