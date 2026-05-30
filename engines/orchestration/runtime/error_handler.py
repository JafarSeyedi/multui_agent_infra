"""Error capture and recovery helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from enum import Enum


class ErrorLevel(Enum):
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ExecutionError(RuntimeError):
    """Domain error for execution engine failures."""


@dataclass
class ErrorRecord:
    scope: str
    error: str
    level: ErrorLevel
    metadata: dict[str, Any]


@dataclass
class ErrorRecoveryContext:
    scope: str
    retries: int = 0
    max_retries: int = 3


class ErrorResolver:
    """Apply recover/retry strategy to a function invocation."""

    def __init__(
        self,
        *,
        default_handler: Callable[[ExecutionError, ErrorRecoveryContext], None] | None = None,
    ) -> None:
        self._default_handler = default_handler
        self._errors: list[ErrorRecord] = []

    def record(self, scope: str, exc: Exception, *, level: ErrorLevel = ErrorLevel.ERROR) -> None:
        self._errors.append(
            ErrorRecord(
                scope=scope,
                error=str(exc),
                level=level,
                metadata={"type": type(exc).__name__},
            )
        )

    def handle(self, exc: Exception, context: ErrorRecoveryContext) -> None:
        if isinstance(exc, ExecutionError):
            self.record(context.scope, exc, level=ErrorLevel.ERROR)
        else:
            self.record(context.scope, exc, level=ErrorLevel.CRITICAL)

        if self._default_handler is not None:
            self._default_handler(ExecutionError(str(exc)), context)

    def errors(self) -> list[ErrorRecord]:
        return list(self._errors)

    def clear(self) -> None:
        self._errors.clear()
