from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from app.runtime.config import RuntimeConfig
from app.runtime.result import (
    AgentExecutionResult,
    ExecutionStatus,
    InputT,
    OutputT,
)


class AgentOperation(Protocol[InputT, OutputT]):
    """A single unit of agent work the runtime executes."""

    def __call__(self, agent_input: InputT) -> OutputT: ...


@runtime_checkable
class AgentRuntime(Protocol):
    """Common execution path for agent operations behind Protocol contracts."""

    def execute(
        self,
        operation: AgentOperation[InputT, OutputT],
        agent_input: InputT,
        config: RuntimeConfig,
    ) -> AgentExecutionResult[OutputT]: ...


class BoundedAgentRuntime:
    """Executes an agent operation through a bounded, observable lifecycle."""

    def execute(
        self,
        operation: AgentOperation[InputT, OutputT],
        agent_input: InputT,
        config: RuntimeConfig,
    ) -> AgentExecutionResult[OutputT]:
        started_at = datetime.now(timezone.utc)
        attempts = 0
        output: OutputT | None = None
        last_error: str | None = None
        status = ExecutionStatus.FAILED

        while attempts < config.max_attempts:
            attempts += 1
            try:
                output = operation(agent_input)
            except Exception as exc:  # bounded: contain, optionally retry
                last_error = f"{type(exc).__name__}: {exc}"
                continue
            status = ExecutionStatus.SUCCESS
            last_error = None
            break

        return AgentExecutionResult[OutputT](
            agent_name=config.agent_name,
            config_version=config.config_version,
            status=status,
            attempts=attempts,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            output=output,
            error=last_error,
        )
