from app.agents.signal_extraction import (
    has_explicit_missing_signal_phrases,
    seniority_level_is_unclear,
)
from app.domain.job_signals import JobSignals, SignalCategory
from app.domain.models import (
    DecisionType,
    JobDescription,
    ProfileMatchResult,
    WorkflowDecision,
)
from app.domain.workflow_run import WorkflowPlan

# MVP thresholds — docs/PRD.md
_PREPARE_MIN = 0.75
_QUEUE_MIN = 0.55
_ESCALATE_MIN = 0.35


def posting_requires_risk_review(signals: JobSignals) -> bool:
    """Risky postings need human review even when the profile match is strong."""
    return bool(signals.risk_indicators)


def posting_may_need_human_review(job: JobDescription, signals: JobSignals) -> bool:
    """Whether the workflow plan should reserve a human review stage."""
    return (
        posting_requires_risk_review(signals)
        or has_explicit_missing_signal_phrases(job)
        or seniority_level_is_unclear(job)
    )


def decision_from_score(score: float) -> DecisionType:
    if score >= _PREPARE_MIN:
        return DecisionType.PREPARE
    if score >= _QUEUE_MIN:
        return DecisionType.QUEUE
    if score >= _ESCALATE_MIN:
        return DecisionType.ESCALATE
    return DecisionType.SKIP


def decision_from_signals(
    score: float,
    *,
    requires_risk_guardrail: bool = False,
    severe_seniority_mismatch: bool = False,
) -> DecisionType:
    """Map match score to a decision, then apply plan guardrails."""
    if severe_seniority_mismatch:
        return DecisionType.SKIP

    base = decision_from_score(score)

    if base == DecisionType.PREPARE and requires_risk_guardrail:
        return DecisionType.ESCALATE

    return base


def build_workflow_decision(
    match: ProfileMatchResult,
    signals: JobSignals,
    plan: WorkflowPlan,
) -> WorkflowDecision:
    missing_information: list[str] = []
    if SignalCategory.MISSING_SIGNALS.value in plan.required_signals:
        missing_information = [
            f"Job posting missing signal: {signal}"
            for signal in signals.missing_signals
        ]

    return WorkflowDecision(
        decision=decision_from_signals(
            match.score,
            requires_risk_guardrail=plan.requires_risk_guardrail,
            severe_seniority_mismatch=match.severe_seniority_mismatch,
        ),
        score=match.score,
        reasons=list(match.reasons),
        risks=list(match.risks),
        missing_information=missing_information,
    )
