import pytest

from app.agents.contracts import SignalExtractorInput, SignalExtractorOutput
from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription
from app.runtime import (
    AgentExecutionResult,
    AgentRuntime,
    BoundedAgentRuntime,
    ExecutionStatus,
    OutputValidationError,
    PydanticOutputValidator,
    RetryPolicy,
    RuntimeConfig,
    RuntimeExecutionError,
)


def _input() -> SignalExtractorInput:
    return SignalExtractorInput(
        job_description=JobDescription(title="AI Engineer", description="- Python")
    )


def _ok(_: SignalExtractorInput) -> SignalExtractorOutput:
    return SignalExtractorOutput(signals=JobSignals(required_skills=["Python"]))


def _fail(_: SignalExtractorInput) -> SignalExtractorOutput:
    raise RuntimeError("model unavailable")


class _Flaky:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def __call__(self, agent_input: SignalExtractorInput) -> SignalExtractorOutput:
        self.calls += 1
        if self.calls <= self.failures:
            raise ValueError("transient failure")
        return _ok(agent_input)


def _execute(operation, **config) -> AgentExecutionResult[SignalExtractorOutput]:
    return BoundedAgentRuntime().execute(
        operation, _input(), RuntimeConfig(agent_name="signal_extractor", **config)
    )


def test_runtime_satisfies_protocol():
    assert isinstance(BoundedAgentRuntime(), AgentRuntime)


def test_success_returns_typed_output():
    result = _execute(_ok)

    assert result.succeeded and result.status == ExecutionStatus.SUCCESS
    assert result.attempts == 1
    assert result.error is None
    assert not result.used_fallback
    assert result.agent_name == "signal_extractor"
    assert result.config_version == "v1"
    assert result.output.signals.required_skills == ["Python"]
    assert result.duration_ms >= 0.0


def test_failure_is_captured_not_raised():
    result = _execute(_fail)

    assert result.status == ExecutionStatus.FAILED
    assert not result.succeeded
    assert result.output is None
    assert not result.used_fallback
    assert "model unavailable" in (result.error or "")


def test_retries_until_success():
    operation = _Flaky(failures=2)

    result = _execute(operation, max_attempts=3)

    assert result.succeeded
    assert result.attempts == operation.calls == 3


def test_stops_after_attempts_exhausted():
    operation = _Flaky(failures=5)

    result = _execute(operation, max_attempts=2)

    assert not result.succeeded
    assert result.attempts == operation.calls == 2


def test_unwrap_returns_output_or_raises():
    assert _execute(_ok).unwrap().signals.required_skills == ["Python"]
    with pytest.raises(RuntimeExecutionError):
        _execute(_fail).unwrap()


@pytest.mark.parametrize(
    "overrides",
    [{"max_attempts": 0}, {"max_attempts": 6}, {"agent_name": ""}],
)
def test_config_enforces_bounds(overrides: dict):
    with pytest.raises(ValueError):
        RuntimeConfig(**{"agent_name": "signal_extractor", **overrides})



def _invalid_output(_: SignalExtractorInput) -> SignalExtractorOutput:
    return SignalExtractorOutput(
        signals=JobSignals.model_construct(required_skills="Python")
    )


def test_validator_rejects_invalid_output():
    result = BoundedAgentRuntime().execute(
        _invalid_output,
        _input(),
        RuntimeConfig(agent_name="signal_extractor", max_attempts=1),
        validator=PydanticOutputValidator(SignalExtractorOutput),
    )

    assert not result.succeeded
    assert result.attempts == 1
    assert result.error.startswith("OutputValidationError")


def test_validator_retries_before_failing():
    calls = 0

    def flaky_invalid(_: SignalExtractorInput) -> SignalExtractorOutput:
        nonlocal calls
        calls += 1
        if calls == 1:
            return SignalExtractorOutput(
                signals=JobSignals.model_construct(required_skills="Python")
            )
        return _ok(_)

    result = BoundedAgentRuntime().execute(
        flaky_invalid,
        _input(),
        RuntimeConfig(agent_name="signal_extractor", max_attempts=2),
        validator=PydanticOutputValidator(SignalExtractorOutput),
    )

    assert result.succeeded
    assert result.attempts == calls == 2


def test_fallback_runs_after_primary_failure():
    result = BoundedAgentRuntime().execute(
        _fail,
        _input(),
        RuntimeConfig(agent_name="signal_extractor", max_attempts=1),
        fallback=_ok,
    )

    assert result.succeeded
    assert result.used_fallback
    assert result.attempts == 1
    assert "model unavailable" in (result.error or "")
    assert result.output.signals.required_skills == ["Python"]


def test_fallback_failure_preserves_primary_error():
    def fallback_fail(_: SignalExtractorInput) -> SignalExtractorOutput:
        raise RuntimeError("fallback unavailable")

    result = BoundedAgentRuntime().execute(
        _fail,
        _input(),
        RuntimeConfig(agent_name="signal_extractor", max_attempts=1),
        fallback=fallback_fail,
    )

    assert not result.succeeded
    assert not result.used_fallback
    assert "model unavailable" in (result.error or "")


def test_retry_policy_skips_non_retryable_errors():
    calls = 0

    def fail_once(_: SignalExtractorInput) -> SignalExtractorOutput:
        nonlocal calls
        calls += 1
        raise ValueError("bad config")

    result = BoundedAgentRuntime().execute(
        fail_once,
        _input(),
        RuntimeConfig(agent_name="signal_extractor", max_attempts=3),
        retry_policy=RetryPolicy(retryable=(RuntimeError,)),
    )

    assert not result.succeeded
    assert result.attempts == calls == 1
