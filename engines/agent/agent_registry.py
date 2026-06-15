from __future__ import annotations

import logging
from typing import Any

from .._types import RawData

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Unified registry for agents and interaction strategies."""

    def __init__(self, vector_db=None, storage=None) -> None:
        self.vector_db = vector_db
        self.storage = storage
        self._agents: dict[str, Any] = {}
        self._strategies: dict[str, Any] = {}

    # --- Agent methods ---

    def register(self, agent_instance) -> Any:
        if agent_instance.vector_db is None:
            if self.vector_db is None:
                raise ValueError(f"Cannot register agent '{agent_instance.agent_name}': vector_db is required")
            agent_instance.vector_db = self.vector_db
        if agent_instance.storage is None and self.storage is not None:
            agent_instance.storage = self.storage
        self._agents[agent_instance.agent_name] = agent_instance
        return agent_instance

    def get(self, agent_name: str) -> Any | None:
        return self._agents.get(agent_name)

    async def run(self, agent_name: str, input_data: RawData) -> Any:
        agent = self.get(agent_name)
        if agent is None:
            raise ValueError(f"Agent '{agent_name}' not found")
        return await agent.run(input_data)

    def list_agents(self) -> list[str]:
        return list(self._agents.keys())

    # --- Strategy methods ---

    def register_strategy(self, scenario: str, strategy_instance) -> None:
        if scenario in self._strategies:
            raise ValueError(f"Strategy for scenario '{scenario}' already registered")
        self._strategies[scenario] = strategy_instance

    def get_strategy(self, scenario: str) -> Any | None:
        return self._strategies.get(scenario)

    def require_strategy(self, scenario: str) -> Any:
        strategy = self.get_strategy(scenario)
        if strategy is None:
            raise KeyError(f"No strategy registered for scenario '{scenario}'")
        return strategy

    def list_strategies(self) -> list[str]:
        return list(self._strategies.keys())

    def unregister_strategy(self, scenario: str) -> None:
        self._strategies.pop(scenario, None)
