from typing import Generic, Protocol, runtime_checkable

from pydantic import BaseModel, ValidationError

from app.runtime.result import OutputT


class OutputValidationError(Exception):
    """Agent output failed schema validation."""


@runtime_checkable
class OutputValidator(Protocol[OutputT]):
    """Validate a typed agent output before accepting it."""

    def validate(self, output: OutputT) -> OutputT: ...


class PydanticOutputValidator(Generic[OutputT]):
    """Re-validate agent output against a Pydantic model."""

    def __init__(self, model: type[BaseModel]) -> None:
        self._model = model

    def validate(self, output: OutputT) -> OutputT:
        try:
            return self._model.model_validate(output.model_dump())  # type: ignore[return-value]
        except ValidationError as exc:
            raise OutputValidationError(str(exc)) from exc


class RetryPolicy:
    """Decide whether a failed attempt should be retried."""

    def __init__(
        self,
        *,
        retryable: tuple[type[Exception], ...] = (Exception,),
    ) -> None:
        self._retryable = retryable

    def should_retry(self, exc: Exception) -> bool:
        return isinstance(exc, self._retryable)
