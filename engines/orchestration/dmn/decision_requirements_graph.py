"""Decision Requirements Graph (DRG) for DMN.

Implements DRG parsing, dependency graph building, topological execution,
and input/output mapping between chained decisions per DMN 1.3.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .models.dmn_models import Decision, DecisionService, InputData, BusinessKnowledgeModel


logger = logging.getLogger(__name__)


@dataclass
class DecisionNode:
    decision_id: str
    name: str | None = None
    required_decisions: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    encapsulated_decisions: list[str] = field(default_factory=list)
    output_decisions: list[str] = field(default_factory=list)
    input_data_refs: list[str] = field(default_factory=list)
    bkm_refs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    in_degree: int = 0


class DecisionRequirementsGraph:
    """Builds and executes decision requirement graphs."""

    def __init__(self) -> None:
        self._nodes: dict[str, DecisionNode] = {}
        self._execution_order: list[str] = []

    def build_from_decisions(self, decisions: list[Decision]) -> None:
        for decision in decisions:
            node = DecisionNode(
                decision_id=decision.id,
                name=getattr(decision, "name", None),
            )
            if hasattr(decision, "required_decisions") and decision.required_decisions:
                for rd in decision.required_decisions:
                    ref_id = rd.id if hasattr(rd, "id") else str(rd)
                    node.required_decisions.append(ref_id)
                    node.dependencies.append(ref_id)
                    node.in_degree += 1
            if hasattr(decision, "required_inputs") and decision.required_inputs:
                for ri in decision.required_inputs:
                    ref_id = ri.id if hasattr(ri, "id") else str(ri)
                    node.required_inputs.append(ref_id)
            if hasattr(decision, "input_data") and decision.input_data:
                for id_ref in decision.input_data:
                    node.input_data_refs.append(id_ref.id if hasattr(id_ref, "id") else str(id_ref))
            self._nodes[decision.id] = node
        self._compute_topological_order()

    def build_from_decision_service(self, ds: DecisionService) -> None:
        if hasattr(ds, "encapsulated_decisions") and ds.encapsulated_decisions:
            for ed in ds.encapsulated_decisions:
                node = DecisionNode(
                    decision_id=ed.id,
                    name=getattr(ed, "name", None),
                    dependencies=[],
                )
                self._nodes[ed.id] = node
        if hasattr(ds, "output_decisions") and ds.output_decisions:
            for od in ds.output_decisions:
                if od.id in self._nodes:
                    self._nodes[od.id].in_degree = len(self._nodes[od.id].dependencies)

    def _compute_topological_order(self) -> None:
        self._execution_order = []
        in_degrees = {nid: node.in_degree for nid, node in self._nodes.items()}
        queue = [nid for nid, deg in in_degrees.items() if deg == 0]
        while queue:
            current = queue.pop(0)
            self._execution_order.append(current)
            for nid, node in self._nodes.items():
                if current in node.dependencies:
                    in_degrees[nid] -= 1
                    if in_degrees[nid] == 0:
                        queue.append(nid)
        if len(self._execution_order) != len(self._nodes):
            logger.warning("DRG has circular dependencies; topological sort incomplete")

    def get_execution_order(self) -> list[str]:
        return list(self._execution_order)

    def get_node(self, decision_id: str) -> DecisionNode | None:
        return self._nodes.get(decision_id)

    def get_dependencies(self, decision_id: str) -> list[str]:
        node = self._nodes.get(decision_id)
        return list(node.dependencies) if node else []

    def get_ready_decisions(self, completed: set[str]) -> list[str]:
        ready = []
        for nid, node in self._nodes.items():
            if nid in completed:
                continue
            if all(dep in completed for dep in node.dependencies):
                ready.append(nid)
        return ready

    def is_fully_executed(self, completed: set[str]) -> bool:
        return all(nid in completed for nid in self._nodes)


class DmnDecisionServiceExecutor:
    """Executes DecisionService with DRG-aware chaining."""

    def __init__(self, decision_executor: Any) -> None:
        self._decision_executor = decision_executor
        self._drg = DecisionRequirementsGraph()

    def register_decisions(self, decisions: list[Decision]) -> None:
        self._drg.build_from_decisions(decisions)

    async def execute_decision_service(
        self,
        ds: DecisionService,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        self._drg.build_from_decision_service(ds)
        results: dict[str, Any] = {}
        completed: set[str] = set()
        execution_order = self._drg.get_execution_order()
        for decision_id in execution_order:
            node = self._drg.get_node(decision_id)
            if node is None:
                continue
            dep_results = {}
            for dep_id in node.dependencies:
                if dep_id in results:
                    dep_results[dep_id] = results[dep_id]
            merged_context = dict(context)
            merged_context.update(dep_results)
            try:
                result = await self._decision_executor.evaluate(
                    Decision(id=decision_id, name=node.name),
                    merged_context,
                )
                results[decision_id] = result
                completed.add(decision_id)
            except Exception as e:
                logger.error("Decision %s failed: %s", decision_id, e)
                results[decision_id] = {"error": str(e)}
        return {
            "results": results,
            "completed": list(completed),
            "output_decisions": [
                results.get(od.id if hasattr(od, "id") else str(od))
                for od in (getattr(ds, "output_decisions", []) or [])
            ],
        }
