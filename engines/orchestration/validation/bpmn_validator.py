"""BPMN definition validator."""

from __future__ import annotations

from .validator import ValidationLevel, ValidationResult, Validator


class BPMNValidator(Validator):
    def validate(self, payload: object) -> list[ValidationResult]:
        if not isinstance(payload, dict):
            return [self._result(ValidationLevel.ERROR, "bpmn.invalid_format", "BPMN definition must be a dict-like payload")]
        if "processes" not in payload:
            return [self._result(ValidationLevel.WARNING, "bpmn.missing_processes", "No processes field in payload")]
        return []
