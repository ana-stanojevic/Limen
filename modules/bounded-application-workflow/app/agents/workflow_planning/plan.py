from pydantic import BaseModel, Field

# Graph node ids — also used for the temporary human_review stage until #79.
INTAKE = "intake"
SIGNAL_EXTRACTION = "signal_extraction"
PROFILE_MATCHING = "profile_matching"
POLICY_EVALUATION = "policy_evaluation"
HUMAN_REVIEW = "human_review"
DECISION = "decision"


class WorkflowPlan(BaseModel):
    """Intended stages before execution (graph node ids)."""

    stages: list[str] = Field(default_factory=list)


class PlanExecutionReport(BaseModel):
    """Comparison of planned stages against the executed stage history."""

    planned_stages: list[str]
    executed_stages: list[str]
    unplanned_stages: list[str]
    skipped_stages: list[str]
    followed_plan: bool


def default_workflow_plan() -> WorkflowPlan:
    return WorkflowPlan(
        stages=[
            INTAKE,
            SIGNAL_EXTRACTION,
            PROFILE_MATCHING,
            POLICY_EVALUATION,
            DECISION,
        ],
    )


def compare_plan(
    plan: WorkflowPlan, stage_history: list[str]
) -> PlanExecutionReport:
    planned = list(plan.stages)
    executed = list(stage_history)
    return PlanExecutionReport(
        planned_stages=planned,
        executed_stages=executed,
        unplanned_stages=[stage for stage in executed if stage not in planned],
        skipped_stages=[stage for stage in planned if stage not in executed],
        followed_plan=planned == executed,
    )


__all__ = [
    "DECISION",
    "HUMAN_REVIEW",
    "INTAKE",
    "POLICY_EVALUATION",
    "PROFILE_MATCHING",
    "PlanExecutionReport",
    "SIGNAL_EXTRACTION",
    "WorkflowPlan",
    "compare_plan",
    "default_workflow_plan",
]
