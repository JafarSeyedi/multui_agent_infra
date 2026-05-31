"""Case Management (CMMN) orchestration adapter.

Supports CMMN 1.1 case lifecycle, durable state, sentry/event interaction,
and case file management at production level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..core.event_bus import Event, EventType
from ..runtime.state_manager import StateManager
from .case_executor import CaseExecutor


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CMMNExecutionError(RuntimeError):
    """Raised when case execution fails."""


class CMMNEngine:
    """CMMN runtime executed from a CMMN definition."""

    def __init__(
        self,
        orchestration_engine: OrchestrationEngine,
        *,
        state_manager: StateManager | None = None,
    ) -> None:
        self.orchestration_engine = orchestration_engine
        self.context_manager = ContextManager()
        self.state_manager = state_manager or orchestration_engine.state_manager
        self.executor = CaseExecutor(orchestration_engine=orchestration_engine)

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}

        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml

        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("CMMN engine executing instance %s", instance.id)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )

        try:
            await self.executor.execute(instance, definition_payload)
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
        await self.orchestration_engine.event_bus.publish(
            Event(
                type=EventType.PROCESS_INSTANCE_COMPLETED,
                data={"instance_id": instance.id, "engine_type": "cmmn"},
            )
        )
        logger.info("CMMN instance completed: %s", instance.id)
