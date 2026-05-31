"""Data mapper for integration layer.

Supports schema-aware mapping between MSDM/DSDM structures and runtime variables.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ...core.instance import ProcessInstance


class MappingType(str, Enum):
    DIRECT = "direct"
    EXPRESSION = "expression"
    SCRIPT = "script"
    TRANSFORM = "transform"
    CONDITIONAL = "conditional"


class MappingDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class DataMapping:
    source: str = ""
    target: str = ""
    mapping_type: str = "direct"
    direction: str = "input"
    expression: str | None = None
    script_language: str = "FEEL"
    condition: str | None = None
    default_value: Any = None
    transform: dict[str, str] = field(default_factory=dict)


class DataMapper:
    def __init__(self) -> None:
        self._mappings: list[DataMapping] = []
        self._transforms: dict[str, Any] = {}

    def add_mapping(self, mapping: DataMapping) -> None:
        self._mappings.append(mapping)

    def map_input(
        self,
        source_data: dict[str, Any],
        instance: ProcessInstance,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for mapping in self._mappings:
            if mapping.direction not in ("input", "bidirectional"):
                continue
            value = self._apply_mapping(mapping, source_data)
            if value is not None:
                instance.set_variable(mapping.target, value)
                results[mapping.target] = value
        return results

    def map_output(
        self,
        instance: ProcessInstance,
    ) -> dict[str, Any]:
        results: dict[str, Any] = {}
        for mapping in self._mappings:
            if mapping.direction not in ("output", "bidirectional"):
                continue
            value = instance.get_variable(mapping.source)
            if value is not None:
                results[mapping.target] = value
        return results

    def _apply_mapping(
        self,
        mapping: DataMapping,
        source_data: dict[str, Any],
    ) -> Any:
        if mapping.condition:
            if not self._evaluate_condition(mapping.condition, source_data):
                return mapping.default_value

        if mapping.mapping_type == "direct":
            return source_data.get(mapping.source, mapping.default_value)
        elif mapping.mapping_type == "expression" and mapping.expression:
            try:
                from ...expression.evaluator import EvaluationContext
                from ...expression.python_evaluator import PythonEvaluator
                return PythonEvaluator().evaluate(mapping.expression, EvaluationContext(variables=source_data))
            except Exception:
                return mapping.default_value
        elif mapping.mapping_type == "transform":
            value = source_data.get(mapping.source)
            if value is not None and mapping.transform:
                return mapping.transform.get(str(value), value)
            return value
        else:
            return source_data.get(mapping.source, mapping.default_value)

    def _evaluate_condition(self, condition: str, context: dict[str, Any]) -> bool:
        try:
            from ...expression.evaluator import EvaluationContext
            from ...expression.python_evaluator import PythonEvaluator
            return bool(PythonEvaluator().evaluate(condition, EvaluationContext(variables=context)))
        except Exception:
            return False

    def register_transform(self, name: str, transform: dict[str, str]) -> None:
        self._transforms[name] = transform

    def get_all_mappings(self) -> list[DataMapping]:
        return list(self._mappings)
