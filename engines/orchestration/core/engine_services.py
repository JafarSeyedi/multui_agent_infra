"""Focused services extracted from OrchestrationEngine.

Each service has a single responsibility and operates on
state dicts owned by the engine facade.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from collections.abc import Callable

from ._definition_models import Deployment, ProcessDefinition

from ..._types import Metadata, RawData, VariableValue


# ── Duck-typed service protocols ────────────────────────────────


class _BamEngine(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...


class _RecoveryService(Protocol):
    async def recover(self) -> RawData: ...


class _StateManager(Protocol):
    async def set_persisted(self, instance_id: str, state: str, *, data: dict[str, Any] | None = None) -> Any: ...


class _VariableManager(Protocol):
    async def set_persisted(self, instance_id: str, scope_id: str, name: str, value: Any, *, value_type: str | None = None, overwrite: bool = True, metadata: dict[str, Any] | None = None) -> Any: ...
    async def restore_persisted(self, instance_id: str, scope_id: str | None = None) -> Any: ...


class _EngineHandler(Protocol):
    async def execute_instance(self, instance: ProcessInstance, definition: Any) -> None: ...


class _CorrelationEngine(Protocol):
    async def cleanup_instance_subscriptions_persisted(self, instance_id: str) -> Any: ...
    async def reload_from_history(self) -> None: ...


class _DefinitionRepository(Protocol):
    def list(self) -> list[RawData]: ...


class _DefinitionLike(Protocol):
    id: str
    key: str
    version: int
    name: str
    deployment_id: str
    resource_name: str
    definition_type: str
    definition_xml: str
    deployed_at: datetime


class _DeploymentLike(Protocol):
    definitions: list[_DefinitionLike]


class _InstanceLike(Protocol):
    definition_id: str
from uuid import uuid4

from .event_bus import Event, EventBus, EventType
from .instance import InstanceManager, InstanceState, ProcessInstance
from .scheduler import Scheduler, ScheduledTask
from .token import TokenManager

logger = logging.getLogger(__name__)


# ── Lifecycle ──────────────────────────────────────────────────


class EngineLifecycleService:
    """Manages engine lifecycle: start, stop, pause, resume."""

    def __init__(
        self,
        event_bus: EventBus,
        scheduler: Scheduler,
        event_type: type,
        recovery_service: _RecoveryService | None = None,
        bam_engine: _BamEngine | None = None,
        config: Any = None,
    ) -> None:
        self._event_bus = event_bus
        self._scheduler = scheduler
        self._event_type = event_type
        self._recovery_service = recovery_service
        self._bam_engine = bam_engine
        self._config = config

    async def start(self) -> None:
        if self._recovery_service:
            await self._recovery_service.recover()
        await self._event_bus.start()
        await self._scheduler.start()
        if self._bam_engine:
            await self._bam_engine.start()

    async def stop(self) -> None:
        await self._scheduler.stop()
        await self._event_bus.stop()
        if self._bam_engine:
            await self._bam_engine.stop()


# ── Instance management ───────────────────────────────────────


class InstanceService:
    """Manages process instance lifecycle."""

    def __init__(
        self,
        instance_manager: InstanceManager,
        token_manager: TokenManager,
        variable_manager: _VariableManager,
        state_manager: _StateManager,
        event_bus: EventBus,
        correlation_engine: _CorrelationEngine,
        engine_handlers: dict[str, _EngineHandler],
        scheduler: Scheduler,
    ) -> None:
        self._instance_manager = instance_manager
        self._token_manager = token_manager
        self._variable_manager = variable_manager
        self._state_manager = state_manager
        self._event_bus = event_bus
        self._correlation_engine = correlation_engine
        self._engine_handlers = engine_handlers
        self._scheduler = scheduler

    async def start_instance(
        self,
        definition: _DefinitionLike,
        business_key: str | None = None,
        variables: dict[str, VariableValue] | None = None,
        tenant_id: str | None = None,
        *,
        instance: ProcessInstance | None = None,
        persist_fn: Callable[..., Any] | None = None,
    ) -> ProcessInstance:
        if instance is None:
            instance = ProcessInstance(
                id=str(uuid4()),
                definition_id=definition.id,
                definition_key=definition.key,
                definition_version=definition.version,
                business_key=business_key,
                tenant_id=tenant_id,
                state=InstanceState.ACTIVE,
                start_time=datetime.utcnow(),
                variables=variables or {},
            )
        self._instance_manager.add_instance(instance)
        await self._instance_manager.persist_instance(instance.id)
        await self._state_manager.set_persisted(
            instance.id,
            instance.state.value,
            data={
                "definition_id": instance.definition_id,
                "definition_key": instance.definition_key,
                "business_key": instance.business_key,
                "variables": dict(instance.variables),
            },
        )
        if variables:
            for name, value in variables.items():
                await self._variable_manager.set_persisted(instance.id, instance.id, name, value)
        await self._event_bus.publish(
            Event(
                type=EventType.PROCESS_INSTANCE_STARTED,
                data={"instance_id": instance.id, "definition_key": definition.key, "business_key": business_key},
            )
        )
        handler = self._engine_handlers.get(getattr(definition, "definition_type", "bpmn"))
        if handler:
            await handler.execute_instance(instance, definition)
        return instance

    async def delete_instance(self, instance_id: str, reason: str = "Deleted") -> None:
        await self._correlation_engine.cleanup_instance_subscriptions_persisted(instance_id)
        await self._instance_manager.persist_instance(instance_id)
        await self._state_manager.set_persisted(
            instance_id,
            InstanceState.TERMINATED.value,
            data={
                "delete_reason": reason,
                "variables": {},
            },
        )
        await self._event_bus.publish(
            Event(type=EventType.PROCESS_INSTANCE_TERMINATED, data={"instance_id": instance_id, "reason": reason})
        )

    async def update_instance_state(
        self,
        instance: ProcessInstance,
        new_state: InstanceState,
        *,
        reason: str | None = None,
    ) -> ProcessInstance:
        _TRANSITIONS: dict[InstanceState, tuple[str, EventType]] = {
            InstanceState.SUSPENDED: ("suspend", EventType.PROCESS_INSTANCE_SUSPENDED),
            InstanceState.ACTIVE: ("resume", EventType.PROCESS_INSTANCE_RESUMED),
            InstanceState.COMPLETED: ("complete", EventType.PROCESS_INSTANCE_COMPLETED),
            InstanceState.TERMINATED: ("terminate", EventType.PROCESS_INSTANCE_TERMINATED),
            InstanceState.FAILED: ("fail", EventType.ERROR_THROWN),
        }

        entry = _TRANSITIONS.get(new_state)
        if entry is not None:
            method_name, event_type = entry
            method = getattr(instance, method_name)
            if method_name == "resume":
                if instance.state == InstanceState.SUSPENDED:
                    method()
            elif method_name in ("terminate", "fail"):
                method(reason or method_name.capitalize())
            else:
                method()
        else:
            instance.state = new_state
            event_type = EventType.CUSTOM

        await self._instance_manager.persist_instance(instance.id)
        await self._state_manager.set_persisted(
            instance.id,
            new_state.value,
            data={
                "definition_id": instance.definition_id,
                "definition_key": instance.definition_key,
                "business_key": instance.business_key,
                "delete_reason": getattr(instance, "delete_reason", None),
                "variables": dict(instance.variables) if hasattr(instance, "variables") else {},
            },
        )
        await self._event_bus.publish(
            Event(type=event_type, data={"instance_id": instance.id, "state": new_state.value, "reason": reason})
        )
        return instance


# ── Recovery ───────────────────────────────────────────────────


class RecoveryService:
    """Handles runtime state recovery on engine restart."""

    def __init__(
        self,
        instance_manager: InstanceManager,
        token_manager: TokenManager,
        variable_manager: _VariableManager,
        state_manager: _StateManager,
        event_bus: EventBus,
        correlation_engine: _CorrelationEngine,
        scheduler: Scheduler,
        definitions: dict[str, ProcessDefinition],
        definition_versions: dict[str, list[ProcessDefinition]],
        deployments: dict[str, Deployment],
    ) -> None:
        self._instance_manager = instance_manager
        self._token_manager = token_manager
        self._variable_manager = variable_manager
        self._state_manager = state_manager
        self._event_bus = event_bus
        self._correlation_engine = correlation_engine
        self._scheduler = scheduler
        self._definitions = definitions
        self._definition_versions = definition_versions
        self._deployments = deployments

    async def recover(self) -> RawData:
        instances = await self._instance_manager.load_all_instances()
        active = set()
        suspended = set()
        for instance in instances:
            if instance.state == InstanceState.ACTIVE:
                active.add(instance.id)
            elif instance.state == InstanceState.SUSPENDED:
                suspended.add(instance.id)
        await self._correlation_engine.reload_from_history()
        for instance in instances:
            await self._token_manager.load_instance_tokens(instance.id)
            await self._variable_manager.restore_persisted(instance.id)
            await self._scheduler.reload_tasks_from_history(instance.id)
        await self._event_bus.reload_history(limit=self._event_bus.max_history_size)
        return {"instances": len(instances), "active": len(active), "suspended": len(suspended)}


# ── Definition management ─────────────────────────────────────


class DefinitionService:
    """Handles definition parsing, detection, and serialization."""

    def __init__(
        self,
        definition_repository: _DefinitionRepository,
        definitions: dict[str, ProcessDefinition],
        definition_versions: dict[str, list[ProcessDefinition]],
    ) -> None:
        self._definition_repository = definition_repository
        self._definitions = definitions
        self._definition_versions = definition_versions

    async def parse(
        self,
        resource_name: str,
        content: str,
        deployment_id: str,
        tenant_id: str | None,
    ) -> ProcessDefinition:
        definition_type = self._detect_type(resource_name, content)
        key = self._extract_key(content, definition_type)
        version = self._calculate_next_version(key)
        return ProcessDefinition(
            id=str(uuid4()),
            key=key,
            name=self._extract_name(content, definition_type),
            version=version,
            deployment_id=deployment_id,
            resource_name=resource_name,
            diagram_resource_name=None,
            has_start_form_key=False,
            has_graphical_notation=True,
            is_suspended=False,
            tenant_id=tenant_id,
            version_tag=None,
            history_time_to_live=None,
            is_startable_in_tasklist=True,
            definition_type=definition_type,
            definition_xml=content,
            deployed_at=datetime.utcnow(),
        )

    def _detect_type(self, resource_name: str, content: str) -> str:
        lower_name = resource_name.lower()
        preview = content[:200].lower()
        if ".bam.json" in lower_name or ".bam.yaml" in lower_name or ".bam.yml" in lower_name:
            return "bam"
        if ".bpmn" in lower_name or "bpmn" in preview:
            return "bpmn"
        if ".cmmn" in lower_name or "cmmn" in preview:
            return "cmmn"
        if ".dmn" in lower_name or "dmn" in preview:
            return "dmn"
        if "statemachine" in lower_name:
            return "state_machine"
        if "cep" in lower_name:
            return "cep"
        if "agent" in lower_name:
            return "multi_agent"
        return "bpmn"

    def _extract_key(self, content: str, definition_type: str) -> str:
        import re
        if definition_type == "bpmn":
            match = re.search(r'id="([^"]+)"', content)
            if match:
                return match.group(1)
        return f"process_{uuid4().hex[:8]}"

    def _extract_name(self, content: str, definition_type: str) -> str:
        import re
        match = re.search(r'name="([^"]+)"', content)
        if match:
            return match.group(1)
        return "Unnamed Process"

    def _calculate_next_version(self, key: str) -> int:
        return len(self._definition_versions.get(key, [])) + 1

    def load_persisted(self) -> None:
        rows = self._definition_repository.list()
        self._definitions.clear()
        self._definition_versions.clear()
        for row in rows:
            definition = self._from_dict(row)
            self._definitions[definition.key] = definition
            self._definition_versions.setdefault(definition.key, []).append(definition)

    def to_dict(self, definition: _DefinitionLike) -> RawData:
        return {
            "id": definition.id,
            "key": definition.key,
            "name": definition.name,
            "version": definition.version,
            "deployment_id": definition.deployment_id,
            "resource_name": definition.resource_name,
            "diagram_resource_name": getattr(definition, "diagram_resource_name", None),
            "has_start_form_key": bool(getattr(definition, "has_start_form_key", False)),
            "has_graphical_notation": bool(getattr(definition, "has_graphical_notation", True)),
            "is_suspended": bool(getattr(definition, "is_suspended", False)),
            "tenant_id": getattr(definition, "tenant_id", None),
            "version_tag": getattr(definition, "version_tag", None),
            "history_time_to_live": getattr(definition, "history_time_to_live", None),
            "is_startable_in_tasklist": bool(getattr(definition, "is_startable_in_tasklist", True)),
            "definition_type": definition.definition_type,
            "definition_xml": definition.definition_xml,
            "deployed_at": definition.deployed_at.isoformat() if hasattr(definition.deployed_at, "isoformat") else str(definition.deployed_at),
            "metadata": dict(getattr(definition, "metadata", {})),
        }

    def _from_dict(self, payload: RawData) -> ProcessDefinition:
        return ProcessDefinition(
            id=str(payload["id"]),
            key=str(payload["key"]),
            name=str(payload.get("name", "Unnamed Process")),
            version=int(payload.get("version", 1)),
            deployment_id=str(payload.get("deployment_id", "")),
            resource_name=str(payload.get("resource_name", "")),
            diagram_resource_name=payload.get("diagram_resource_name"),
            has_start_form_key=bool(payload.get("has_start_form_key", False)),
            has_graphical_notation=bool(payload.get("has_graphical_notation", True)),
            is_suspended=bool(payload.get("is_suspended", False)),
            tenant_id=payload.get("tenant_id"),
            version_tag=payload.get("version_tag"),
            history_time_to_live=payload.get("history_time_to_live"),
            is_startable_in_tasklist=bool(payload.get("is_startable_in_tasklist", True)),
            definition_type=str(payload.get("definition_type", "bpmn")),
            definition_xml=str(payload.get("definition_xml", "")),
            deployed_at=_parse_datetime(payload.get("deployed_at")),
            metadata=dict(payload.get("metadata") or {}),
        )


# ── Deployment helpers ─────────────────────────────────────────


async def _delete_deployment_state(
    deployment_id: str,
    cascade: bool,
    deployments: dict[str, Deployment],
    definitions: dict[str, ProcessDefinition],
    definition_versions: dict[str, list[ProcessDefinition]],
    instances: dict[str, ProcessInstance],
    delete_instance_fn: Callable[[str, str], Any] | None = None,
) -> None:
    deployment = deployments.get(deployment_id)
    if not deployment:
        raise ValueError(f"Deployment not found: {deployment_id}")
    if cascade and delete_instance_fn:
        for definition in deployment.definitions:
            for inst_id, inst in list(instances.items()):
                if inst.definition_id == definition.id:
                    await delete_instance_fn(inst_id, "Deployment deleted")
    for definition in deployment.definitions:
        definitions.pop(definition.key, None)
        if definition.key in definition_versions:
            definition_versions[definition.key] = [
                item for item in definition_versions[definition.key] if item.id != definition.id
            ]
    del deployments[deployment_id]


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()
