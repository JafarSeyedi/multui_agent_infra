# agents/orchestration/orchestrator_agent.py
from typing import Any, Dict
from agents.base_agent import BaseAgent

from .models import OrchestrationRequest, OrchestrationResult
from .backends.native_backend import NativeOrchestrationBackend
from agents.buses.base import MessageBus

class OrchestratorAgent(BaseAgent):
    """
    Agent سطح بالا برای اجرای workflowهای چندعامله
    """

    def __init__(self, name: str, agent_registry, message_bus: MessageBus):
        super().__init__(name)

        self.backend = NativeOrchestrationBackend(
            agent_registry=agent_registry,
            message_bus=message_bus
        )

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        # تبدیل ورودی به model
        request = OrchestrationRequest(**payload)

        # اجرای استراتژی انتخاب‌شده
        result: OrchestrationResult = await self.backend.execute(request)

        # خروجی باید raw dict باشد
        return result.model_dump()
