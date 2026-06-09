import pytest

from app.agents import extract_job_signals
from app.agents.workflow_planning import build_workflow_plan
from app.domain.job_signals import SignalCategory
from app.domain.models import JobDescription
from tests.fixture_helpers import workflow_input


def test_extract_job_signals_respects_plan_categories():
    job = JobDescription(
        title="Platform Engineer",
        description=(
            "Operate large-scale systems with on-call rotation.\n\n"
            "- Python\n\nAmbiguous scope. We need a 10x engineer."
        ),
    )
    plan = build_workflow_plan(
        workflow_input("strong_match.json").model_copy(update={"job_description": job})
    )

    scoped = extract_job_signals(job, plan.required_signals)
    full = extract_job_signals(job)

    assert scoped.required_skills == full.required_skills
    assert SignalCategory.PRODUCTION_EXPECTATIONS.value in plan.required_signals
    assert scoped.production_expectations == full.production_expectations
    assert SignalCategory.RISK_INDICATORS.value in plan.required_signals
    assert scoped.risk_indicators == full.risk_indicators

    base_only = [
        SignalCategory.REQUIRED_SKILLS.value,
        SignalCategory.PREFERRED_SKILLS.value,
    ]
    minimal = extract_job_signals(job, base_only)
    assert minimal.required_skills == full.required_skills
    assert minimal.production_expectations == []
    assert minimal.risk_indicators == []
    assert minimal.missing_signals == []
