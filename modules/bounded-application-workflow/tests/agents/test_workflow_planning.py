from app.agents.workflow_planning.plan import (
    DECISION,
    HUMAN_REVIEW,
    INTAKE,
    POLICY_EVALUATION,
    PROFILE_MATCHING,
    SIGNAL_EXTRACTION,
    WorkflowPlan,
    compare_plan,
    default_workflow_plan,
)


def test_default_workflow_plan():
    assert default_workflow_plan().stages == [
        INTAKE,
        SIGNAL_EXTRACTION,
        PROFILE_MATCHING,
        POLICY_EVALUATION,
        DECISION,
    ]


def test_compare_plan_flags_skipped_human_review():
    plan = WorkflowPlan(
        stages=[
            INTAKE,
            SIGNAL_EXTRACTION,
            PROFILE_MATCHING,
            POLICY_EVALUATION,
            HUMAN_REVIEW,
            DECISION,
        ],
    )
    executed = [
        INTAKE,
        SIGNAL_EXTRACTION,
        PROFILE_MATCHING,
        POLICY_EVALUATION,
        DECISION,
    ]

    report = compare_plan(plan, executed)

    assert report.followed_plan is False
    assert report.skipped_stages == [HUMAN_REVIEW]
    assert report.unplanned_stages == []


def test_compare_plan_followed():
    plan = default_workflow_plan()
    report = compare_plan(plan, list(plan.stages))
    assert report.followed_plan is True
    assert report.unplanned_stages == []
    assert report.skipped_stages == []
