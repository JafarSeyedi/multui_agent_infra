"""Discretionary task and planning activation for CMMN.

Supports discretionary items and planning activation rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..core.instance import ProcessInstance
from ..core.engine import OrchestrationEngine


@dataclass
class DiscretionaryItem:
    item_id: str
    name: str | None = None
    definition_type: str = "task"
    definition_ref: str | None = None
    planning_table_ref: str | None = None
    entry_criteria: list[dict[str, Any]] = field(default_factory=list)
    exit_criteria: list[dict[str, Any]] = field(default_factory=list)
    authorized_roles: list[str] = field(default_factory=list)
    is_planned: bool = False
    is_available: bool = True


@dataclass
class PlanningTableTable:
    table_id: str
    name: str | None = None
    applicability_rules: list[dict[str, Any]] = field(default_factory=list)
    discretionary_items: list[DiscretionaryItem] = field(default_factory=list)
    authorized_roles: list[str] = field(default_factory=list)


class DiscretionaryTaskHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._engine = orchestration_engine
        self._items: dict[str, DiscretionaryItem] = {}
        self._planning_tables: dict[str, PlanningTableTable] = {}

    def register(self, item: DiscretionaryItem) -> None:
        self._items[item.item_id] = item

    def register_planning_table(self, table: PlanningTableTable) -> None:
        self._planning_tables[table.table_id] = table
        for item in table.discretionary_items:
            self._items[item.item_id] = item

    def get_item(self, item_id: str) -> DiscretionaryItem | None:
        return self._items.get(item_id)

    def get_available_items(
        self,
        instance: ProcessInstance,
        user_roles: list[str] | None = None,
    ) -> list[DiscretionaryItem]:
        available: list[DiscretionaryItem] = []

        for item in self._items.values():
            if not item.is_available:
                continue
            if item.entry_criteria:
                if not self._evaluate_criteria(item.entry_criteria, instance):
                    continue
            if item.authorized_roles and user_roles:
                if not any(r in item.authorized_roles for r in user_roles):
                    continue
            available.append(item)

        return available

    def plan_item(
        self,
        item_id: str,
        instance: ProcessInstance,
        user_roles: list[str] | None = None,
    ) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        if not item.is_available:
            return False
        if item.authorized_roles and user_roles:
            if not any(r in item.authorized_roles for r in user_roles):
                return False
        if item.entry_criteria:
            if not self._evaluate_criteria(item.entry_criteria, instance):
                return False

        item.is_planned = True
        instance.set_variable(f"discretionary.{item_id}.planned", True)
        return True

    def unplan_item(self, item_id: str, instance: ProcessInstance) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        item.is_planned = False
        instance.set_variable(f"discretionary.{item_id}.planned", False)
        return True

    def get_planning_table(self, table_id: str) -> PlanningTableTable | None:
        return self._planning_tables.get(table_id)

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

    def get_summary(self, instance: ProcessInstance | None = None) -> dict[str, Any]:
        total = len(self._items)
        planned = sum(1 for i in self._items.values() if i.is_planned)
        available = sum(1 for i in self._items.values() if i.is_available)
        return {
            "total_items": total,
            "planned": planned,
            "unplanned": total - planned,
            "available": available,
            "planning_tables": len(self._planning_tables),
        }
