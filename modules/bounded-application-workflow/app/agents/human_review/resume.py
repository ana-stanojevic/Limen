"""Human review payloads for LangGraph interrupt / Command resume."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.models import WorkflowDecision


class HumanReviewInterrupt(BaseModel):
    """Value surfaced by ``interrupt()`` when policy escalates."""

    reason: str
    decision: WorkflowDecision
    workflow_id: str
    requested_at: datetime


class HumanReviewResume(BaseModel):
    """Payload passed via ``Command(resume=...)`` to resolve an escalation."""

    decision: WorkflowDecision
    approved: bool
    reviewer_notes: str = Field(default="")
    requested_at: datetime


def approve_escalation(
    decision: WorkflowDecision,
    *,
    requested_at: datetime,
    reviewer_notes: str = "Approved without changes.",
) -> HumanReviewResume:
    """Keep the escalated decision as-is."""
    return HumanReviewResume(
        decision=decision,
        approved=True,
        reviewer_notes=reviewer_notes,
        requested_at=requested_at,
    )


def revise_escalation(
    decision: WorkflowDecision,
    *,
    requested_at: datetime,
    reviewer_notes: str = "",
) -> HumanReviewResume:
    """Replace the escalated decision with a revised one."""
    return HumanReviewResume(
        decision=decision,
        approved=False,
        reviewer_notes=reviewer_notes,
        requested_at=requested_at,
    )


def parse_review_resume(value: object) -> HumanReviewResume:
    if isinstance(value, HumanReviewResume):
        return value
    return HumanReviewResume.model_validate(value)
