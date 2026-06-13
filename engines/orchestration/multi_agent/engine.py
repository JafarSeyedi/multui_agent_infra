"""Multi-agent orchestration engine used by top-level coordinator.

Coordinates agent interaction lifecycle and durable conversation state
at production level. Delegates handler communication to MultiAgentMediator.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..runtime.state_manager import StateManager
from .mediator import AgentMediator, MultiAgentMediator


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
        mediator: AgentMediator | None = None,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.mediator = mediator or MultiAgentMediator(
            orchestration_engine, state_manager=self.state_manager,
        )
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

            for agent_entry in plan.agents:
                agent_id = agent_entry.get("id", "")
                if agent_id:
                    self.mediator.register_agent(agent_id, agent_entry)

            result = await self.mediator.execute_workflow(instance, definition, plan)

            if not result.success:
                raise MultiAgentExecutionError("; ".join(result.errors))

            await self.state_manager.set_persisted(
                context_id,
                "completed",
                data={"definition_key": definition.key, "definition_id": definition.id},
            )

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

    @property
    def coordinator(self):
        return self.mediator.coordinator

    @property
    def message_router(self):
        return self.mediator.message_router
