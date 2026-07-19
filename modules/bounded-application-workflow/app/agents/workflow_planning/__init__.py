from app.agents.workflow_planning.plan import (
    DECISION,
    HUMAN_REVIEW,
    INTAKE,
    POLICY_EVALUATION,
    PROFILE_MATCHING,
    SIGNAL_EXTRACTION,
    PlanExecutionReport,
    WorkflowPlan,
    compare_plan,
    default_workflow_plan,
)

__all__ = [
    "DECISION",
    "DefaultWorkflowPlanner",
    "HUMAN_REVIEW",
    "INTAKE",
    "POLICY_EVALUATION",
    "PROFILE_MATCHING",
    "PlanExecutionReport",
    "SIGNAL_EXTRACTION",
    "WorkflowPlan",
    "compare_plan",
    "create_workflow_plan",
    "default_workflow_plan",
]


def __getattr__(name: str):
    if name in {"DefaultWorkflowPlanner", "create_workflow_plan"}:
        from app.agents.workflow_planning import planner

        return getattr(planner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
