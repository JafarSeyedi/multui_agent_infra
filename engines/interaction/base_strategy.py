# agents/interaction/base_strategy.py

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime
from engines.agents.models import AgentInput, AgentOutput
from engines.buses.base_message_bus import MessageBus
from engines.interaction.interaction_models import AgentMessage

class InteractionStrategy:
    scenario_name: str = "base"

    def __init__(self, agent_registry, message_bus: Optional[MessageBus] = None, storage=None):
        self.agent_registry = agent_registry
        self.message_bus = message_bus
        self.storage = storage

    async def execute(self, request):
        raise NotImplementedError

    # ------------------------------------------------
    # Event emitter
    # ------------------------------------------------

    async def _emit(
        self,
        message_type: str,
        payload: Dict[str, Any],
        sender: str,
        recipient: str,
        message_id: str,
    ) -> None:

        if not self.message_bus:
            return

        await self.message_bus.publish(
            AgentMessage(
                message_type= message_type,
                sender= sender,
                recipient= recipient,
                message_id= message_id,
                payload= payload,
                timestamp = datetime.now()
            )
        )

    # ------------------------------------------------
    # AgentInput builder
    # ------------------------------------------------

    def _build_input(
        self,
        agent_name: str,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentInput:

        return AgentInput(
            agent_name=agent_name,
            message=message,
            payload=payload or {},
            context=context or {},
        )

    # ------------------------------------------------
    # Safe agent execution
    # ------------------------------------------------

    async def _run_agent(
        self,
        agent_name: str,
        agent_id: str,
        context: Dict[str, Any],
        payload: Optional[Dict[str, Any]] = None,
        message: Optional[str] = None,
    ) -> AgentOutput:

        agent = self.agent_registry.get(agent_name)

        if agent is None:
            return AgentOutput(
                agent_id=agent_id,
                agent_name=agent_name,
                error=f"Agent '{agent_name}' not found",
            )

        try:

            agent_input = self._build_input(
                agent_name=agent_name,
                message=message,
                payload=payload,
                context=context,
            )

            output: AgentOutput = await agent.run(agent_input)

            if output.agent_id is None:
                output.agent_id = agent_id

            return output

        except Exception as exc:

            return AgentOutput(
                agent_id=agent_id,
                agent_name=agent_name,
                error=str(exc),
            )
