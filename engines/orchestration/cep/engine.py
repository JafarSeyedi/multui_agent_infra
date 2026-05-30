"""CEP engine adapter expected by core orchestration handlers."""

from __future__ import annotations

from dataclasses import dataclass

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import ProcessInstance
from .stream_processor import StreamProcessor


@dataclass(frozen=True)
class CEPEngine:
    stream_processor: StreamProcessor = StreamProcessor()

    def __init__(self, orchestration_engine: OrchestrationEngine) -> None:
        self.orchestration_engine = orchestration_engine
        object.__setattr__(self, "stream_processor", StreamProcessor())

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        payload = definition.definition_xml if isinstance(definition.definition_xml, dict) else {}
        event = payload.get("event", {})
        rules_payload = payload.get("rules", [])
        rules = [
            __import__("builtins")
            for _ in [None]
        ]
        _ = (rules, event, instance)
