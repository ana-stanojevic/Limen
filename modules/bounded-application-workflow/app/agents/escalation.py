"""Shared escalation and human-review triggers for planning and policy."""

from app.agents.signal_extraction import (
    has_explicit_missing_signal_phrases,
    seniority_level_is_unclear,
)
from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription


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
