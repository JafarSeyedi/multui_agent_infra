"""State machine engine adapter used by `OrchestrationEngine`."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from ..core.event_bus import Event, EventType
from .state_executor import StateMachineExecutor


@dataclass(frozen=True)
class StateMachineError(RuntimeError):
    """Raised when state machine execution fails."""


class StateMachineEngine:
    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self.orchestration_engine = orchestration_engine
        self.executor = StateMachineExecutor()

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        payload = definition.definition_xml if isinstance(definition.definition_xml, dict) else {}
        self.executor.execute(instance, payload)
        await self.orchestration_engine.event_bus.publish(
            Event(type=EventType.PROCESS_INSTANCE_COMPLETED, data={"instance_id": instance.id})
        )
