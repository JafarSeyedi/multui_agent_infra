from __future__ import annotations

import logging
from typing import Any

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.models import AgentInput
from engines.agent.models import AgentOutput

logger = logging.getLogger(__name__)


class AgentMediator:
    """Mediator pattern — decouples agent communication.

    Agents interact through the mediator rather than directly,
    enabling centralized routing, logging, and transformation.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.agent_name] = agent

    def unregister(self, name: str) -> None:
        self._agents.pop(name, None)

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    async def send(
        self,
        sender: str,
        recipient: str,
        input_data: AgentInput | dict[str, Any],
    ) -> AgentOutput | None:
        agent = self._agents.get(recipient)
        if agent is None:
            logger.warning("Mediator: unknown recipient '%s'", recipient)
            return None
        if isinstance(input_data, dict):
            input_data = AgentInput(**input_data)
        result = await agent.run(input_data)
        if isinstance(result, AgentOutput):
            return result
        return AgentOutput(agent_name=recipient, payload={"result": result})

    async def broadcast(
        self,
        sender: str,
        input_data: AgentInput | dict[str, Any],
    ) -> dict[str, AgentOutput]:
        results: dict[str, AgentOutput] = {}
        for name, agent in self._agents.items():
            result = await self.send(sender, name, input_data)
            if result is not None:
                results[name] = result
        return results

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())
