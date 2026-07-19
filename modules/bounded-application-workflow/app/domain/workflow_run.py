from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.domain.models import WorkflowDecision

# Graph node ids — also used for the temporary human_review stage until #79.
INTAKE = "intake"
SIGNAL_EXTRACTION = "signal_extraction"
PROFILE_MATCHING = "profile_matching"
POLICY_EVALUATION = "policy_evaluation"
HUMAN_REVIEW = "human_review"
DECISION = "decision"


class WorkflowEventType(str, Enum):
    RUN_STARTED = "run_started"
    PLAN_CREATED = "plan_created"
    STAGE_ENTERED = "stage_entered"
    AGENT_COMPLETED = "agent_completed"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"
    RUN_COMPLETED = "run_completed"


class WorkflowEvent(BaseModel):
    event_type: WorkflowEventType
    stage: str
    timestamp: datetime
    message: str = ""


class AgentTrace(BaseModel):
    """Inspectable record of a single agent invocation within a run."""

    stage: str
    agent: str
    output: dict[str, Any]
    timestamp: datetime


class HumanReviewRecord(BaseModel):
    """Why a run entered human review and how the review was resolved."""

    reason: str
    original_decision: WorkflowDecision
    final_decision: Optional[WorkflowDecision] = None
    approved: Optional[bool] = None
    reviewer_notes: str = ""
    requested_at: datetime
    reviewed_at: Optional[datetime] = None

    @property
    def is_pending(self) -> bool:
        return self.approved is None

    @property
    def is_revised(self) -> bool:
        return (
            self.final_decision is not None
            and self.final_decision != self.original_decision
        )


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
    "AgentTrace",
    "DECISION",
    "HUMAN_REVIEW",
    "INTAKE",
    "POLICY_EVALUATION",
    "PROFILE_MATCHING",
    "PlanExecutionReport",
    "SIGNAL_EXTRACTION",
    "HumanReviewRecord",
    "WorkflowEvent",
    "WorkflowEventType",
    "WorkflowPlan",
    "compare_plan",
    "default_workflow_plan",
]
