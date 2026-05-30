"""DMN definition validator."""

from __future__ import annotations

from .validator import ValidationLevel, ValidationResult, Validator


class DMNValidator(Validator):
    def validate(self, payload: object) -> list[ValidationResult]:
        if not isinstance(payload, dict):
            return [self._result(ValidationLevel.ERROR, "dmn.invalid_format", "DMN definition must be a dict-like payload")]
        if "decisions" not in payload:
            return [self._result(ValidationLevel.WARNING, "dmn.missing_decisions", "No decisions field in payload")]
        return []
