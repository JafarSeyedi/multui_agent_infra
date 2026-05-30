"""DMN orchestrator used as `engine_handlers['dmn']`."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from .decision_executor import DecisionExecutor


@dataclass(frozen=True)
class DMNExecutionError(RuntimeError):
    """Raised when DMN execution fails."""


class DMNEngine:
    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self.orchestration_engine = orchestration_engine
        self.executor = DecisionExecutor()

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        payload = definition.definition_xml if isinstance(definition.definition_xml, dict) else {}
        result = self.executor.evaluate(decision=payload, context=instance.get_all_variables())
        if result is not None:
            instance.set_variable("decision_result", result)
