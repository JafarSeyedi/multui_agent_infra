from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel

from agents.base_agent import BaseAgent
from agents.message_bus import InMemoryMessageBus
from agents.registry import AgentRegistry

from .backends import AutoGenOrchestrationBackend, NativeOrchestrationBackend
from .models import OrchestrationRequest, OrchestrationResult


class OrchestratorAgent(BaseAgent):
    agent_name = "OrchestratorAgent"
    agent_version = "1.0.0"
    InputModel = OrchestrationRequest
    OutputModel = OrchestrationResult

    def __init__(self, registry: AgentRegistry, message_bus: InMemoryMessageBus | None = None, **kwargs):
        super().__init__(**kwargs)
        self.registry = registry
        self.message_bus = message_bus
        self.native_backend = NativeOrchestrationBackend(registry=registry, message_bus=message_bus)
        self.autogen_backend = AutoGenOrchestrationBackend(registry=registry, message_bus=message_bus)

    async def execute(self, input_model: OrchestrationRequest) -> Dict[str, Any]:
        """
        Execute an orchestration workflow and always return a JSON-serializable dict.

        This method is resilient to different backend result types:
        - Pydantic v2 models (model_dump)
        - Pydantic v1 models (dict)
        - Raw dicts
        - Fallback: return the object as-is (last resort)
        """
        request: OrchestrationRequest


        # اگر کاربر یک dict خام پاس داد، آن را به OrchestrationRequest تبدیل کن
        if isinstance(input_data, dict):
            request = OrchestrationRequest(**input_data)
        else:
            request = input_data

        # انتخاب backend بر اساس request.backend
        if request.backend == "native":
            result = await self.native_backend.run(request)
        elif request.backend == "autogen":
            result = await self.autogen_backend.run(request)
        else:  # "auto"
            result = await self._run_auto(request)


        # نرمال‌سازی خروجی
        # 1) Pydantic v2
        if hasattr(result, "model_dump") and callable(getattr(result, "model_dump")):
            try:
                return result.model_dump()
            except Exception:
                # اگر به هر دلیل model_dump شکست خورد، ادامه می‌دهیم
                pass

        # 2) Pydantic v1
        if hasattr(result, "dict") and callable(getattr(result, "dict")):
            try:
                return result.dict()
            except Exception:
                pass

        # 3) اگر خود result یک dict بود
        if isinstance(result, dict):
            return result

        # 4) آخرین راه‌حل: object را همان‌طور برگردان (ممکن است در لایه‌ی بالاتر هندل شود)
        return result
    
    async def _run_auto(self, input_model: OrchestrationRequest) -> OrchestrationResult:
        if input_model.scenario in {"group_chat", "round_robin", "selector"} and self.autogen_backend.is_available():
            return await self.autogen_backend.run(input_model)
        return await self.native_backend.run(input_model)
