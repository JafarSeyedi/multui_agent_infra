from __future__ import annotations

from typing import Any

from .._types import Metadata
from engines.agent.agent_registry import AgentRegistry
from engines.agent.base_agents.base_agent import BaseAgent


class AgentBuilder:
    """Builder pattern — step-by-step agent construction with sensible defaults."""

    def __init__(self, agent_id: str, agent_name: str) -> None:
        self._agent_id = agent_id
        self._agent_name = agent_name
        self._vector_db: Any = None
        self._storage: Any = None
        self._metadata: Metadata | None = None
        self._extra: Metadata = {}

    def with_vector_db(self, vector_db: Any) -> AgentBuilder:
        self._vector_db = vector_db
        return self

    def with_storage(self, storage: Any) -> AgentBuilder:
        self._storage = storage
        return self

    def with_metadata(self, metadata: Metadata) -> AgentBuilder:
        self._metadata = metadata
        return self

    def with_extra(self, **kwargs: Any) -> AgentBuilder:
        self._extra.update(kwargs)
        return self

    def build(self, agent_cls: type[BaseAgent]) -> BaseAgent:
        return agent_cls(
            agent_id=self._agent_id,
            agent_name=self._agent_name,
            vector_db=self._vector_db,
            storage=self._storage,
            metadata=self._metadata,
            **self._extra,
        )

    def register(self, registry: AgentRegistry, agent_cls: type[BaseAgent]) -> BaseAgent:
        agent = self.build(agent_cls)
        registry.register(agent)
        return agent
