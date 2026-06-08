from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models import WorkflowInput, WorkflowOutput
from app.domain.workflow_state import (
    VALID_TRANSITIONS,
    InvalidTransitionError,
    WorkflowState,
)


class WorkflowEventType(str, Enum):
    RUN_STARTED = "run_started"
    STATE_ENTERED = "state_entered"
    RUN_COMPLETED = "run_completed"


class WorkflowEvent(BaseModel):
    event_type: WorkflowEventType
    state: WorkflowState
    timestamp: datetime
    message: str = ""


class WorkflowPlan(BaseModel):
    """Describes intended workflow stages before execution."""

    stages: list[WorkflowState] = Field(default_factory=list)
    evaluation_focus: list[str] = Field(default_factory=list)
    required_signals: list[str] = Field(default_factory=list)


def default_workflow_plan() -> WorkflowPlan:
    return WorkflowPlan(
        stages=[
            WorkflowState.INTAKE,
            WorkflowState.SIGNAL_EXTRACTION,
            WorkflowState.PROFILE_MATCHING,
            WorkflowState.POLICY_EVALUATION,
            WorkflowState.DECISION,
        ],
    )


class WorkflowRun(BaseModel):
    """Runtime record of a single workflow execution."""

    model_config = ConfigDict(validate_assignment=True)

    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    input: WorkflowInput
    current_state: WorkflowState = WorkflowState.INTAKE
    plan: WorkflowPlan
    output: Optional[WorkflowOutput] = None
    events: list[WorkflowEvent] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    @property
    def is_complete(self) -> bool:
        return (
            self.current_state == WorkflowState.DECISION
            and self.output is not None
            and self.completed_at is not None
        )

    @property
    def state_history(self) -> list[WorkflowState]:
        history = [WorkflowState.INTAKE]
        for event in self.events:
            if event.event_type == WorkflowEventType.STATE_ENTERED:
                history.append(event.state)
        return history

    def record_event(
        self,
        event_type: WorkflowEventType,
        state: WorkflowState,
        message: str = "",
        *,
        timestamp: Optional[datetime] = None,
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            event_type=event_type,
            state=state,
            timestamp=timestamp or datetime.now(timezone.utc),
            message=message,
        )
        self.events.append(event)
        return event

    def transition_to(self, target: WorkflowState, message: str = "") -> WorkflowState:
        if target not in VALID_TRANSITIONS[self.current_state]:
            raise InvalidTransitionError(self.current_state, target)
        self.current_state = target
        self.record_event(WorkflowEventType.STATE_ENTERED, target, message)
        return target

    def complete(self, output: WorkflowOutput) -> None:
        if self.current_state != WorkflowState.DECISION:
            self.transition_to(WorkflowState.DECISION)
        self.output = output
        self.completed_at = datetime.now(timezone.utc)
        self.record_event(
            WorkflowEventType.RUN_COMPLETED,
            WorkflowState.DECISION,
            "Workflow run completed.",
        )
