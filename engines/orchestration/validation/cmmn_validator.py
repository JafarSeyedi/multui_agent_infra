"""CMMN definition validator."""

from __future__ import annotations

from .validator import ValidationLevel, ValidationResult, Validator


class CMMNValidator(Validator):
    def validate(self, payload: object) -> list[ValidationResult]:
        if not isinstance(payload, dict):
            return [self._result(ValidationLevel.ERROR, "cmmn.invalid_format", "CMMN definition must be a dict-like payload")]
        if "cases" not in payload:
            return [self._result(ValidationLevel.WARNING, "cmmn.missing_cases", "No cases field in payload")]
        return []
