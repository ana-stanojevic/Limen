from app.agents.escalation import posting_may_need_human_review, posting_requires_risk_review
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

_BASE_EVALUATION_FOCUS = [
    "required skills alignment",
    "role alignment",
]

_BASE_REQUIRED_SIGNALS = [
    SignalCategory.REQUIRED_SKILLS.value,
    SignalCategory.PREFERRED_SKILLS.value,
    SignalCategory.SENIORITY.value,
    SignalCategory.MISSING_SIGNALS.value,
]


def build_workflow_plan(workflow_input: WorkflowInput) -> WorkflowPlan:
    """Inspect workflow input and derive stages, focus, and required signals."""
    job = workflow_input.job_description
    profile = workflow_input.user_profile
    signals = extract_job_signals(job)

    evaluation_focus = list(_BASE_EVALUATION_FOCUS)
    required_signals = list(_BASE_REQUIRED_SIGNALS)
    stages = list(_BASE_STAGES)

    if signals.production_expectations or profile.production_experience:
        evaluation_focus.append("production expectations")
        required_signals.append(SignalCategory.PRODUCTION_EXPECTATIONS.value)

    if posting_requires_risk_review(signals):
        evaluation_focus.append("posting risk and ambiguity")
        required_signals.append(SignalCategory.RISK_INDICATORS.value)

    if seniority_level_is_unclear(job):
        evaluation_focus.append("seniority clarity")

    if profile.work_preferences:
        evaluation_focus.append("work preference alignment")

    if posting_may_need_human_review(job, signals):
        stages.append(WorkflowState.HUMAN_REVIEW)

    stages.append(WorkflowState.DECISION)

    return WorkflowPlan(
        stages=stages,
        evaluation_focus=dedupe_strings(evaluation_focus),
        required_signals=dedupe_strings(required_signals),
    )
