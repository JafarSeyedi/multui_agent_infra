"""
Core Orchestration Engine

Main coordinator for orchestration lifecycle, deployment, recovery,
instance execution, and shared runtime persistence.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .correlation import CorrelationEngine
from .event_bus import Event, EventBus, EventType
from .instance import InstanceManager, InstanceState, ProcessInstance
from .scheduler import Scheduler
from .token import TokenManager
from .transaction import TransactionManager
from ..persistence import (
    DefinitionRepository,
    EventRepository,
    HistoryRepository,
    InstanceRepository,
    TokenRepository,
    VariableRepository,
)
from ..runtime import StateManager, VariableManager
from ..runtime.incident_manager import IncidentManager
from ..runtime.migration import ProcessInstanceMigrator, BatchOperationManager
from ..runtime.tenant import TenantManager
from ..runtime.circuit_breaker import CircuitBreakerRegistry, RetryHandler, RetryConfig
from ..runtime.external_task import ExternalTaskManager, ExternalTaskWorker
from ..runtime.listeners import TaskListenerManager, ExecutionListenerManager
from ..runtime.rate_limiter import RateLimiter
from ..runtime.state_snapshot import StateSnapshotManager, CheckpointConfig
from ..forms.form_engine import FormEngine
from ..monitoring.metrics_collector import MetricsCollector
from ..monitoring.process_heatmap import ProcessHeatmap, BottleneckDetection, KpiTracker
from ..persistence.audit_log import AuditLog
from ..validation.osdm_validator import (
    BpmnOsdmValidator,
    CmmnOsdmValidator,
    DmnOsdmValidator,
    StateMachineOsdmValidator,
)
from ..runtime.osdm_serializer import OsdmSerializer, OsdmDeserializer, SerializationContext


logger = logging.getLogger(__name__)


class EngineState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class DeploymentMode(Enum):
    REPLACE = "replace"
    VERSION = "version"
    PARALLEL = "parallel"


@dataclass
class EngineConfig:
    max_concurrent_instances: int = 1000
    enable_persistence: bool = True
    enable_monitoring: bool = True
    enable_clustering: bool = False
    job_executor_threads: int = 10
    async_executor_threads: int = 5
    history_level: str = "full"
    deployment_mode: DeploymentMode = DeploymentMode.VERSION
    enable_optimistic_locking: bool = True
    enable_metrics: bool = True
    metrics_interval_seconds: int = 60
    enable_bpmn: bool = True
    bpmn_validation: bool = True
    enable_cmmn: bool = True
    cmmn_validation: bool = True
    enable_dmn: bool = True
    dmn_validation: bool = True
    enable_state_machine: bool = True
    enable_cep: bool = True
    cep_buffer_size: int = 10000
    enable_multi_agent: bool = True
    agent_timeout_seconds: int = 300


@dataclass
class ProcessDefinition:
    id: str
    key: str
    name: str
    version: int
    deployment_id: str
    resource_name: str
    diagram_resource_name: Optional[str]
    has_start_form_key: bool
    has_graphical_notation: bool
    is_suspended: bool
    tenant_id: Optional[str]
    version_tag: Optional[str]
    history_time_to_live: Optional[int]
    is_startable_in_tasklist: bool
    definition_type: str
    definition_xml: str
    deployed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Deployment:
    id: str
    name: str
    deployment_time: datetime
    source: str
    tenant_id: Optional[str]
    definitions: List[ProcessDefinition] = field(default_factory=list)


class OrchestrationEngine:
    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        *,
        event_repository: EventRepository | None = None,
        instance_repository: InstanceRepository | None = None,
        history_repository: HistoryRepository | None = None,
        variable_repository: VariableRepository | None = None,
        token_repository: TokenRepository | None = None,
        definition_repository: DefinitionRepository | None = None,
    ) -> None:
        self.config = config or EngineConfig()
        self.state = EngineState.STOPPED
        self.engine_id = str(uuid4())

        self.event_repository = event_repository or EventRepository()
        self.instance_repository = instance_repository or InstanceRepository()
        self.history_repository = history_repository or HistoryRepository()
        self.variable_repository = variable_repository or VariableRepository()
        self.token_repository = token_repository or TokenRepository()
        self.definition_repository = definition_repository or DefinitionRepository()

        self.event_bus = EventBus(event_repository=self.event_repository)
        self.correlation_engine = CorrelationEngine(self.event_bus, history_repository=self.history_repository)
        self.transaction_manager = TransactionManager()
        self.scheduler = Scheduler(history_repository=self.history_repository)
        self.instance_manager = InstanceManager(repository=self.instance_repository)
        self.token_manager = TokenManager(repository=self.token_repository)
        self.variable_manager = VariableManager(repository=self.variable_repository)
        self.state_manager = StateManager()

        self.incident_manager = IncidentManager()
        self.tenant_manager = TenantManager()
        self.circuit_breaker_registry = CircuitBreakerRegistry()
        self.retry_handler = RetryHandler()
        self.external_task_manager = ExternalTaskManager()
        self.task_listener_manager = TaskListenerManager()
        self.execution_listener_manager = ExecutionListenerManager()
        self.rate_limiter = RateLimiter()
        self.snapshot_manager = StateSnapshotManager(
            config=CheckpointConfig(
                enabled=True,
                auto_checkpoint_interval_seconds=30,
                checkpoint_on_activity_start=True,
                checkpoint_on_activity_complete=True,
                checkpoint_on_error=True,
            )
        )
        self.form_engine = FormEngine()
        self.metrics_collector = MetricsCollector()
        self.process_heatmap = ProcessHeatmap()
        self.bottleneck_detector = BottleneckDetection()
        self.kpi_tracker = KpiTracker()
        self.audit_log = AuditLog()
        self.osdm_serializer = OsdmSerializer()
        self.osdm_deserializer = OsdmDeserializer()
        self.bpmn_validator = BpmnOsdmValidator()
        self.cmmn_validator = CmmnOsdmValidator()
        self.dmn_validator = DmnOsdmValidator()
        self.state_machine_validator = StateMachineOsdmValidator()

        self.migrator = ProcessInstanceMigrator(self)
        self.batch_manager = BatchOperationManager(self)

        self.deployments: Dict[str, Deployment] = {}
        self.definitions: Dict[str, ProcessDefinition] = {}
        self.definition_versions: Dict[str, List[ProcessDefinition]] = {}
        self.instances: Dict[str, ProcessInstance] = {}
        self.engine_handlers: Dict[str, Any] = {}
        self.active_instances: Set[str] = set()
        self.suspended_instances: Set[str] = set()
        self._executor_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        if self.state == EngineState.RUNNING:
            return
        self.state = EngineState.STARTING
        try:
            await self._recover_runtime_state()
            await self.event_bus.start()
            await self.scheduler.start()
            for i in range(self.config.job_executor_threads):
                self._executor_tasks.append(asyncio.create_task(self._job_executor_loop(i)))
            for i in range(self.config.async_executor_threads):
                self._executor_tasks.append(asyncio.create_task(self._async_executor_loop(i)))
            if self.config.enable_monitoring:
                self._executor_tasks.append(asyncio.create_task(self._monitoring_loop()))
            self.state = EngineState.RUNNING
            await self.event_bus.publish(
                Event(type=EventType.ENGINE_STARTED, data={"engine_id": self.engine_id, "timestamp": datetime.utcnow()})
            )
        except Exception:
            self.state = EngineState.ERROR
            logger.exception("Failed to start engine")
            raise

    async def stop(self) -> None:
        if self.state == EngineState.STOPPED:
            return
        self.state = EngineState.STOPPING
        self._shutdown_event.set()
        if self._executor_tasks:
            await asyncio.gather(*self._executor_tasks, return_exceptions=True)
            self._executor_tasks.clear()
        await self.scheduler.stop()
        await self.event_bus.stop()
        self.state = EngineState.STOPPED

    async def pause(self) -> None:
        if self.state != EngineState.RUNNING:
            raise RuntimeError(f"Cannot pause engine in state: {self.state}")
        self.state = EngineState.PAUSED
        await self.scheduler.pause()

    async def resume(self) -> None:
        if self.state != EngineState.PAUSED:
            raise RuntimeError(f"Cannot resume engine in state: {self.state}")
        self.state = EngineState.RUNNING
        await self.scheduler.resume()

    def register_engine_handler(self, definition_type: str, handler: Any) -> None:
        self.engine_handlers[definition_type] = handler

    async def deploy(
        self,
        name: str,
        resources: Dict[str, str],
        source: str = "api",
        tenant_id: Optional[str] = None,
    ) -> Deployment:
        deployment_id = str(uuid4())
        deployment = Deployment(
            id=deployment_id,
            name=name,
            deployment_time=datetime.utcnow(),
            source=source,
            tenant_id=tenant_id,
        )
        for resource_name, content in resources.items():
            definition = await self._parse_definition(resource_name, content, deployment_id, tenant_id)
            deployment.definitions.append(definition)
            self.definitions[definition.key] = definition
            self.definition_versions.setdefault(definition.key, []).append(definition)
            self.definition_repository.save(definition.id, self._definition_to_dict(definition))
        self.deployments[deployment_id] = deployment
        await self.event_bus.publish(
            Event(type=EventType.DEPLOYMENT_CREATED, data={"deployment_id": deployment_id, "name": name})
        )
        return deployment

    async def start_process_instance(
        self,
        process_definition_key: str,
        business_key: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> ProcessInstance:
        definition = self.definitions.get(process_definition_key)
        if not definition:
            raise ValueError(f"Process definition not found: {process_definition_key}")
        if definition.is_suspended:
            raise RuntimeError(f"Process definition is suspended: {process_definition_key}")

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
        self.instances[instance.id] = instance
        self.instance_manager.add_instance(instance)
        self.active_instances.add(instance.id)
        await self.instance_manager.persist_instance(instance.id)
        await self.state_manager.set_persisted(
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
                await self.variable_manager.set_persisted(instance.id, instance.id, name, value)
        await self.event_bus.publish(
            Event(
                type=EventType.PROCESS_INSTANCE_STARTED,
                data={"instance_id": instance.id, "definition_key": definition.key, "business_key": business_key},
            )
        )
        handler = self.engine_handlers.get(definition.definition_type)
        if handler:
            await handler.execute_instance(instance, definition)
        return instance

    async def delete_instance(self, instance_id: str, reason: str = "Deleted") -> None:
        instance = self.instances.get(instance_id)
        if not instance:
            raise ValueError(f"Instance not found: {instance_id}")
        instance.terminate(reason)
        self.active_instances.discard(instance_id)
        self.suspended_instances.discard(instance_id)
        await self.correlation_engine.cleanup_instance_subscriptions_persisted(instance_id)
        await self._persist_instance_state(instance)
        await self.event_bus.publish(
            Event(type=EventType.PROCESS_INSTANCE_TERMINATED, data={"instance_id": instance_id, "reason": reason})
        )

    async def update_instance_state(
        self,
        instance_id: str,
        new_state: InstanceState,
        *,
        reason: str | None = None,
    ) -> ProcessInstance:
        instance = self.instances.get(instance_id)
        if instance is None:
            raise ValueError(f"Instance not found: {instance_id}")
        if new_state == InstanceState.SUSPENDED:
            instance.suspend()
            self.active_instances.discard(instance_id)
            self.suspended_instances.add(instance_id)
            event_type = EventType.PROCESS_INSTANCE_SUSPENDED
        elif new_state == InstanceState.ACTIVE:
            if instance.state == InstanceState.SUSPENDED:
                instance.resume()
            self.suspended_instances.discard(instance_id)
            self.active_instances.add(instance_id)
            event_type = EventType.PROCESS_INSTANCE_RESUMED
        elif new_state == InstanceState.COMPLETED:
            instance.complete()
            self.active_instances.discard(instance_id)
            self.suspended_instances.discard(instance_id)
            event_type = EventType.PROCESS_INSTANCE_COMPLETED
        elif new_state == InstanceState.TERMINATED:
            instance.terminate(reason or "Terminated")
            self.active_instances.discard(instance_id)
            self.suspended_instances.discard(instance_id)
            event_type = EventType.PROCESS_INSTANCE_TERMINATED
        elif new_state == InstanceState.FAILED:
            instance.fail(reason or "Failed")
            self.active_instances.discard(instance_id)
            self.suspended_instances.discard(instance_id)
            event_type = EventType.ERROR_THROWN
        else:
            instance.state = new_state
            event_type = EventType.CUSTOM
        await self._persist_instance_state(instance)
        await self.event_bus.publish(
            Event(type=event_type, data={"instance_id": instance.id, "state": instance.state.value, "reason": reason})
        )
        return instance

    async def _recover_runtime_state(self) -> None:
        self._load_persisted_definitions()
        instances = await self.instance_manager.load_all_instances()
        self.instances = {instance.id: instance for instance in instances}
        self.active_instances = {instance.id for instance in instances if instance.state == InstanceState.ACTIVE}
        self.suspended_instances = {instance.id for instance in instances if instance.state == InstanceState.SUSPENDED}
        await self.correlation_engine.reload_from_history()
        for instance in instances:
            await self.token_manager.load_instance_tokens(instance.id)
            await self.variable_manager.restore_persisted(instance.id)
            await self.scheduler.reload_tasks_from_history(instance.id)
        await self.event_bus.reload_history(limit=self.event_bus.max_history_size)

    async def _persist_instance_state(self, instance: ProcessInstance) -> None:
        await self.instance_manager.persist_instance(instance.id)
        await self.state_manager.set_persisted(
            instance.id,
            instance.state.value,
            data={
                "definition_id": instance.definition_id,
                "definition_key": instance.definition_key,
                "business_key": instance.business_key,
                "delete_reason": instance.delete_reason,
                "variables": dict(instance.variables),
            },
        )

    def _load_persisted_definitions(self) -> None:
        rows = self.definition_repository.list()
        self.definitions.clear()
        self.definition_versions.clear()
        self.deployments.clear()
        for row in rows:
            definition = self._definition_from_dict(row)
            self.definitions[definition.key] = definition
            self.definition_versions.setdefault(definition.key, []).append(definition)
            deployment = self.deployments.setdefault(
                definition.deployment_id,
                Deployment(
                    id=definition.deployment_id,
                    name=str(row.get("deployment_name") or definition.deployment_id),
                    deployment_time=_parse_datetime(row.get("deployed_at")),
                    source=str(row.get("deployment_source") or "recovered"),
                    tenant_id=definition.tenant_id,
                    definitions=[],
                ),
            )
            deployment.definitions.append(definition)

    async def _parse_definition(
        self,
        resource_name: str,
        content: str,
        deployment_id: str,
        tenant_id: Optional[str],
    ) -> ProcessDefinition:
        definition_type = self._detect_definition_type(resource_name, content)
        key = self._extract_definition_key(content, definition_type)
        version = self._calculate_next_version(key)
        return ProcessDefinition(
            id=str(uuid4()),
            key=key,
            name=self._extract_definition_name(content, definition_type),
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

    def _detect_definition_type(self, resource_name: str, content: str) -> str:
        lower_name = resource_name.lower()
        preview = content[:200].lower()
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

    def _extract_definition_key(self, content: str, definition_type: str) -> str:
        import re

        if definition_type == "bpmn":
            match = re.search(r'id="([^"]+)"', content)
            if match:
                return match.group(1)
        return f"process_{uuid4().hex[:8]}"

    def _extract_definition_name(self, content: str, definition_type: str) -> str:
        import re

        match = re.search(r'name="([^"]+)"', content)
        if match:
            return match.group(1)
        return "Unnamed Process"

    def _calculate_next_version(self, key: str) -> int:
        return len(self.definition_versions.get(key, [])) + 1

    async def _job_executor_loop(self, executor_id: int) -> None:
        logger.info("Job executor %s started", executor_id)
        while not self._shutdown_event.is_set():
            try:
                if self.state == EngineState.RUNNING:
                    await self.scheduler.process_due_jobs()
                await asyncio.sleep(1)
            except Exception:
                logger.exception("Error in job executor %s", executor_id)
        logger.info("Job executor %s stopped", executor_id)

    async def _async_executor_loop(self, executor_id: int) -> None:
        logger.info("Async executor %s started", executor_id)
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(0.5)
            except Exception:
                logger.exception("Error in async executor %s", executor_id)
        logger.info("Async executor %s stopped", executor_id)

    async def _monitoring_loop(self) -> None:
        logger.info("Monitoring loop started")
        while not self._shutdown_event.is_set():
            try:
                if self.state == EngineState.RUNNING and self.config.enable_metrics:
                    await self.event_bus.publish(
                        Event(
                            type=EventType.METRICS_COLLECTED,
                            data={
                                "active_instances": len(self.active_instances),
                                "suspended_instances": len(self.suspended_instances),
                                "total_definitions": len(self.definitions),
                                "total_deployments": len(self.deployments),
                            },
                        )
                    )
                await asyncio.sleep(self.config.metrics_interval_seconds)
            except Exception:
                logger.exception("Error in monitoring loop")
        logger.info("Monitoring loop stopped")

    def get_instance(self, instance_id: str) -> Optional[ProcessInstance]:
        return self.instances.get(instance_id)

    def get_definition(self, key: str, version: Optional[int] = None) -> Optional[ProcessDefinition]:
        if version is None:
            return self.definitions.get(key)
        for definition in self.definition_versions.get(key, []):
            if definition.version == version:
                return definition
        return None

    async def delete_deployment(self, deployment_id: str, cascade: bool = False) -> None:
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            raise ValueError(f"Deployment not found: {deployment_id}")
        if cascade:
            for definition in deployment.definitions:
                for inst_id, inst in list(self.instances.items()):
                    if inst.definition_id == definition.id:
                        await self.delete_instance(inst_id, "Deployment deleted")
        for definition in deployment.definitions:
            self.definitions.pop(definition.key, None)
            if definition.key in self.definition_versions:
                self.definition_versions[definition.key] = [
                    item for item in self.definition_versions[definition.key] if item.id != definition.id
                ]
        del self.deployments[deployment_id]

    def _definition_to_dict(self, definition: ProcessDefinition) -> dict[str, Any]:
        return {
            "id": definition.id,
            "key": definition.key,
            "name": definition.name,
            "version": definition.version,
            "deployment_id": definition.deployment_id,
            "resource_name": definition.resource_name,
            "diagram_resource_name": definition.diagram_resource_name,
            "has_start_form_key": definition.has_start_form_key,
            "has_graphical_notation": definition.has_graphical_notation,
            "is_suspended": definition.is_suspended,
            "tenant_id": definition.tenant_id,
            "version_tag": definition.version_tag,
            "history_time_to_live": definition.history_time_to_live,
            "is_startable_in_tasklist": definition.is_startable_in_tasklist,
            "definition_type": definition.definition_type,
            "definition_xml": definition.definition_xml,
            "deployed_at": definition.deployed_at.isoformat(),
            "metadata": dict(definition.metadata),
        }

    def _definition_from_dict(self, payload: dict[str, Any]) -> ProcessDefinition:
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


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()
