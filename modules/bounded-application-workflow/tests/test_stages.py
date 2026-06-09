import pytest

from app.agents import (
    build_workflow_decision,
    decision_from_score,
    decision_from_signals,
    extract_job_signals,
    match_profile_to_job,
    seniority_level_is_unclear,
)
from app.domain.job_signals import JobSignals
from app.domain.models import DecisionType, JobDescription, ProfileMatchResult, UserProfile
from app.parser import parse_job_description
from tests.fixture_helpers import AI_ENGINEER_JOB_TEXT, load_fixture, workflow_input


def _match(name: str):
    wf = workflow_input(name)
    signals = extract_job_signals(wf.job_description)
    return match_profile_to_job(wf.user_profile, wf.job_description, signals)


@pytest.mark.parametrize("fixture", ["skill_extraction.json", "risk_extraction.json"])
def test_extract_job_signals_fixtures(fixture):
    data = load_fixture(fixture)
    signals = extract_job_signals(JobDescription(**data["job_description"]))
    expected = data["expected_signals"]
    for field in (
        "required_skills",
        "preferred_skills",
        "seniority_signals",
        "production_expectations",
        "risk_indicators",
        "missing_signals",
    ):
        if field in expected:
            assert getattr(signals, field) == expected[field]


def test_extract_job_signals_parsed_and_skill_rules():
    signals = extract_job_signals(parse_job_description(AI_ENGINEER_JOB_TEXT))
    assert signals.required_skills[:2] == ["Python", "LLM applications"]
    assert signals.missing_signals == ["salary range", "team size"]

    deduped = extract_job_signals(
        JobDescription(
            title="AI Engineer",
            description="- Python\n- python\n- LLMs\n+ FastAPI\n+ fastapi\n+ React",
        )
    )
    assert deduped.required_skills == ["Python", "LLMs"]
    assert deduped.preferred_skills == ["FastAPI", "React"]

    required_wins = extract_job_signals(
        JobDescription(title="AI Engineer", description="- Python\n+ Python\n+ FastAPI")
    )
    assert required_wins.required_skills == ["Python"]
    assert required_wins.preferred_skills == ["FastAPI"]


@pytest.mark.parametrize(
    "title,description,seniority,field,expected",
    [
        (
            "Senior AI Engineer",
            "Looking for 5+ years of experience building ML systems.",
            None,
            "seniority_signals",
            ["5+ years of experience", "Senior"],
        ),
        (
            "Platform Engineer",
            "Operate large-scale inference systems with on-call rotation and production-ready deployment.",
            None,
            "production_expectations",
            ["on-call rotation", "large-scale inference", "production readiness"],
        ),
        (
            "Full Stack Unicorn Engineer",
            "Ambiguous scope with high infrastructure ownership. We need a 10x engineer who can wear many hats.",
            None,
            "risk_indicators",
            [
                "ambiguous scope",
                "unrealistic expectations",
                "broad unfocused role",
                "high ownership expectations",
            ],
        ),
    ],
)
def test_extract_job_signals_patterns(title, description, seniority, field, expected):
    signals = extract_job_signals(
        JobDescription(title=title, description=description, seniority=seniority)
    )
    assert getattr(signals, field) == expected


def test_seniority_and_missing_signal_detection():
    job = JobDescription(
        title="Engineer",
        description="- product ownership\nBuild and own product workflows.",
        seniority=None,
    )
    assert seniority_level_is_unclear(job)
    signals = extract_job_signals(job)
    assert "product ownership" in signals.seniority_signals
    assert "seniority level" in signals.missing_signals

    explicit = extract_job_signals(
        JobDescription(
            title="ML Engineer",
            description=(
                "Build ML models.\n\n- Python\n\n"
                "No explicit remote policy. Seniority level unclear. Compensation not listed."
            ),
        )
    )
    assert {"remote policy", "seniority level", "salary range"} <= set(
        explicit.missing_signals
    )


@pytest.mark.parametrize(
    "fixture,min_score,max_score,role_aligned",
    [
        ("strong_match.json", 0.5, 1.0, True),
        ("weak_match.json", 0.0, 0.35, False),
        ("ambiguous_match.json", 0.35, 0.75, True),
    ],
)
def test_match_fixtures(fixture, min_score, max_score, role_aligned):
    result = _match(fixture)
    assert min_score <= result.score <= max_score
    assert result.role_aligned is role_aligned


def test_match_skill_and_seniority_behavior():
    weak = _match("weak_match.json")
    assert weak.required_skills_matched == []
    assert set(weak.required_skills_missing) == {
        "React", "TypeScript", "CSS", "frontend architecture", "design systems"
    }
    assert any("Job expects senior" in risk for risk in weak.risks)

    ambiguous = _match("ambiguous_match.json")
    assert ambiguous.required_skills_matched and ambiguous.required_skills_missing

    job = JobDescription(title="Platform Engineer", description="Operate services.")
    aligned = UserProfile(
        name="Ana", skills=["Python"], production_experience=["on-call rotation", "observability"]
    )
    partial = UserProfile(name="Ana", skills=["Python"], production_experience=["on-call rotation"])
    signals = JobSignals(
        required_skills=["Python"],
        production_expectations=["on-call rotation", "observability"],
    )
    assert match_profile_to_job(aligned, job, signals).score > match_profile_to_job(
        partial, job, signals
    ).score

    for profile_seniority, job_seniority in [("staff", "junior"), ("junior", "principal")]:
        result = match_profile_to_job(
            UserProfile(name="Ana", seniority=profile_seniority),
            JobDescription(
                title=f"{job_seniority.title()} Engineer",
                description="- Python",
                seniority=job_seniority,
            ),
            JobSignals(required_skills=["Python"], seniority_signals=[job_seniority]),
        )
        assert result.severe_seniority_mismatch


@pytest.mark.parametrize(
    "score,expected",
    [
        (0.0, DecisionType.SKIP),
        (0.34, DecisionType.SKIP),
        (0.35, DecisionType.ESCALATE),
        (0.54, DecisionType.ESCALATE),
        (0.55, DecisionType.QUEUE),
        (0.74, DecisionType.QUEUE),
        (0.75, DecisionType.PREPARE),
        (1.0, DecisionType.PREPARE),
    ],
)
def test_decision_from_score(score, expected):
    assert decision_from_score(score) == expected


@pytest.mark.parametrize(
    "score,requires_risk_guardrail,severe,expected",
    [
        (0.9, True, False, DecisionType.ESCALATE),
        (0.9, False, False, DecisionType.PREPARE),
        (0.9, True, True, DecisionType.SKIP),
    ],
)
def test_decision_from_signals(score, requires_risk_guardrail, severe, expected):
    assert (
        decision_from_signals(
            score,
            requires_risk_guardrail=requires_risk_guardrail,
            severe_seniority_mismatch=severe,
        )
        == expected
    )


def test_build_workflow_decision():
    from app.domain.workflow_run import WorkflowPlan
    from app.domain.workflow_state import WorkflowState

    plan = WorkflowPlan(
        stages=[WorkflowState.POLICY_EVALUATION, WorkflowState.DECISION],
        required_signals=["missing_signals"],
        requires_risk_guardrail=True,
    )
    match = ProfileMatchResult(
        score=0.82,
        reasons=["Matched 1 of 2 required skills."],
        risks=["Missing required skills: Kubernetes."],
    )
    signals = JobSignals(
        risk_indicators=["ambiguous scope"], missing_signals=["salary range"]
    )
    decision = build_workflow_decision(match, signals, plan)
    assert decision.decision == DecisionType.ESCALATE
    assert decision.missing_information == ["Job posting missing signal: salary range"]
