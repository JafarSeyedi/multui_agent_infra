# agents/orchestration/interaction/base_strategy.py
from typing import Dict, List, Protocol, Any
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult
)
from config.models.system.interaction_models import AgentMessage
from agents.orchestration.buses.base import MessageBus

class InteractionStrategy:
    def __init__(self, registry, message_bus: MessageBus, storage):
        self.registry = registry
        self.message_bus = message_bus
        self.storage = storage

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        raise NotImplementedError()

