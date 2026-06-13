from __future__ import annotations

import logging
from typing import Any

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.models import AgentOutput
from engines.communication.buses.base_message_bus import MessageBus
from engines.interaction.interaction_models import InteractionRequest
from engines.interaction.interaction_models import InteractionResult

logger = logging.getLogger(__name__)


class InteractionMediator:
    """Mediator pattern — centralizes agent interaction orchestration.

    Manages the turn-taking, message routing, and lifecycle of multi-agent
    conversations. Strategies are registered by scenario name and the
    mediator dispatches to the appropriate strategy at runtime.
    """

    def __init__(self, message_bus: MessageBus | None = None) -> None:
        self._strategies: dict[str, Any] = {}
        self._agent_registry: dict[str, BaseAgent] = {}
        self._message_bus = message_bus

    def register_strategy(self, name: str, strategy_cls: type) -> None:
        self._strategies[name] = strategy_cls

    def register_agent(self, agent: BaseAgent) -> None:
        self._agent_registry[agent.agent_name] = agent

    async def execute(
        self,
        scenario: str,
        agents: list[str],
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> InteractionResult:
        strategy_cls = self._strategies.get(scenario)
        if strategy_cls is None:
            return InteractionResult(
                scenario=scenario,
                results=[],
                success=False,
                final_context={},
                status="failed",
                notes=[f"Unknown scenario '{scenario}'"],
            )
        agent_instances = [self._agent_registry[name] for name in agents if name in self._agent_registry]
        strategy = strategy_cls(
            agent_registry=self._agent_registry,
            message_bus=self._message_bus,
            **{k: v for k, v in kwargs.items() if k != "agents"},
        )
        request = InteractionRequest(
            workflow_id=kwargs.get("workflow_id", ""),
            scenario=scenario,
            agents=agent_instances,
            context=context or {},
            metadata=kwargs.get("metadata", {}),
        )
        return await strategy.execute(request)

    def list_scenarios(self) -> list[str]:
        return list(self._strategies.keys())

    def list_agents(self) -> list[str]:
        return list(self._agent_registry.keys())
