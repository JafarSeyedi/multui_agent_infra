# agents/agent_registry.py
from __future__ import annotations

from typing import Any

from .base_agents.base_agent import BaseAgent
from engines.storage.event_log.base import LogStorage
from engines.storage.vector.base import VectorDBAdapter


class AgentRegistry:
    def __init__( self,
        vector_db: VectorDBAdapter | None = None,
        storage: LogStorage | None = None ):
        self.vector_db = vector_db
        self.storage = storage
        self.agents: dict[str, BaseAgent] = {}

    def register(self, agent_instance: BaseAgent) -> BaseAgent:
        if agent_instance.vector_db is None:
            agent_instance.vector_db = self.vector_db
        if agent_instance.storage is None:
            agent_instance.storage = self.storage
        self.agents[agent_instance.agent_name] = agent_instance
        return agent_instance

    def get(self, agent_name: str) -> BaseAgent | None:
        return self.agents.get(agent_name)

    async def run(self, agent_name: str, input_data: dict[str, Any]):
        agent = self.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent '{agent_name}' is not registered.")
        return await agent.run(input_data)
