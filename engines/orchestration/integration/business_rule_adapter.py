"""Business rule adapter for BPMN business rule tasks.

Integrates DMN/business rule execution with runtime scopes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.instance import ProcessInstance
from ...core.engine import OrchestrationEngine


@dataclass
class BusinessRule:
    rule_id: str = ""
    name: str | None = None
    decision_ref: str = ""
    input_mapping: list[dict[str, str]] = field(default_factory=list)
    output_variable: str = ""
    hit_policy: str = "UNIQUE"


class BusinessRuleAdapter:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._rules: dict[str, BusinessRule] = {}

    def register(self, rule: BusinessRule) -> None:
        self._rules[rule.rule_id] = rule

    def get_rule(self, rule_id: str) -> BusinessRule | None:
        return self._rules.get(rule_id)

    async def execute(
        self,
        rule: BusinessRule,
        context: dict[str, Any],
        instance: ProcessInstance | None = None,
    ) -> dict[str, Any]:
        input_data: dict[str, Any] = {}
        for mapping in rule.input_mapping:
            source = mapping.get("source")
            target = mapping.get("target")
            if source and target:
                value = context.get(source)
                if value is not None:
                    input_data[target] = value

        result = {
            "rule_id": rule.rule_id,
            "decision_ref": rule.decision_ref,
            "input": input_data,
            "output": {},
        }

        if instance and rule.output_variable:
            instance.set_variable(rule.output_variable, result)

        return result
