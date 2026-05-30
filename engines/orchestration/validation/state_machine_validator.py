"""State machine definition validator."""

from __future__ import annotations

from .validator import ValidationLevel, ValidationResult, Validator


class StateMachineValidator(Validator):
    def validate(self, payload: object) -> list[ValidationResult]:
        if not isinstance(payload, dict):
            return [self._result(ValidationLevel.ERROR, "sm.invalid_format", "State machine definition must be a dict-like payload")]
        if "states" not in payload:
            return [self._result(ValidationLevel.WARNING, "sm.missing_states", "No states field in payload")]
        return []
