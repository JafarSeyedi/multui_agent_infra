"""DMN orchestrator used as `engine_handlers['dmn']`.

Coordinates decision execution and integration with process/case runtimes
at DMN 1.3 specification level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from .decision_requirements_graph import DmnDecisionServiceExecutor
from engines.orchestration.models.osdm_models import DecisionService
from ..core.event_bus import Event, EventType
from .decision_executor import DecisionExecutor


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DMNExecutionError(RuntimeError):
    """Raised when DMN execution fails."""


class DMNEngine:
    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.executor = DecisionExecutor(orchestration_engine=orchestration_engine)
        self.drg_executor = DmnDecisionServiceExecutor(self.executor)

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}

        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml

        definition_payload["_engine_type"] = "dmn"
        definition_payload["_definition_key"] = definition.key

        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("DMN engine evaluating decision for instance %s", instance.id)

        try:
            result = await self.executor.evaluate(
                decision=definition_payload,
                context=instance.get_all_variables(),
                instance=instance,
            )
            if result is not None:
                instance.set_variable("decision_result", result)
                instance.set_variable("decision_status", "completed")

            if self.orchestration_engine is not None:
                await self.orchestration_engine.event_bus.publish(
                    Event(
                        type=EventType.PROCESS_INSTANCE_COMPLETED,
                        data={
                            "instance_id": instance.id,
                            "engine_type": "dmn",
                            "decision_result": result,
                        },
                    )
                )
        except Exception as exc:
            instance.set_variable("decision_error", str(exc))
            raise DMNExecutionError(f"DMN evaluation failed for {definition.key}: {exc}") from exc

        logger.info("DMN decision completed for instance %s: %s", instance.id, result)
