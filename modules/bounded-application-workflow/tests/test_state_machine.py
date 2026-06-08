import pytest

from app.domain.state_machine import WorkflowStateMachine
from app.domain.workflow_state import (
    VALID_TRANSITIONS,
    InvalidTransitionError,
    WorkflowState,
)


def test_workflow_state_contract():
    assert {state.value for state in WorkflowState} == {
        "intake",
        "signal_extraction",
        "profile_matching",
        "policy_evaluation",
        "human_review",
        "decision",
    }
    assert WorkflowState.SIGNAL_EXTRACTION in VALID_TRANSITIONS[WorkflowState.INTAKE]
    assert WorkflowState.DECISION in VALID_TRANSITIONS[WorkflowState.HUMAN_REVIEW]
    assert VALID_TRANSITIONS[WorkflowState.DECISION] == frozenset()


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
)
def test_valid_transition_paths(path: list[WorkflowState]):
    machine = WorkflowStateMachine()

    for target in path:
        machine.transition_to(target)

    assert machine.current_state == WorkflowState.DECISION
    assert machine.history == [WorkflowState.INTAKE, *path]


@pytest.mark.parametrize(
    "current,target,error_match",
    [
        (WorkflowState.INTAKE, WorkflowState.DECISION, None),
        (WorkflowState.INTAKE, WorkflowState.HUMAN_REVIEW, None),
        (WorkflowState.SIGNAL_EXTRACTION, WorkflowState.DECISION, None),
        (WorkflowState.PROFILE_MATCHING, WorkflowState.INTAKE, None),
        (WorkflowState.POLICY_EVALUATION, WorkflowState.INTAKE, None),
        (WorkflowState.HUMAN_REVIEW, WorkflowState.POLICY_EVALUATION, None),
        (WorkflowState.DECISION, WorkflowState.INTAKE, "terminal state"),
    ],
)
def test_invalid_transitions_fail_with_clear_error(
    current: WorkflowState,
    target: WorkflowState,
    error_match: str | None,
):
    machine = WorkflowStateMachine(initial_state=current)

    with pytest.raises(InvalidTransitionError, match=error_match) as exc_info:
        machine.transition_to(target)

    error = exc_info.value
    assert error.current == current
    assert error.target == target
    assert machine.current_state == current
    assert machine.history == [current]
