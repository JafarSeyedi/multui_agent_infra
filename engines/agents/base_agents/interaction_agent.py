# agents/base_agents/interaction_agent.py
from typing import Any

from ...buses.base_message_bus import MessageBus
from ...interaction.backends.native_backend import NativeOrchestrationBackend
from ...interaction.interaction_models import InteractionRequest
from ...interaction.interaction_models import InteractionResult
from .base_agent import BaseAgent

class InteractionAgent(BaseAgent):
    """
    Agent سطح بالا برای اجرای workflowهای چندعامله
    """

    def __init__(self, id: str, name: str, agent_registry, message_bus: MessageBus | None):
        super().__init__(id, name)

        self.backend = NativeOrchestrationBackend(
            agent_registry=agent_registry,
            message_bus=message_bus
        )

    async def run(self, payload: dict[str, Any]) -> dict[str, Any]:

        # تبدیل ورودی به model
        request = InteractionRequest(**payload)

        # اجرای استراتژی انتخاب‌شده
        result: InteractionResult = await self.backend.execute(request)

        # خروجی باید raw dict باشد
        return result.model_dump()
