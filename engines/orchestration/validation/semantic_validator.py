"""Cross-domain semantic validation."""

from __future__ import annotations

from typing import Any

from .validator import ValidationLevel, ValidationResult, Validator


class SemanticValidator(Validator):
    def validate(self, payload: Any) -> list[ValidationResult]:
        if not isinstance(payload, dict):
            return [self._result(ValidationLevel.ERROR, "semantic.invalid_format", "Payload must be dictionary")]
        issues = []
        if "id" not in payload:
            issues.append(self._result(ValidationLevel.WARNING, "semantic.missing_id", "Payload is missing identifier"))
        if "name" not in payload:
            issues.append(self._result(ValidationLevel.INFO, "semantic.missing_name", "Payload is missing display name"))
        return issues

    def find_reference_gaps(self, payload: dict[str, Any], refs: set[str]) -> set[str]:
        referenced = set(str(v) for v in payload.get("references", []))
        return referenced - refs
