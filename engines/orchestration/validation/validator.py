"""Common validation abstraction used by all domain validators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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


class Validator:
    def validate(self, payload: object) -> list[ValidationResult]:
        raise NotImplementedError

    @staticmethod
    def _result(level: ValidationLevel, code: str, message: str) -> ValidationResult:
        return ValidationResult(level=level, code=code, message=message)
