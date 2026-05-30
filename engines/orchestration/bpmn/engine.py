"""BPMN 2.0 orchestration engine implementation."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..runtime.state_manager import StateManager
from .process_executor import BPMNProcessExecutor


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BPMNExecutionError(RuntimeError):
    """Raised when BPMN runtime cannot execute a definition."""


class BPMNEngine:
    """Engine adapter used by :class:`OrchestrationEngine` via `engine_handlers`."""

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.executor = BPMNProcessExecutor(
            engine=self,
            orchestration_engine=orchestration_engine,
            state_manager=self.state_manager,
            context_manager=self.context_manager,
        )

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}
        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml
        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("BPMN engine executing instance %s", instance.id)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )
        try:
            outcome = await self.executor.execute(instance, definition_payload)
        except Exception as exc:
            await self.orchestration_engine.update_instance_state(instance.id, InstanceState.FAILED, reason=str(exc))
            await self.state_manager.set_persisted(
                context_id,
                "failed",
                data={"definition_key": definition.key, "definition_id": definition.id, "error": str(exc)},
            )
            raise

        if outcome.completed:
            await self.orchestration_engine.update_instance_state(instance.id, InstanceState.COMPLETED)
            await self.state_manager.set_persisted(
                context_id,
                "completed",
                data={"definition_key": definition.key, "definition_id": definition.id},
            )
            return

        final_state = "waiting" if outcome.waiting else (instance.state.value if hasattr(instance.state, "value") else str(instance.state))
        await self.state_manager.set_persisted(
            context_id,
            final_state,
            data={"definition_key": definition.key, "definition_id": definition.id, "current_node": outcome.current_node},
        )
        logger.debug("BPMN instance paused in state for %s: %s", instance.id, final_state)
