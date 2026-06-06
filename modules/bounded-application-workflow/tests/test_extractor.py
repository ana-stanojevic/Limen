from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription
from app.parser import parse_job_description
from app.services.extractor import extract_job_signals
from tests.fixture_helpers import load_fixture

RAW_JOB_TEXT = """
AI Engineer

Company: Frontier AI Startup
Location: Remote Europe
Seniority: mid-senior
Employment Type: full-time

- Python
- LLM applications
- evaluation pipelines
- agentic workflows
- product ownership

+ research background
+ startup experience

Build and own LLM-based product workflows.
"""


def test_extract_job_signals_from_fixture():
    fixture = load_fixture("skill_extraction.json")
    job = JobDescription(**fixture["job_description"])
    expected = fixture["expected_signals"]

    signals = extract_job_signals(job)

    assert signals.required_skills == expected["required_skills"]
    assert signals.preferred_skills == expected["preferred_skills"]


def test_extract_job_signals_from_parsed_description():
    job = parse_job_description(RAW_JOB_TEXT)

    signals = extract_job_signals(job)

    assert signals.required_skills == [
        "Python",
        "LLM applications",
        "evaluation pipelines",
        "agentic workflows",
        "product ownership",
    ]
    assert signals.preferred_skills == [
        "research background",
        "startup experience",
    ]


def test_extract_job_signals_deduplicates_skills():
    job = JobDescription(
        title="AI Engineer",
        description="""
- Python
- python
-  Python

+ FastAPI
+ fastapi
+ React
""",
        required_skills=["Python", "LLMs"],
        nice_to_have_skills=["FastAPI", "React"],
    )

    signals = extract_job_signals(job)

    assert signals.required_skills == ["Python", "LLMs"]
    assert signals.preferred_skills == ["FastAPI", "React"]


def test_extract_job_signals_prefers_required_over_preferred():
    job = JobDescription(
        title="AI Engineer",
        description="""
- Python
+ Python
+ FastAPI
""",
        required_skills=[],
        nice_to_have_skills=["Python", "FastAPI"],
    )

    signals = extract_job_signals(job)

    assert signals.required_skills == ["Python"]
    assert signals.preferred_skills == ["FastAPI"]


def test_extract_job_signals_returns_job_signals_model():
    job = JobDescription(
        title="AI Engineer",
        description="Build LLM workflows.",
        required_skills=["Python"],
        nice_to_have_skills=["FastAPI"],
    )

    signals = extract_job_signals(job)

    assert isinstance(signals, JobSignals)
    assert signals.seniority_signals == []
    assert signals.production_expectations == []
    assert signals.risk_indicators == []
    assert signals.missing_signals == []
