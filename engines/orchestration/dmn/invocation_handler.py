"""Invocation handler for DMN decisions.

Supports invocation/business knowledge/decision service behavior at DMN 1.3 level.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.engine import OrchestrationEngine
from .feel_engine import FEELEngine


@dataclass
class Binding:
    parameter: str
    literal_expression: str | None = None
    decision_ref: str | None = None
    bkm_ref: str | None = None


@dataclass
class Invocation:
    called_element: str = ""
    called_type: str = "decision"
    bindings: list[Binding] = field(default_factory=list)


@dataclass
class InvocationResult:
    called_element: str
    result: Any = None
    binding_results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class InvocationHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._feel_engine = FEELEngine()
        self._cache: dict[str, InvocationResult] = {}

    async def invoke(
        self,
        invocation_data: dict[str, Any],
        context: dict[str, Any],
    ) -> Any:
        called_element = (
            invocation_data.get("calledElement")
            or invocation_data.get("called_element")
            or invocation_data.get("decisionRef")
            or invocation_data.get("bkmRef")
            or ""
        )

        if not called_element:
            return None

        bindings: list[Binding] = []
        for binding_data in invocation_data.get("binding", invocation_data.get("bindings", [])):
            param = (
                binding_data.get("parameter")
                or binding_data.get("formalParameter")
                or binding_data.get("name", "")
            )
            literal = (
                binding_data.get("literalExpression")
                or binding_data.get("literal_expression")
                or binding_data.get("expression")
            )
            binding = Binding(parameter=param, literal_expression=literal)
            bindings.append(binding)

        resolved_bindings: dict[str, Any] = {}
        binding_errors: list[str] = []

        for binding in bindings:
            if binding.literal_expression:
                try:
                    value = self._feel_engine.evaluate(binding.literal_expression, context)
                    resolved_bindings[binding.parameter] = value
                except Exception as e:
                    binding_errors.append(f"Binding {binding.parameter} failed: {e}")
            else:
                value = context.get(binding.parameter)
                resolved_bindings[binding.parameter] = value

        merged_context = dict(context)
        merged_context.update(resolved_bindings)

        result = self._resolve_called_element(called_element, merged_context)

        inv_result = InvocationResult(
            called_element=called_element,
            result=result,
            binding_results=resolved_bindings,
            errors=binding_errors,
        )
        self._cache[called_element] = inv_result
        return result

    def _resolve_called_element(self, called_element: str, context: dict[str, Any]) -> Any:
        value = context.get(called_element)
        if value is not None:
            return value

        decision_ref = context.get(f"decision.{called_element}")
        if decision_ref is not None:
            return decision_ref

        return context.get(f"input.{called_element}")

    def get_cached_result(self, called_element: str) -> InvocationResult | None:
        return self._cache.get(called_element)

    def clear_cache(self) -> None:
        self._cache.clear()
