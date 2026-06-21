from functools import lru_cache
from pathlib import Path
from typing import Any

from app.agents.contracts import (
    SignalExtractor,
    SignalExtractorInput,
    SignalExtractorOutput,
)
from app.domain.job_signals import JobSignals
from app.domain.models import JobDescription
from app.llm.client import LLMClient, LLMClientError
from app.runtime import (
    AgentRuntime,
    BoundedAgentRuntime,
    OutputValidationError,
    PydanticOutputValidator,
    RetryPolicy,
)
from app.runtime.signal_extractor_config import SignalExtractorRuntimeConfig

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class SignalExtractionError(Exception):
    """Base error for LLM-backed signal extraction."""


class SignalExtractionLLMError(SignalExtractionError):
    """The LLM provider failed during signal extraction."""


@lru_cache
def load_system_prompt(config_version: str) -> str:
    prompt_path = _PROMPTS_DIR / f"signal_extraction_{config_version}.txt"
    if not prompt_path.is_file():
        raise FileNotFoundError(
            f"No signal extraction prompt for config version '{config_version}'"
        )
    return prompt_path.read_text(encoding="utf-8").strip()


def job_signals_schema() -> dict[str, Any]:
    schema = JobSignals.model_json_schema()
    schema["additionalProperties"] = False
    return schema


def format_job_for_prompt(job: JobDescription) -> str:
    lines = [
        f"Title: {job.title}",
        f"Company: {job.company or 'unspecified'}",
        f"Location: {job.location or 'unspecified'}",
        f"Seniority: {job.seniority or 'unspecified'}",
        f"Employment type: {job.employment_type or 'unspecified'}",
        "",
        "Description:",
        job.description,
    ]
    return "\n".join(lines)


class LLMSignalExtractor:
    """LLM-backed signal extractor with bounded runtime execution and fallback."""

    def __init__(
        self,
        *,
        client: LLMClient,
        config: SignalExtractorRuntimeConfig | None = None,
        runtime: AgentRuntime | None = None,
        fallback: SignalExtractor | None = None,
    ) -> None:
        from app.agents.default import DefaultSignalExtractor

        self._client = client
        self._config = config or SignalExtractorRuntimeConfig()
        self._runtime = runtime or BoundedAgentRuntime()
        self._fallback = fallback or DefaultSignalExtractor()

    def run(self, agent_input: SignalExtractorInput) -> SignalExtractorOutput:
        result = self._runtime.execute(
            self._extract_with_llm,
            agent_input,
            self._config,
            validator=PydanticOutputValidator(SignalExtractorOutput),
            fallback=self._fallback.run,
            retry_policy=RetryPolicy(
                retryable=(SignalExtractionLLMError, OutputValidationError),
            ),
        )

        output = result.unwrap()
        output.execution = result.without_output()
        return output

    def _extract_with_llm(
        self, agent_input: SignalExtractorInput
    ) -> SignalExtractorOutput:
        try:
            payload = self._client.complete_json(
                system=load_system_prompt(self._config.config_version),
                user=format_job_for_prompt(agent_input.job_description),
                response_schema=job_signals_schema(),
            )
        except LLMClientError as exc:
            raise SignalExtractionLLMError(str(exc)) from exc

        return SignalExtractorOutput(
            signals=JobSignals.model_construct(**payload),
        )
