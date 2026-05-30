"""Multi-agent orchestration engine used by top-level coordinator."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from .coordination_handler import CoordinationHandler


@dataclass(frozen=True)
class MultiAgentExecutionError(RuntimeError):
    """Raised when a multi-agent workflow fails."""


class MultiAgentEngine:
    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self.orchestration_engine = orchestration_engine
        self.coordinator = CoordinationHandler()

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        definition_payload = definition.definition_xml if isinstance(definition.definition_xml, dict) else {}
        plan = definition_payload.get("plan", [])
        self.coordinator.coordinate(instance.id, plan)
