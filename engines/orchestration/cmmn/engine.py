"""Case Management (CMMN) orchestration adapter.

Supports CMMN 1.1 case lifecycle (§5.2): Draft → Active → Completed/Terminated/
Suspended/Closed/Failed, with reactivation from Closed/Suspended states.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..core.context import ContextManager, ContextScope
from ..core.engine import OrchestrationEngine, ProcessDefinition
from ..core.instance import InstanceState, ProcessInstance
from ..core.event_bus import Event, EventType
from ..runtime.state_manager import StateManager
from .case_executor import CaseExecutor


logger = logging.getLogger(__name__)


class CMMNCaseState(Enum):
    """CMMN 1.1 case lifecycle states per §5.2."""
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    TERMINATED = "Terminated"
    SUSPENDED = "Suspended"
    CLOSED = "Closed"
    FAILED = "Failed"


# Valid state transitions per CMMN §5.2
CMMN_VALID_TRANSITIONS: dict[CMMNCaseState, set[CMMNCaseState]] = {
    CMMNCaseState.DRAFT: {CMMNCaseState.ACTIVE, CMMNCaseState.CLOSED},
    CMMNCaseState.ACTIVE: {CMMNCaseState.COMPLETED, CMMNCaseState.TERMINATED, CMMNCaseState.SUSPENDED, CMMNCaseState.FAILED, CMMNCaseState.CLOSED},
    CMMNCaseState.SUSPENDED: {CMMNCaseState.ACTIVE, CMMNCaseState.TERMINATED, CMMNCaseState.CLOSED},
    CMMNCaseState.COMPLETED: {CMMNCaseState.CLOSED},
    CMMNCaseState.TERMINATED: {CMMNCaseState.CLOSED},
    CMMNCaseState.FAILED: {CMMNCaseState.CLOSED, CMMNCaseState.ACTIVE},
    CMMNCaseState.CLOSED: {CMMNCaseState.ACTIVE},  # reactivate
}


@dataclass(frozen=True)
class CMMNExecutionError(RuntimeError):
    """Raised when case execution fails."""


class CMMNEngine:
    """CMMN runtime executed from a CMMN definition with full lifecycle."""

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
        self._case_states: dict[str, CMMNCaseState] = {}

    def get_case_state(self, instance_id: str) -> CMMNCaseState | None:
        return self._case_states.get(instance_id)

    def _transition(self, instance: ProcessInstance, new_state: CMMNCaseState) -> None:
        current = self._case_states.get(instance.id, CMMNCaseState.DRAFT)
        valid_next = CMMN_VALID_TRANSITIONS.get(current, set())
        if new_state not in valid_next:
            raise CMMNExecutionError(
                f"Invalid CMMN state transition: {current.value} → {new_state.value}"
            )
        self._case_states[instance.id] = new_state
        logger.info("CMMN instance %s: %s → %s", instance.id, current.value, new_state.value)

    async def start_case(self, instance: ProcessInstance) -> None:
        """Transition from Draft → Active."""
        self._transition(instance, CMMNCaseState.ACTIVE)

    async def terminate_case(self, instance: ProcessInstance, reason: str = "") -> None:
        """Force-terminate an active case (Active → Terminated)."""
        self._transition(instance, CMMNCaseState.TERMINATED)
        await self.state_manager.set_persisted(instance.id, "terminated", data={"reason": reason})
        await self.orchestration_engine.update_instance_state(
            instance.id, InstanceState.TERMINATED, reason=reason
        )

    async def suspend_case(self, instance: ProcessInstance) -> None:
        """Suspend an active case (Active → Suspended)."""
        self._transition(instance, CMMNCaseState.SUSPENDED)
        await self.state_manager.set_persisted(instance.id, "suspended")
        await self.orchestration_engine.update_instance_state(
            instance.id, InstanceState.SUSPENDED
        )

    async def resume_case(self, instance: ProcessInstance) -> None:
        """Resume a suspended case (Suspended → Active)."""
        self._transition(instance, CMMNCaseState.ACTIVE)
        await self.state_manager.set_persisted(instance.id, "running")
        await self.orchestration_engine.update_instance_state(
            instance.id, InstanceState.ACTIVE
        )

    async def close_case(self, instance: ProcessInstance) -> None:
        """Close a completed/terminated/suspended case (→ Closed)."""
        self._transition(instance, CMMNCaseState.CLOSED)
        await self.state_manager.set_persisted(instance.id, "closed")
        await self.orchestration_engine.update_instance_state(
            instance.id, InstanceState.COMPLETED, reason="closed"
        )

    async def reactivate_case(self, instance: ProcessInstance) -> None:
        """Reactivate a closed case (Closed → Active)."""
        self._transition(instance, CMMNCaseState.ACTIVE)
        await self.state_manager.set_persisted(instance.id, "running")
        await self.orchestration_engine.update_instance_state(
            instance.id, InstanceState.ACTIVE
        )

    async def execute_instance(self, instance: ProcessInstance, definition: ProcessDefinition) -> None:
        context_id = instance.id
        definition_payload: dict[str, Any] = {}

        if isinstance(definition.definition_xml, dict):
            definition_payload = definition.definition_xml

        self.context_manager.create_context(ContextScope.PROCESS, context_id)
        logger.info("CMMN engine executing instance %s", instance.id)

        # Ensure we start from DRAFT
        if instance.id not in self._case_states:
            self._case_states[instance.id] = CMMNCaseState.DRAFT

        # Transition to ACTIVE
        await self.start_case(instance)

        await self.state_manager.set_persisted(
            context_id,
            "running",
            data={"definition_key": definition.key, "definition_id": definition.id},
        )

        try:
            await self.executor.execute(instance, definition_payload)
        except Exception as exc:
            self._case_states[instance.id] = CMMNCaseState.FAILED
            await self.orchestration_engine.update_instance_state(
                instance.id, InstanceState.FAILED, reason=str(exc)
            )
            await self.state_manager.set_persisted(
                context_id,
                "failed",
                data={"definition_key": definition.key, "definition_id": definition.id, "error": str(exc)},
            )
            raise

        # Transition to COMPLETED
        self._transition(instance, CMMNCaseState.COMPLETED)
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
