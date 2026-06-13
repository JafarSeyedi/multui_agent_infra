from __future__ import annotations

import logging
from typing import Any

from engines.agent.base_agents.base_agent import BaseAgent
from engines.agent.base_agents.skill_agent import SkillAgent
from engines.agent.base_agents.state_machine_agent import StateMachineAgent

logger = logging.getLogger(__name__)


class AgentFactory:
    """Abstract Factory — centralized agent creation with consistent DI."""

    _registry: dict[str, type[BaseAgent]] = {}

    @classmethod
    def register(cls, name: str, agent_cls: type[BaseAgent]) -> None:
        cls._registry[name] = agent_cls

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> BaseAgent:
        agent_cls = cls._registry.get(name)
        if agent_cls is None:
            raise ValueError(f"Unknown agent type '{name}'. Registered: {list(cls._registry)}")
        return agent_cls(**kwargs)

    @classmethod
    def known_types(cls) -> list[str]:
        return list(cls._registry)


class SkillAgentFactory:
    """Factory for SkillAgent — bundles SkillLoader + LLMClient provisioning."""

    @staticmethod
    def create(
        agent_id: str,
        agent_name: str,
        skill_id: str,
        skill_loader: Any = None,
        llm_client: Any = None,
        **kwargs: Any,
    ) -> SkillAgent:
        return SkillAgent(
            agent_id=agent_id,
            agent_name=agent_name,
            skill_id=skill_id,
            skill_loader=skill_loader,
            llm_client=llm_client,
            **kwargs,
        )


class StateMachineAgentFactory:
    """Factory for StateMachineAgent."""

    @staticmethod
    def create(
        agent_id: str,
        agent_name: str,
        state_machine_doc: Any,
        skill_loader: Any = None,
        llm_client: Any = None,
        **kwargs: Any,
    ) -> StateMachineAgent:
        return StateMachineAgent(
            agent_id=agent_id,
            agent_name=agent_name,
            state_machine_doc=state_machine_doc,
            skill_loader=skill_loader,
            llm_client=llm_client,
            **kwargs,
        )
