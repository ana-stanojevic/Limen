from app.agents import (
    DefaultWorkflowPlanner,
    WorkflowPlannerInput,
    build_workflow_plan,
)
from app.domain.job_signals import SignalCategory
from app.domain.workflow_state import WorkflowState
from tests.fixture_helpers import workflow_input as load_workflow_input


def test_build_workflow_plan_standard_stages_for_clear_posting():
    plan = build_workflow_plan(load_workflow_input("strong_match.json"))

    assert plan.stages == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]


def test_build_workflow_plan_includes_human_review_for_ambiguous_posting():
    plan = build_workflow_plan(load_workflow_input("ambiguous_match.json"))

    assert WorkflowState.HUMAN_REVIEW in plan.stages
    assert plan.stages[-1] == WorkflowState.DECISION


def test_build_workflow_plan_records_evaluation_focus():
    plan = build_workflow_plan(load_workflow_input("ambiguous_match.json"))

    assert "required skills alignment" in plan.evaluation_focus
    assert "posting risk and ambiguity" in plan.evaluation_focus
    assert "seniority clarity" in plan.evaluation_focus
    assert "work preference alignment" in plan.evaluation_focus


def test_build_workflow_plan_records_required_signals():
    plan = build_workflow_plan(load_workflow_input("ambiguous_match.json"))

    assert SignalCategory.REQUIRED_SKILLS.value in plan.required_signals
    assert SignalCategory.PREFERRED_SKILLS.value in plan.required_signals
    assert SignalCategory.SENIORITY.value in plan.required_signals
    assert SignalCategory.MISSING_SIGNALS.value in plan.required_signals
    assert SignalCategory.RISK_INDICATORS.value in plan.required_signals


def test_default_workflow_planner_contract():
    planner = DefaultWorkflowPlanner()
    workflow_input = load_workflow_input("strong_match.json")

    result = planner.run(WorkflowPlannerInput(workflow_input=workflow_input))

    assert result.plan.stages
    assert result.plan.evaluation_focus
    assert result.plan.required_signals


def test_planning_runs_independently_from_execution():
    workflow_input = load_workflow_input("ambiguous_match.json")

    plan = build_workflow_plan(workflow_input)

    assert plan.stages
    assert plan.evaluation_focus
    assert plan.required_signals
