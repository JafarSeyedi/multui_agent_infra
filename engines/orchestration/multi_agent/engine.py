"""Multi-agent orchestration engine used by top-level coordinator.

Coordinates agent interaction lifecycle and durable conversation state
at production level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..core.event_bus import Event, EventType
from ..runtime.state_manager import StateManager
from .coordination_handler import CoordinationHandler
from .agent_executor import AgentExecutor
from .message_router import MessageRouter
from .interaction_handler import InteractionHandler
from .protocol_handler import ProtocolHandler
from .negotiation_handler import NegotiationHandler


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MultiAgentExecutionError(RuntimeError):
    """Raised when a multi-agent workflow fails."""


@dataclass
class MultiAgentPlan:
    agents: list[dict[str, Any]] = field(default_factory=list)
    interactions: list[dict[str, Any]] = field(default_factory=list)
    coordination_pattern: str = "orchestration"
    protocols: list[dict[str, Any]] = field(default_factory=list)
    negotiation_config: dict[str, Any] = field(default_factory=dict)


class MultiAgentEngine:
    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.coordinator = CoordinationHandler()
        self.agent_executor = AgentExecutor(orchestration_engine=orchestration_engine)
        self.message_router = MessageRouter()
        self.interaction_handler = InteractionHandler()
        self.protocol_handler = ProtocolHandler()
        self.negotiation_handler = NegotiationHandler()
        self._conversation_state: dict[str, dict[str, Any]] = {}

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}

        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml

        definition_payload["_engine_type"] = "multi_agent"
        definition_payload["_definition_key"] = definition.key

        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("Multi-agent engine executing instance %s", instance.id)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )

        try:
            plan = self._normalize_plan(definition_payload)
            self._conversation_state[instance.id] = {
                "agents": {a.get("id", f"agent_{i}"): a for i, a in enumerate(plan.agents)},
                "interactions": plan.interactions,
                "pattern": plan.coordination_pattern,
            }

            await self.coordinator.coordinate(instance.id, plan, instance)

            for interaction in plan.interactions:
                result = await self.interaction_handler.handle(interaction, instance, plan.agents)
                instance.set_variable(
                    f"interaction.{interaction.get('id', 'unknown')}", result
                )

            for protocol in plan.protocols:
                await self.protocol_handler.execute(protocol, instance)

            if plan.negotiation_config:
                negotiation_result = await self.negotiation_handler.negotiate(
                    plan.negotiation_config, instance, plan.agents
                )
                if negotiation_result:
                    instance.set_variable("negotiation.result", negotiation_result)

            for agent in plan.agents:
                agent_id = agent.get("id", "")
                agent_result = await self.agent_executor.execute(agent, instance)
                instance.set_variable(f"agent.{agent_id}.result", agent_result)

        except Exception as exc:
            await self.orchestration_engine.update_instance_state(
                instance.id, InstanceState.FAILED, reason=str(exc)
            )
            await self.state_manager.set_persisted(
                context_id,
                "failed",
                data={"definition_key": definition.key, "definition_id": definition.id, "error": str(exc)},
            )
            raise

        await self.orchestration_engine.update_instance_state(instance.id, InstanceState.COMPLETED)
        await self.state_manager.set_persisted(
            context_id,
            "completed",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )
        logger.info("Multi-agent instance completed: %s", instance.id)

    def _normalize_plan(self, definition_payload: dict[str, Any]) -> MultiAgentPlan:
        return MultiAgentPlan(
            agents=definition_payload.get("agents", definition_payload.get("plan", [])),
            interactions=definition_payload.get("interactions", []),
            coordination_pattern=definition_payload.get("coordinationPattern", "orchestration"),
            protocols=definition_payload.get("protocols", []),
            negotiation_config=definition_payload.get("negotiation", {}),
        )

    def get_conversation_state(self, instance_id: str) -> dict[str, Any] | None:
        return self._conversation_state.get(instance_id)
