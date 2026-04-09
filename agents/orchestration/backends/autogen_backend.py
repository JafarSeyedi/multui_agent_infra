# agents/orchestration/backends/autogen_backend.py
from __future__ import annotations

from datetime import datetime
from functools import cached_property
from typing import Dict, List, Optional, Type

from agents.buses.base import MessageBus
from agents.orchestration.interaction.base_strategy import InteractionStrategy
from .native_backend import NativeOrchestrationBackend
from agents.orchestration.models import (
    OrchestrationRequest,
    OrchestrationResult,
    TaskResult,
)
from .base_backend import BaseOrchestrationBackend


class AutoGenOrchestrationBackend(BaseOrchestrationBackend):
    """AutoGen wrapper که از GroupChat واقعی استفاده می‌کند.
    
    اگر autogen نصب نباشد یا خطا بدهد، به native backend fallback می‌کند.
    """

    def __init__(
        self,
        agent_registry,
        message_bus: Optional[MessageBus] = None,
        storage=None,
        strategy_overrides: Optional[Dict[str, Type[InteractionStrategy]]] = None,
    ):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.storage = storage
        self._strategy_overrides = strategy_overrides

        self._native = NativeOrchestrationBackend(
            agent_registry=agent_registry,
            message_bus=message_bus,
            storage=storage,
            strategy_overrides=strategy_overrides,
        )

    @cached_property
    def _autogen_available(self) -> bool:
        """یک‌بار چک می‌شه و نتیجه cache می‌مونه."""
        try:
            import autogen    # type: ignore[import-not-found] # noqa: F401 
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        """API عمومی برای بررسی در دسترس بودن autogen."""
        return self._autogen_available

    async def execute(self, request: OrchestrationRequest) -> OrchestrationResult:
        if not self._autogen_available:
            result = await self._native.execute(request)
            result.notes.append(
                "AutoGen requested but not installed; native backend used"
            )
            return result

        try:
            return await self._execute_with_autogen_group_chat(request)
        except (NotImplementedError, Exception) as exc:
            result = await self._native.execute(request)
            result.notes.append(
                f"AutoGen GroupChat failed ({exc!r}); native backend used"
            )
            return result

    async def _execute_with_autogen_group_chat(
        self,
        request: OrchestrationRequest,
    ) -> OrchestrationResult:
        """اجرای GroupChat واقعی با autogen."""
        import autogen    # type: ignore[import-not-found] # type: ignore[import-untyped]

        if not request.tasks:
            raise ValueError("request.tasks cannot be empty")

        started_at = datetime.utcnow()

        # خواندن llm_config از context
        llm_config: Dict = request.context.get("llm_config", {"model": "gpt-4"})

        # ساخت AssistantAgent برای هر task
        autogen_agents: List[autogen.AssistantAgent] = []
        for task in request.tasks:
            system_message = (
                task.system_message 
                or task.description 
                or task.metadata.get("system_message", "")
            )
            agent = autogen.AssistantAgent(
                name=task.agent_name,
                system_message=system_message,
                llm_config=llm_config,
            )
            autogen_agents.append(agent)

        # ساخت GroupChat و Manager
        group_chat = autogen.GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=max(len(request.tasks) * 2, 4),
        )
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )

        # شروع مکالمه با اولین task
        first_task = request.tasks[0]
        initial_message = str(first_task.payload.get("message", "start"))

        await autogen_agents[0].a_initiate_chat(
            manager,
            message=initial_message,
        )

        # جمع‌آوری نتایج از پیام‌های GroupChat
        chat_messages = group_chat.messages
        results: List[TaskResult] = []

        for idx, task in enumerate(request.tasks):
            content = ""
            if idx < len(chat_messages):
                content = chat_messages[idx].get("content", "")

            results.append(
                TaskResult(
                    task_id=task.task_id,
                    agent_name=task.agent_name,
                    success=True,
                    output={"content": content},
                    metadata={"message_index": idx},
                )
            )

        completed_at = datetime.utcnow()

        return OrchestrationResult(
            workflow_id=request.workflow_id,
            scenario=request.scenario,
            results=results,
            success=True,
            final_context={
                **request.context,
                "autogen_messages": chat_messages,
            },
            backend_used="autogen-groupchat",
            status="success",
            started_at=started_at,
            completed_at=completed_at,
            notes=[
                f"AutoGen GroupChat: {len(chat_messages)} messages, "
                f"{len(autogen_agents)} agents"
            ],
            metadata={
                "total_messages": len(chat_messages),
                "total_agents": len(autogen_agents),
            },
        )
