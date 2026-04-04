# class InteractionStrategy:
#     def __init__(self, registry, message_bus, storage):
#         self.registry = registry
#         self.message_bus = message_bus
#         self.storage = storage
#     async def run(self, request):
#         raise NotImplementedError()


# agents/orchestration/interaction/base_strategy.py
from typing import Dict, List, Protocol, Any
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationExecution,
    PipelineStep,
)
from agents.message_bus import AgentMessage  # اگر در مسیر واقعی است


class InteractionStrategy:
    def __init__(self, registry, message_bus, storage):
        self.registry = registry
        self.message_bus = message_bus
        self.storage = storage

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        raise NotImplementedError()

