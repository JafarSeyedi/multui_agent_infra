"""Common validation abstraction used by all domain validators.

Uses Visitor pattern (via ModelVisitor) and Chain of Responsibility
(via ValidatorChain) for composable validation pipelines.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .model_visitor import ModelVisitor


class ValidationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class ValidationResult:
    level: ValidationLevel
    code: str
    message: str

    def is_ok(self) -> bool:
        return self.level != ValidationLevel.ERROR


class Validator(ModelVisitor):
    """Base validator implementing ModelVisitor.

    Each validator implements visit_* methods to validate
    specific model node types.
    """

    @abstractmethod
    def validate(self, payload: Any) -> list[ValidationResult]:
        ...

    def visit_process(self, process: Any) -> Any: ...
    def visit_activity(self, activity: Any) -> Any: ...
    def visit_gateway(self, gateway: Any) -> Any: ...
    def visit_event(self, event: Any) -> Any: ...
    def visit_sequence_flow(self, flow: Any) -> Any: ...
    def visit_subprocess(self, subprocess: Any) -> Any: ...

    @staticmethod
    def _result(level: ValidationLevel, code: str, message: str) -> ValidationResult:
        return ValidationResult(level=level, code=code, message=message)


class ValidationChain:
    """Chain of Responsibility for validation pipeline.

    Runs validators in sequence, collecting all results.
    """

    def __init__(self) -> None:
        self._validators: list[Validator] = []

    def add_validator(self, validator: Validator) -> ValidationChain:
        self._validators.append(validator)
        return self

    def validate(self, payload: Any) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for validator in self._validators:
            results.extend(validator.validate(payload))
        return results
