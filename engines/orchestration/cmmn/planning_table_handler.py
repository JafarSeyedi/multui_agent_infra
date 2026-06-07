"""Planning table behavior and authorized planning actions for CMMN.

Supports planning table behavior and authorized planning actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.instance import ProcessInstance
from ..core.engine import OrchestrationEngine
from .discretionary_handler import DiscretionaryItem, PlanningTableTable


class PlanningTableHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._tables: dict[str, PlanningTableTable] = {}

    def register_table(self, table: PlanningTableTable) -> None:
        self._tables[table.table_id] = table

    def get_table(self, table_id: str) -> PlanningTableTable | None:
        return self._tables.get(table_id)

    def process(
        self,
        table_id: str,
        instance: ProcessInstance,
        user_roles: list[str] | None = None,
    ) -> list[DiscretionaryItem]:
        table = self._tables.get(table_id)
        if table is None:
            return []

        available_items: list[DiscretionaryItem] = []

        for item in table.discretionary_items:
            if not item.is_available:
                continue
            if item.authorized_roles and user_roles:
                if not any(r in item.authorized_roles for r in user_roles):
                    continue
            if table.applicability_rules:
                if not self._evaluate_applicability_rules(table.applicability_rules, instance):
                    continue
            if item.entry_criteria:
                if not self._evaluate_criteria(item.entry_criteria, instance):
                    continue
            available_items.append(item)

        return available_items

    def authorize_planning(
        self,
        table_id: str,
        item_id: str,
        user_roles: list[str],
    ) -> bool:
        table = self._tables.get(table_id)
        if table is None:
            return False

        for item in table.discretionary_items:
            if item.item_id == item_id:
                if item.authorized_roles:
                    return any(r in item.authorized_roles for r in user_roles)
                return True

        return False

    def _evaluate_applicability_rules(
        self,
        rules: list[dict[str, Any]],
        instance: ProcessInstance,
    ) -> bool:
        if not rules:
            return True
        context = instance.get_all_variables()
        for rule in rules:
            condition = rule.get("condition") or rule.get("body")
            if condition:
                from ..expression.evaluator import EvaluationContext
                from ..expression.python_evaluator import PythonEvaluator
                try:
                    result = PythonEvaluator().evaluate(condition, EvaluationContext(variables=context))
                    if not result:
                        return False
                except Exception:
                    return False
        return True

    def _evaluate_criteria(
        self,
        criteria: list[dict[str, Any]],
        instance: ProcessInstance,
    ) -> bool:
        if not criteria:
            return True
        context = instance.get_all_variables()
        for criterion in criteria:
            expression = criterion.get("condition") or criterion.get("body")
            if expression:
                from ..expression.evaluator import EvaluationContext
                from ..expression.python_evaluator import PythonEvaluator
                try:
                    result = PythonEvaluator().evaluate(expression, EvaluationContext(variables=context))
                    if not result:
                        return False
                except Exception:
                    return False
        return True

    def get_statistics(self) -> dict[str, Any]:
        total_items = sum(len(t.discretionary_items) for t in self._tables.values())
        return {
            "total_tables": len(self._tables),
            "total_discretionary_items": total_items,
        }
