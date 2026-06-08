# agents/interaction/backends/autogen_backend.py
from __future__ import annotations

from datetime import datetime
from functools import cached_property

from ...agents.models import AgentOutput
from .base_backend import BaseOrchestrationBackend
from .native_backend import NativeOrchestrationBackend
from engines.communication.buses.base_message_bus import MessageBus
from engines.interaction.base_strategy import InteractionStrategy
from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.interaction_models import InteractionResult


class AutoGenOrchestrationBackend(BaseOrchestrationBackend):
    """
    AutoGen backend wrapper.

    If autogen is not installed, falls back to native backend.
    """

    def __init__(
        self,
        agent_registry,
        message_bus: MessageBus | None = None,
        storage=None,
        strategy_overrides: dict[str, type[InteractionStrategy]] | None = None,
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
        try:
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._autogen_available

    async def execute(self, request: InteractionRequest) -> InteractionResult:

        if not self._autogen_available:
            result = await self._native.execute(request)
            result.notes.append(
                "AutoGen requested but not installed; native backend used"
            )
            return result

        try:
            return await self._execute_with_autogen_group_chat(request)
        except Exception as exc:
            result = await self._native.execute(request)
            result.notes.append(
                f"AutoGen GroupChat failed ({exc!r}); native backend used"
            )
            return result

    async def _execute_with_autogen_group_chat(
        self,
        request: InteractionRequest,
    ) -> InteractionResult:

        import autogen  # type: ignore

        if not request.agents:
            raise ValueError("request.agents cannot be empty")

        started_at = datetime.utcnow()

        # 1) llm_config
        llm_config: dict = request.context.get(
            "llm_config",
            {"model": "gpt-4"}
        )

        # 2) Get system_message from metadata/context
        default_system = request.metadata.get(
            "default_system_message",
            "You are an AI assistant in a multi-agent conversation."
        )

        # 3) Build AutoGen agents
        autogen_agents: list[autogen.AssistantAgent] = []

        for agent_spec in request.agents:

            # agent-specific system prompt
            system_message = (
                agent_spec.metadata.get("system_message")
                or default_system
            )

            a = autogen.AssistantAgent(
                name=agent_spec.agent_name,
                system_message=system_message,
                llm_config=llm_config,
            )
            autogen_agents.append(a)

        # 4) Build GroupChat
        group_chat = autogen.GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=max(4, len(autogen_agents) * 2),
        )

        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config,
        )

        # 5) initial message
        initial_message = request.context.get("initial_message", "start")

        await autogen_agents[0].a_initiate_chat(
            manager,
            message=str(initial_message),
        )

        # 6) Results
        chat_messages = group_chat.messages
        results: list[AgentOutput] = []

        # map each agent to message index if exists
        for idx, agent_spec in enumerate(request.agents):
            msg_content = ""

            if idx < len(chat_messages):
                msg_content = chat_messages[idx].get("content", "") or ""

            results.append(
                AgentOutput(
                    agent_id=agent_spec.agent_id,
                    agent_name=agent_spec.agent_name,
                    message=msg_content,
                    payload={"content": msg_content},
                    error=None,
                    metadata={"message_index": idx},
                )
            )

        completed_at = datetime.utcnow()

        return InteractionResult(
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
                f"{len(autogen_agents)} agents used"
            ],
            metadata={
                "total_messages": len(chat_messages),
                "total_agents": len(autogen_agents),
            },
        )
