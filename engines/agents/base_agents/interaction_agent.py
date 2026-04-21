# agents/base_agents/interaction_agent.py
from typing import Any, Dict, Optional
from .base_agent import BaseAgent
from engines.interaction.interaction_models import InteractionRequest, InteractionResult
from engines.interaction.backends.native_backend import NativeOrchestrationBackend
from engines.buses.base_message_bus import MessageBus

class InteractionAgent(BaseAgent):
    """
    Agent سطح بالا برای اجرای workflowهای چندعامله
    """

    def __init__(self, id: str, name: str, agent_registry, message_bus: Optional[MessageBus]):
        super().__init__(id, name)

        self.backend = NativeOrchestrationBackend(
            agent_registry=agent_registry,
            message_bus=message_bus
        )

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        # تبدیل ورودی به model
        request = InteractionRequest(**payload)

        # اجرای استراتژی انتخاب‌شده
        result: InteractionResult = await self.backend.execute(request)

        # خروجی باید raw dict باشد
        return result.model_dump()
