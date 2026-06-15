from __future__ import annotations

from typing import Any

from ...communication.buses.base_message_bus import MessageBus
from ..interaction_models import InteractionRequest
from ..interaction_models import InteractionResult
from .base_agent import BaseAgent


class InteractionAgent(BaseAgent):

    def __init__(self, id: str, name: str, agent_registry, message_bus: MessageBus | None = None):
        super().__init__(id, name)
        self._backend = None
        self._agent_registry = agent_registry
        self._message_bus = message_bus

    @property
    def backend(self):
        if self._backend is None:
            from ..backends.native_backend import NativeOrchestrationBackend
            self._backend = NativeOrchestrationBackend(
                agent_registry=self._agent_registry,
                message_bus=self._message_bus,
            )
        return self._backend

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = InteractionRequest(**payload)
        result: InteractionResult = await self.backend.execute(request)
        return result.model_dump()

    async def execute(self, input_model: Any) -> Any:
        return await self.run(input_model.model_dump() if hasattr(input_model, 'model_dump') else input_model)
