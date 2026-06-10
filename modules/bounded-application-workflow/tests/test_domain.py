import pytest
from pydantic import ValidationError

from app.domain.models import DecisionType, UserProfile, WorkflowDecision
from app.domain.state_machine import WorkflowStateMachine
from app.domain.workflow_run import WorkflowEventType, WorkflowRun, default_workflow_plan
from app.domain.workflow_state import InvalidTransitionError, WorkflowState
from tests.fixture_helpers import workflow_input


@pytest.mark.parametrize(
    "path",
    [
        [
            WorkflowState.SIGNAL_EXTRACTION,
            WorkflowState.PROFILE_MATCHING,
            WorkflowState.POLICY_EVALUATION,
            WorkflowState.DECISION,
        ],
        [
            WorkflowState.SIGNAL_EXTRACTION,
            WorkflowState.PROFILE_MATCHING,
            WorkflowState.POLICY_EVALUATION,
            WorkflowState.HUMAN_REVIEW,
            WorkflowState.DECISION,
        ],
    ],
    ids=["direct", "via_review"],
)
def test_valid_state_transitions(path: list[WorkflowState]):
    machine = WorkflowStateMachine()

    for target in path:
        machine.transition_to(target)

    assert machine.current_state == WorkflowState.DECISION
    assert machine.history == [WorkflowState.INTAKE, *path]


@pytest.mark.parametrize(
    "current,target",
    [
        (WorkflowState.INTAKE, WorkflowState.DECISION),
        (WorkflowState.DECISION, WorkflowState.INTAKE),
    ],
)
def test_invalid_state_transition(current: WorkflowState, target: WorkflowState):
    machine = WorkflowStateMachine(initial_state=current)

    with pytest.raises(InvalidTransitionError):
        machine.transition_to(target)

    assert machine.current_state == current


def test_workflow_run_records_transition():
    run = WorkflowRun(
        input=workflow_input("strong_match.json"),
        plan=default_workflow_plan(),
    )

    run.transition_to(WorkflowState.SIGNAL_EXTRACTION, "extracting signals")

    assert run.current_state == WorkflowState.SIGNAL_EXTRACTION
    assert run.events[-1].event_type == WorkflowEventType.STATE_ENTERED
    assert run.events[-1].message == "extracting signals"


def test_default_workflow_plan():
    assert default_workflow_plan().stages == [
        WorkflowState.INTAKE,
        WorkflowState.SIGNAL_EXTRACTION,
        WorkflowState.PROFILE_MATCHING,
        WorkflowState.POLICY_EVALUATION,
        WorkflowState.DECISION,
    ]


def test_user_profile_rejects_null_list_fields():
    with pytest.raises(ValidationError):
        UserProfile(name="Ana", skills=None)


def test_workflow_decision_rejects_invalid_score():
    with pytest.raises(ValidationError):
        WorkflowDecision(decision=DecisionType.SKIP, score=1.5)
