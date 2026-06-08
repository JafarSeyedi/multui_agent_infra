# agents/base_agents/interaction_agent.py
from typing import Any

from ...communication.buses.base_message_bus import MessageBus
from ...interaction.backends.native_backend import NativeOrchestrationBackend
from ...interaction.interaction_models import InteractionRequest
from ...interaction.interaction_models import InteractionResult
from .base_agent import BaseAgent

class InteractionAgent(BaseAgent):
    """
    High-level agent for executing multi-agent workflows
    """

    def __init__(self, id: str, name: str, agent_registry, message_bus: MessageBus | None) -> None:
        super().__init__(id, name)

        self.backend = NativeOrchestrationBackend(
            agent_registry=agent_registry,
            message_bus=message_bus
        )

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:

        # Convert input to model
        request = InteractionRequest(**payload)

        # Execute selected strategy
        result: InteractionResult = await self.backend.execute(request)

        # Output must be raw dict
        return result.model_dump()
