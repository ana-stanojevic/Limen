from typing import Protocol

from pydantic import BaseModel, Field

from app.domain.job_signals import JobSignals
from app.domain.models import (
    EvaluationBrief,
    JobDescription,
    ProfileMatchResult,
    UserProfile,
    WorkflowDecision,
    WorkflowInput,
    WorkflowOutput,
)
from app.domain.workflow_run import WorkflowPlan, WorkflowRun


class SignalExtractorInput(BaseModel):
    job_description: JobDescription
    required_signals: list[str] = Field(default_factory=list)


class SignalExtractorOutput(BaseModel):
    signals: JobSignals


class SignalExtractor(Protocol):
    def run(self, agent_input: SignalExtractorInput) -> SignalExtractorOutput: ...


class ProfileMatcherInput(BaseModel):
    user_profile: UserProfile
    job_description: JobDescription
    signals: JobSignals
    required_signals: list[str] = Field(default_factory=list)


class ProfileMatcherOutput(BaseModel):
    match: ProfileMatchResult


class ProfileMatcher(Protocol):
    def run(self, agent_input: ProfileMatcherInput) -> ProfileMatcherOutput: ...


class DecisionPolicyInput(BaseModel):
    match: ProfileMatchResult
    signals: JobSignals
    plan: WorkflowPlan


class DecisionPolicyOutput(BaseModel):
    decision: WorkflowDecision


class DecisionPolicy(Protocol):
    def run(self, agent_input: DecisionPolicyInput) -> DecisionPolicyOutput: ...


class HumanReviewGateInput(BaseModel):
    evaluation_brief: EvaluationBrief
    decision: WorkflowDecision


class HumanReviewGateOutput(BaseModel):
    decision: WorkflowDecision
    approved: bool
    reviewer_notes: str = Field(default="")


class HumanReviewGate(Protocol):
    def run(self, agent_input: HumanReviewGateInput) -> HumanReviewGateOutput: ...


class WorkflowPlannerInput(BaseModel):
    workflow_input: WorkflowInput


class WorkflowPlannerOutput(BaseModel):
    plan: WorkflowPlan


class WorkflowPlanner(Protocol):
    def run(self, agent_input: WorkflowPlannerInput) -> WorkflowPlannerOutput: ...


class WorkflowOrchestratorInput(BaseModel):
    workflow_input: WorkflowInput


class WorkflowOrchestratorOutput(BaseModel):
    output: WorkflowOutput
    run: WorkflowRun


class WorkflowOrchestrator(Protocol):
    def run(
        self, agent_input: WorkflowOrchestratorInput
    ) -> WorkflowOrchestratorOutput: ...
