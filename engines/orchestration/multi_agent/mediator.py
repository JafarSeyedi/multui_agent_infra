"""Mediator pattern for multi-agent coordination.

Centralizes communication between agents and handlers, decoupling
MultiAgentEngine from direct handler invocation and agent-to-agent
message passing.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from ..._types import MessagePayload, Metadata, RawData, VariableValue

from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.event_bus import Event, EventType
from ..core.instance import InstanceState, ProcessInstance
from ..runtime.state_manager import StateManager
from .agent_executor import AgentExecutionResult, AgentExecutor
from .coordination_handler import CoordinationHandler
from .interaction_handler import InteractionHandler
from .message_router import AgentMessage, MessageRouter, RoutingResult
from .negotiation_handler import NegotiationHandler
from .protocol_handler import ProtocolHandler


logger = logging.getLogger(__name__)


@dataclass
class MediationResult:
    success: bool
    results: Metadata = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class AgentMediator(ABC):
    """Mediator interface for agent communication and coordination."""

    @abstractmethod
    async def notify(self, sender: str, event: str, data: MessagePayload) -> None:
        ...

    @abstractmethod
    async def send_message(self, message: AgentMessage, instance: ProcessInstance | None = None) -> RoutingResult:
        ...

    @abstractmethod
    async def broadcast(self, message: AgentMessage, recipients: list[str], instance: ProcessInstance | None = None) -> list[RoutingResult]:
        ...

    @abstractmethod
    def register_agent(self, agent_id: str, agent_data: Metadata) -> None:
        ...

    @abstractmethod
    def get_agent(self, agent_id: str) -> Metadata | None:
        ...

    @abstractmethod
    async def execute_agent(self, agent: Metadata, instance: ProcessInstance) -> AgentExecutionResult:
        ...

    @abstractmethod
    async def coordinate(self, instance_id: str, plan: Any, instance: ProcessInstance) -> Metadata:
        ...

    @abstractmethod
    async def handle_interaction(self, interaction: Metadata, instance: ProcessInstance, agents: list[dict[str, Any]]) -> Metadata:
        ...

    @abstractmethod
    async def execute_protocol(self, protocol: Metadata, instance: ProcessInstance) -> Metadata:
        ...

    @abstractmethod
    async def negotiate(self, config: Metadata, instance: ProcessInstance, agents: list[dict[str, Any]]) -> Metadata | None:
        ...

    @abstractmethod
    async def execute_workflow(
        self, instance: ProcessInstance, definition: ProcessDefinition, plan: Any,
    ) -> MediationResult:
        ...


class MultiAgentMediator(AgentMediator):
    """Concrete mediator that coordinates all agent communication.

    Owns all handlers and manages message routing, agent registration,
    and event dispatch. Handlers communicate through this mediator
    rather than directly with each other or with agents.
    """

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self._orchestration_engine = orchestration_engine
        self._state_manager = state_manager or orchestration_engine.state_manager

        from engines.agent.agent_mediator import AgentMediator as CoreAgentMediator
        self._core_mediator = CoreAgentMediator()

        self.coordinator = CoordinationHandler()
        self.interaction_handler = InteractionHandler()
        self.protocol_handler = ProtocolHandler()
        self.negotiation_handler = NegotiationHandler()
        self.agent_executor = AgentExecutor(orchestration_engine=orchestration_engine)
        self.message_router = MessageRouter(orchestration_engine=orchestration_engine)

        self._agents: dict[str, Metadata] = {}
        self._conversation_state: dict[str, MessagePayload] = {}

    async def notify(self, sender: str, event: str, data: MessagePayload) -> None:
        logger.debug("Mediator notify: %s sent %s", sender, event)
        await self._orchestration_engine.event_bus.publish(
            Event(
                type=EventType.ACTIVITY_COMPLETED,
                data={"sender": sender, "event": event, **data},
            )
        )

    async def send_message(self, message: AgentMessage, instance: ProcessInstance | None = None) -> RoutingResult:
        return self.message_router.route(message, instance)

    async def broadcast(
        self, message: AgentMessage, recipients: list[str],
        instance: ProcessInstance | None = None,
    ) -> list[RoutingResult]:
        return self.message_router.broadcast(message, recipients, instance)

    def register_agent(self, agent_id: str, agent_data: Metadata) -> None:
        self._agents[agent_id] = agent_data
        self._core_mediator.register_agent(agent_data)

    def get_agent(self, agent_id: str) -> Metadata | None:
        return self._agents.get(agent_id)

    async def execute_agent(self, agent: Metadata, instance: ProcessInstance) -> AgentExecutionResult:
        result = await self.agent_executor.execute(agent, instance)
        await self.notify("agent_executor", "agent_executed", {
            "instance_id": instance.id,
            "agent_id": agent.get("id", ""),
            "success": result.success,
        })
        return result

    async def coordinate(self, instance_id: str, plan: Any, instance: ProcessInstance) -> Metadata:
        result = await self.coordinator.coordinate(instance_id, plan, instance)
        await self.notify("coordinator", "coordination_completed", {
            "instance_id": instance_id,
            "pattern": getattr(plan, "coordination_pattern", "orchestration"),
        })
        return result

    async def handle_interaction(
        self, interaction: Metadata, instance: ProcessInstance,
        agents: list[dict[str, Any]],
    ) -> Metadata:
        result = await self.interaction_handler.handle(interaction, instance, agents)
        await self.notify("interaction_handler", "interaction_completed", {
            "instance_id": instance.id,
            "interaction_id": interaction.get("id", ""),
        })
        return result

    async def execute_protocol(self, protocol: Metadata, instance: ProcessInstance) -> Metadata:
        result = await self.protocol_handler.execute(protocol, instance)
        await self.notify("protocol_handler", "protocol_executed", {
            "instance_id": instance.id,
            "protocol_id": protocol.get("id", ""),
        })
        return result

    async def negotiate(
        self, config: Metadata, instance: ProcessInstance,
        agents: list[dict[str, Any]],
    ) -> Metadata | None:
        result = await self.negotiation_handler.negotiate(config, instance, agents)
        await self.notify("negotiation_handler", "negotiation_completed", {
            "instance_id": instance.id,
        })
        return result

    async def execute_workflow(
        self,
        instance: ProcessInstance,
        definition: ProcessDefinition,
        plan: Any,
    ) -> MediationResult:
        """Execute a complete multi-agent workflow through the mediator."""
        results: Metadata = {}
        errors: list[str] = []

        try:
            coord_result = await self.coordinate(instance.id, plan, instance)
            results["coordination"] = coord_result

            for interaction in plan.interactions:
                interaction_result = await self.handle_interaction(
                    interaction, instance, plan.agents,
                )
                instance.set_variable(
                    f"interaction.{interaction.get('id', 'unknown')}", interaction_result,
                )
                results.setdefault("interactions", {})[interaction.get('id', '')] = interaction_result

            for protocol in plan.protocols:
                protocol_result = await self.execute_protocol(protocol, instance)
                results.setdefault("protocols", {})[protocol.get('id', '')] = protocol_result

            if plan.negotiation_config:
                negotiation_result = await self.negotiate(
                    plan.negotiation_config, instance, plan.agents,
                )
                if negotiation_result:
                    instance.set_variable("negotiation.result", negotiation_result)
                results["negotiation"] = negotiation_result

            for agent in plan.agents:
                agent_id = agent.get("id", "")
                agent_result = await self.execute_agent(agent, instance)
                instance.set_variable(f"agent.{agent_id}.result", agent_result.result)
                results.setdefault("agent_results", {})[agent_id] = str(agent_result.result)

            return MediationResult(success=True, results=results)

        except Exception as exc:
            logger.exception("Workflow execution failed via mediator")
            errors.append(str(exc))
            return MediationResult(success=False, results=results, errors=errors)
