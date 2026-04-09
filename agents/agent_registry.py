# agents/registry.py
from __future__ import annotations

from typing import Any, Dict, Optional

from .base_agent import BaseAgent

from storage.base_storage import StorageAdapter
from storage.vector.base import VectorDBAdapter


class AgentRegistry:
    def __init__( self,
        vector_db: Optional[VectorDBAdapter] = None,
        storage: Optional[StorageAdapter] = None ):
        self.vector_db = vector_db
        self.storage = storage
        self.agents: Dict[str, BaseAgent] = {}

    def register(self, agent_instance: BaseAgent) -> BaseAgent:
        if agent_instance.vector_db is None:
            agent_instance.vector_db = self.vector_db
        if agent_instance.storage is None:
            agent_instance.storage = self.storage
        self.agents[agent_instance.agent_name] = agent_instance
        return agent_instance

    def get(self, agent_name: str) -> Optional[BaseAgent]:
        return self.agents.get(agent_name)

    async def run(self, agent_name: str, input_data: Dict[str, Any]):
        agent = self.get(agent_name)
        if agent is None:
            raise KeyError(f"Agent '{agent_name}' is not registered.")
        return await agent.run(input_data)
