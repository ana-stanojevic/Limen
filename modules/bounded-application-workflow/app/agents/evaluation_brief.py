"""Build a single evaluation view from plan focus and runtime results."""

from app.agents.signal_extraction import focus_job_signals
from app.domain.job_signals import JobSignals
from app.domain.models import (
    EvaluationBrief,
    ProfileMatchResult,
    WorkflowDecision,
)
from app.domain.workflow_run import WorkflowPlan
from app.text import dedupe_strings


def _findings_for_focus(
    focus: str,
    match: ProfileMatchResult,
    decision: WorkflowDecision,
    signals: JobSignals,
) -> list[str]:
    if focus == "required skills alignment":
        findings: list[str] = []
        if match.required_skills_matched:
            findings.append(
                "Matched required skills: "
                f"{', '.join(match.required_skills_matched)}."
            )
        if match.required_skills_missing:
            findings.append(
                "Missing required skills: "
                f"{', '.join(match.required_skills_missing)}."
            )
        return findings

    if focus == "role alignment":
        if match.role_aligned:
            return ["Job aligns with target role."]
        return ["Job does not clearly align with target role."]

    if focus == "production expectations":
        findings = []
        if match.production_expectations_matched:
            findings.append(
                "Matched production expectations: "
                f"{', '.join(match.production_expectations_matched)}."
            )
        if match.production_expectations_missing:
            findings.append(
                "Missing production expectations: "
                f"{', '.join(match.production_expectations_missing)}."
            )
        return findings

    if focus == "posting risk and ambiguity":
        return [
            *(f"Posting risk: {risk}" for risk in signals.risk_indicators),
            *(f"Ambiguity: {item}" for item in decision.missing_information),
        ]

    if focus == "seniority clarity":
        findings = []
        if signals.seniority_signals:
            findings.append(
                "Seniority signals: " f"{', '.join(signals.seniority_signals)}."
            )
        if match.severe_seniority_mismatch:
            findings.append("Severe seniority mismatch detected.")
        for risk in match.risks:
            if "seniority" in risk.casefold():
                findings.append(risk)
        return findings

    if focus == "work preference alignment":
        if match.role_aligned:
            return ["Role alignment supports stated work preferences."]
        return ["Role alignment may not match stated work preferences."]

    return []


def build_evaluation_brief(
    plan: WorkflowPlan,
    match: ProfileMatchResult,
    decision: WorkflowDecision,
    signals: JobSignals,
) -> EvaluationBrief:
    """Consolidate plan focus and runtime results into one human-readable view."""
    findings: list[str] = []
    for focus in plan.evaluation_focus:
        findings.extend(_findings_for_focus(focus, match, decision, signals))

    if not findings:
        findings = list(decision.reasons) + list(decision.risks)
        if decision.missing_information:
            findings.extend(decision.missing_information)

    return EvaluationBrief(
        evaluation_focus=list(plan.evaluation_focus),
        signal_highlights=focus_job_signals(signals, plan.required_signals),
        findings=dedupe_strings(findings),
        decision=decision.decision,
        score=decision.score,
    )
