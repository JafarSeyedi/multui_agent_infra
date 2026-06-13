"""
Core Orchestration Engine

Main coordinator for orchestration lifecycle, deployment, recovery,
instance execution, and shared runtime persistence.

Refactored to delegate to focused services for separation of concerns.
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
from .engine_services import (
    EngineLifecycleService,
    InstanceService,
    RecoveryService,
    DefinitionService,
)
from .engine_states import (
    EngineState as EngineStateABC,
    ErrorState,
    RunningState,
    StoppedState,
)

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
    enable_bam: bool = True
    bam_metric_buffer_size: int = 100000
    bam_persistence_interval: int = 60
    bam_enable_predictive: bool = True


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
    """Orchestration engine that delegates to focused services.

    This class acts as a facade — it composes specialized services
    for lifecycle, deployment, instance, recovery, and definition
    management while exposing the same public API.
    """

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
        self.engine_id = str(uuid4())
        self._lifecycle_state: EngineStateABC = StoppedState()

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

        self.engine_handlers: Dict[str, Any] = {}

        self._bam_engine: Any | None = None
        if self.config.enable_bam:
            from ..bam.engine import BamEngine
            self._bam_engine = BamEngine(engine=self)
            self.register_engine_handler("bam", self._bam_engine)

        self.deployments: Dict[str, Deployment] = {}
        self.definitions: Dict[str, ProcessDefinition] = {}
        self.definition_versions: Dict[str, List[ProcessDefinition]] = {}
        self.instances: Dict[str, ProcessInstance] = {}
        self.active_instances: Set[str] = set()
        self.suspended_instances: Set[str] = set()
        self._executor_tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()

        # Focused services
        self._definition_service = DefinitionService(
            definition_repository=self.definition_repository,
            definitions=self.definitions,
            definition_versions=self.definition_versions,
        )
        self._instance_service = InstanceService(
            instance_manager=self.instance_manager,
            token_manager=self.token_manager,
            variable_manager=self.variable_manager,
            state_manager=self.state_manager,
            event_bus=self.event_bus,
            correlation_engine=self.correlation_engine,
            engine_handlers=self.engine_handlers,
            scheduler=self.scheduler,
        )
        self._recovery_service = RecoveryService(
            instance_manager=self.instance_manager,
            token_manager=self.token_manager,
            variable_manager=self.variable_manager,
            state_manager=self.state_manager,
            event_bus=self.event_bus,
            correlation_engine=self.correlation_engine,
            scheduler=self.scheduler,
            definitions=self.definitions,
            definition_versions=self.definition_versions,
            deployments=self.deployments,
        )
        self._lifecycle_service = EngineLifecycleService(
            event_bus=self.event_bus,
            scheduler=self.scheduler,
            event_type=EventType,
            recovery_service=self._recovery_service,
            bam_engine=self._bam_engine,
            config=self.config,
        )

    # ── Lifecycle ──────────────────────────────────────────────────

    @property
    def state(self) -> str:
        return self._lifecycle_state.name

    async def start(self) -> None:
        await self._lifecycle_state.start(self)
        if self._lifecycle_state.name == "starting":
            try:
                await self._lifecycle_service.start()
                self._lifecycle_state = RunningState()
                await self.event_bus.publish(
                    Event(type=EventType.ENGINE_STARTED, data={})
                )
            except Exception:
                self._lifecycle_state = ErrorState()
                logger.exception("Failed to start engine")
                raise

    async def stop(self) -> None:
        await self._lifecycle_state.stop(self)
        if self._lifecycle_state.name == "stopping":
            self._shutdown_event.set()
            if self._executor_tasks:
                await asyncio.gather(*self._executor_tasks, return_exceptions=True)
                self._executor_tasks.clear()
            await self.scheduler.stop()
            if self._bam_engine:
                await self._bam_engine.stop()
            await self.event_bus.publish(
                Event(type=EventType.ENGINE_STOPPED, data={})
            )
            await self.event_bus.stop()
            self._lifecycle_state = StoppedState()

    async def pause(self) -> None:
        current = self._lifecycle_state.name
        await self._lifecycle_state.pause(self)
        if self._lifecycle_state.name == "paused":
            await self.scheduler.pause()
            await self.event_bus.publish(
                Event(type=EventType.ENGINE_PAUSED, data={})
            )
        elif self._lifecycle_state.name != current:
            pass

    async def resume(self) -> None:
        current = self._lifecycle_state.name
        await self._lifecycle_state.resume(self)
        if self._lifecycle_state.name == "running" and current == "paused":
            await self.scheduler.resume()
            await self.event_bus.publish(
                Event(type=EventType.ENGINE_RESUMED, data={})
            )

    def register_engine_handler(self, definition_type: str, handler: Any) -> None:
        self.engine_handlers[definition_type] = handler

    # ── Deployment ─────────────────────────────────────────────────

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

    async def delete_deployment(self, deployment_id: str, cascade: bool = False) -> None:
        from .engine_services import _delete_deployment_state
        await _delete_deployment_state(
            deployment_id=deployment_id,
            cascade=cascade,
            deployments=self.deployments,
            definitions=self.definitions,
            definition_versions=self.definition_versions,
            instances=self.instances,
            delete_instance_fn=self._delete_instance_internal,
        )

    async def _delete_instance_internal(self, instance_id: str, reason: str) -> None:
        await self._instance_service.delete_instance(instance_id, reason)

    # ── Instance management ────────────────────────────────────────

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
        self.active_instances.add(instance.id)

        await self._instance_service.start_instance(
            definition, business_key, variables, tenant_id,
            instance=instance,
            persist_fn=self._persist_instance_state,
        )
        return instance

    async def delete_instance(self, instance_id: str, reason: str = "Deleted") -> None:
        await self._instance_service.delete_instance(instance_id, reason)

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
        result = await self._instance_service.update_instance_state(instance, new_state, reason=reason)
        if new_state == InstanceState.SUSPENDED:
            self.active_instances.discard(instance_id)
            self.suspended_instances.add(instance_id)
        elif new_state == InstanceState.ACTIVE:
            self.suspended_instances.discard(instance_id)
            self.active_instances.add(instance_id)
        else:
            self.active_instances.discard(instance_id)
            self.suspended_instances.discard(instance_id)
        return result

    def get_instance(self, instance_id: str) -> Optional[ProcessInstance]:
        return self.instances.get(instance_id)

    # ── Definition lookup ──────────────────────────────────────────

    def get_definition(self, key: str, version: Optional[int] = None) -> Optional[ProcessDefinition]:
        if version is None:
            return self.definitions.get(key)
        for definition in self.definition_versions.get(key, []):
            if definition.version == version:
                return definition
        return None

    # ── Recovery ───────────────────────────────────────────────────

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
        self._definition_service.load_persisted()

    async def _parse_definition(
        self,
        resource_name: str,
        content: str,
        deployment_id: str,
        tenant_id: Optional[str],
    ) -> ProcessDefinition:
        return await self._definition_service.parse(resource_name, content, deployment_id, tenant_id)

    def _detect_definition_type(self, resource_name: str, content: str) -> str:
        return self._definition_service._detect_type(resource_name, content)

    def _extract_definition_key(self, content: str, definition_type: str) -> str:
        return self._definition_service._extract_key(content, definition_type)

    def _extract_definition_name(self, content: str, definition_type: str) -> str:
        return self._definition_service._extract_name(content, definition_type)

    def _calculate_next_version(self, key: str) -> int:
        return self._definition_service._calculate_next_version(key)

    # ── Executor loops ─────────────────────────────────────────────

    async def _job_executor_loop(self, executor_id: int) -> None:
        logger.info("Job executor %s started", executor_id)
        while not self._shutdown_event.is_set():
            try:
                if self.state == "running":
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
                if self.state == "running" and self.config.enable_metrics:
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

    # ── Serialization ──────────────────────────────────────────────

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
