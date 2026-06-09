from app.agents.decision_rules import (
    posting_may_need_human_review,
    posting_requires_risk_review,
)
from app.agents.signal_extraction import extract_job_signals, seniority_level_is_unclear
from app.domain.job_signals import SignalCategory
from app.domain.models import WorkflowInput
from app.domain.workflow_run import WorkflowPlan
from app.domain.workflow_state import WorkflowState
from app.text import dedupe_strings

_BASE_STAGES = [
    WorkflowState.INTAKE,
    WorkflowState.SIGNAL_EXTRACTION,
    WorkflowState.PROFILE_MATCHING,
    WorkflowState.POLICY_EVALUATION,
]
_BASE_FOCUS = ["required skills alignment", "role alignment"]
_BASE_SIGNALS = [
    SignalCategory.REQUIRED_SKILLS.value,
    SignalCategory.PREFERRED_SKILLS.value,
    SignalCategory.SENIORITY.value,
    SignalCategory.MISSING_SIGNALS.value,
]


def build_workflow_plan(workflow_input: WorkflowInput) -> WorkflowPlan:
    """Plan the evaluation pipeline from job text and profile before matching."""
    job = workflow_input.job_description
    profile = workflow_input.user_profile
    signals = extract_job_signals(job)
    focus = list(_BASE_FOCUS)
    required = list(_BASE_SIGNALS)
    stages = list(_BASE_STAGES)
    requires_risk_guardrail = posting_requires_risk_review(signals)

    if signals.production_expectations or profile.production_experience:
        focus.append("production expectations")
        required.append(SignalCategory.PRODUCTION_EXPECTATIONS.value)
    if requires_risk_guardrail:
        focus.append("posting risk and ambiguity")
        required.append(SignalCategory.RISK_INDICATORS.value)
    if seniority_level_is_unclear(job):
        focus.append("seniority clarity")
    if profile.work_preferences:
        focus.append("work preference alignment")

    requires_human_review = posting_may_need_human_review(job, signals)
    if requires_human_review:
        stages.append(WorkflowState.HUMAN_REVIEW)
    stages.append(WorkflowState.DECISION)

    return WorkflowPlan(
        stages=stages,
        evaluation_focus=dedupe_strings(focus),
        required_signals=dedupe_strings(required),
        requires_human_review=requires_human_review,
        requires_risk_guardrail=requires_risk_guardrail,
    )
