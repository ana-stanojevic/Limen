import pytest

from app.agents import (
    DecisionPolicyInput,
    DefaultDecisionPolicy,
    DefaultProfileMatcher,
    DefaultSignalExtractor,
    ProfileMatcherInput,
    SignalExtractorInput,
    build_workflow_plan,
)
from app.domain.models import WorkflowInput
from tests.fixture_helpers import workflow_input as load_workflow_input


@pytest.fixture
def strong_input() -> WorkflowInput:
    return load_workflow_input("strong_match.json")


@pytest.fixture
def ambiguous_input() -> WorkflowInput:
    return load_workflow_input("ambiguous_match.json")


@pytest.fixture
def pipeline_stages(strong_input):
    plan = build_workflow_plan(strong_input)
    signals = DefaultSignalExtractor().run(
        SignalExtractorInput(
            job_description=strong_input.job_description,
            required_signals=plan.required_signals,
        )
    ).signals
    match = DefaultProfileMatcher().run(
        ProfileMatcherInput(
            user_profile=strong_input.user_profile,
            job_description=strong_input.job_description,
            signals=signals,
            required_signals=plan.required_signals,
        )
    ).match
    decision = DefaultDecisionPolicy().run(
        DecisionPolicyInput(match=match, signals=signals, plan=plan)
    ).decision
    return {"plan": plan, "signals": signals, "match": match, "decision": decision}
