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
)
from app.domain.models import DecisionType
from app.domain.workflow_state import WorkflowState
from tests.fixture_helpers import expected_decision, workflow_input as load_workflow_input


def test_default_agents_return_all_contracts():
    extractor, matcher, policy, review_gate, planner, orchestrator = default_agents()

    assert isinstance(extractor, DefaultSignalExtractor)
    assert isinstance(matcher, DefaultProfileMatcher)
    assert isinstance(policy, DefaultDecisionPolicy)
    assert isinstance(review_gate, PassthroughHumanReviewGate)
    assert isinstance(planner, DefaultWorkflowPlanner)
    assert isinstance(orchestrator, DefaultWorkflowOrchestrator)
    assert orchestrator._planner is planner


def test_signal_extractor_contract():
    workflow_input = load_workflow_input("strong_match.json")
    extractor = DefaultSignalExtractor()

    result = extractor.run(
        SignalExtractorInput(job_description=workflow_input.job_description)
    )

    assert result.signals.required_skills
    assert isinstance(result.signals.required_skills, list)


def test_profile_matcher_contract():
    workflow_input = load_workflow_input("strong_match.json")
    extractor = DefaultSignalExtractor()
    matcher = DefaultProfileMatcher()

    signals = extractor.run(
        SignalExtractorInput(job_description=workflow_input.job_description)
    ).signals
    result = matcher.run(
        ProfileMatcherInput(
            user_profile=workflow_input.user_profile,
            job_description=workflow_input.job_description,
            signals=signals,
        )
    )

    assert 0.0 <= result.match.score <= 1.0
    assert isinstance(result.match.reasons, list)


def test_decision_policy_contract():
    workflow_input = load_workflow_input("strong_match.json")
    extractor = DefaultSignalExtractor()
    matcher = DefaultProfileMatcher()
    policy = DefaultDecisionPolicy()

    signals = extractor.run(
        SignalExtractorInput(job_description=workflow_input.job_description)
    ).signals
    match = matcher.run(
        ProfileMatcherInput(
            user_profile=workflow_input.user_profile,
            job_description=workflow_input.job_description,
            signals=signals,
        )
    ).match
    result = policy.run(DecisionPolicyInput(match=match, signals=signals))

    assert result.decision.decision == DecisionType.PREPARE
    assert result.decision.score == match.score


def test_workflow_planner_contract():
    workflow_input = load_workflow_input("strong_match.json")
    planner = DefaultWorkflowPlanner()

    result = planner.run(WorkflowPlannerInput(workflow_input=workflow_input))

    assert result.plan.stages
    assert result.plan.evaluation_focus
    assert result.plan.required_signals


def test_human_review_gate_contract_passthrough():
    workflow_input = load_workflow_input("ambiguous_match.json")
    extractor = DefaultSignalExtractor()
    matcher = DefaultProfileMatcher()
    policy = DefaultDecisionPolicy()
    review_gate = PassthroughHumanReviewGate()

    signals = extractor.run(
        SignalExtractorInput(job_description=workflow_input.job_description)
    ).signals
    match = matcher.run(
        ProfileMatcherInput(
            user_profile=workflow_input.user_profile,
            job_description=workflow_input.job_description,
            signals=signals,
        )
    ).match
    decision = policy.run(
        DecisionPolicyInput(match=match, signals=signals)
    ).decision
    plan = build_workflow_plan(workflow_input)
    evaluation_brief = build_evaluation_brief(plan, match, decision, signals)
    result = review_gate.run(
        HumanReviewGateInput(
            evaluation_brief=evaluation_brief,
            decision=decision,
        )
    )

    assert result.approved is True
    assert result.decision == decision


def test_workflow_orchestrator_contract():
    workflow_input = load_workflow_input("strong_match.json")
    *_, orchestrator = default_agents()

    result = orchestrator.run(WorkflowOrchestratorInput(workflow_input=workflow_input))

    assert result.output.decision.decision == expected_decision("strong_match.json")
    assert result.run.is_complete is True
    assert result.run.current_state == WorkflowState.DECISION
    assert result.run.state_history[-1] == WorkflowState.DECISION
