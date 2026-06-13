"""Builder pattern implementations for engine configuration.

Separates construction of complex objects from their representation,
enabling step-wise configuration with sensible defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4


@dataclass
class EngineConfig:
    """Immutable engine configuration produced by EngineConfigBuilder."""

    engine_id: str = ""
    engine_name: str = "orchestration-engine"
    max_concurrent_instances: int = 100
    instance_timeout: timedelta = timedelta(hours=1)
    poll_interval: timedelta = timedelta(seconds=5)
    enable_monitoring: bool = True
    monitoring_interval: timedelta = timedelta(seconds=30)
    enable_persistence: bool = True
    enable_recovery: bool = True
    storage_backend: str = "memory"
    event_history_size: int = 10000
    scheduler_pool_size: int = 4
    executor_pool_size: int = 8
    retry_max_attempts: int = 3
    retry_base_delay: float = 0.5
    definitions_path: str = "definitions"
    tenant_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def merge(self, **kwargs: Any) -> EngineConfig:
        for key, value in kwargs.items():
            if hasattr(self, key):
                object.__setattr__(self, key, value)
            else:
                self.extra[key] = value
        return self


class EngineConfigBuilder:
    """Step-wise builder for EngineConfig."""

    def __init__(self) -> None:
        self._config = EngineConfig()

    def with_engine_id(self, engine_id: str) -> EngineConfigBuilder:
        self._config.engine_id = engine_id
        return self

    def with_engine_name(self, name: str) -> EngineConfigBuilder:
        self._config.engine_name = name
        return self

    def with_max_concurrent_instances(self, limit: int) -> EngineConfigBuilder:
        self._config.max_concurrent_instances = limit
        return self

    def with_instance_timeout(self, timeout: timedelta) -> EngineConfigBuilder:
        self._config.instance_timeout = timeout
        return self

    def with_poll_interval(self, interval: timedelta) -> EngineConfigBuilder:
        self._config.poll_interval = interval
        return self

    def with_monitoring(self, enabled: bool, interval: timedelta | None = None) -> EngineConfigBuilder:
        self._config.enable_monitoring = enabled
        if interval is not None:
            self._config.monitoring_interval = interval
        return self

    def with_persistence(self, enabled: bool, backend: str = "memory") -> EngineConfigBuilder:
        self._config.enable_persistence = enabled
        self._config.storage_backend = backend
        return self

    def with_recovery(self, enabled: bool) -> EngineConfigBuilder:
        self._config.enable_recovery = enabled
        return self

    def with_event_history(self, size: int) -> EngineConfigBuilder:
        self._config.event_history_size = size
        return self

    def with_pool_sizes(self, scheduler: int = 4, executor: int = 8) -> EngineConfigBuilder:
        self._config.scheduler_pool_size = scheduler
        self._config.executor_pool_size = executor
        return self

    def with_retry(self, max_attempts: int = 3, base_delay: float = 0.5) -> EngineConfigBuilder:
        self._config.retry_max_attempts = max_attempts
        self._config.retry_base_delay = base_delay
        return self

    def with_definitions_path(self, path: str) -> EngineConfigBuilder:
        self._config.definitions_path = path
        return self

    def with_tenant(self, tenant_id: str) -> EngineConfigBuilder:
        self._config.tenant_id = tenant_id
        return self

    def with_extra(self, **kwargs: Any) -> EngineConfigBuilder:
        self._config.extra.update(kwargs)
        return self

    def build(self) -> EngineConfig:
        if not self._config.engine_id:
            self._config.engine_id = str(uuid4())
        return self._config


class ProcessDefinitionBuilder:
    """Step-wise builder for process definitions."""

    def __init__(self, key: str, name: str | None = None) -> None:
        from .engine import ProcessDefinition
        self._def = ProcessDefinition(
            id=str(uuid4()),
            key=key,
            name=name or key,
            version=1,
            deployment_id="",
            resource_name="",
            diagram_resource_name=None,
            has_start_form_key=False,
            has_graphical_notation=False,
            is_suspended=False,
            tenant_id=None,
            version_tag=None,
            history_time_to_live=None,
            is_startable_in_tasklist=False,
            definition_type="bpmn",
            definition_xml="",
            deployed_at=datetime.now(),
        )

    def with_id(self, id: str) -> ProcessDefinitionBuilder:
        self._def.id = id
        return self

    def with_version(self, version: int) -> ProcessDefinitionBuilder:
        self._def.version = version
        return self

    def with_deployment(self, deployment_id: str) -> ProcessDefinitionBuilder:
        self._def.deployment_id = deployment_id
        return self

    def with_resource(self, resource_name: str) -> ProcessDefinitionBuilder:
        self._def.resource_name = resource_name
        return self

    def with_type(self, definition_type: str) -> ProcessDefinitionBuilder:
        self._def.definition_type = definition_type
        return self

    def with_xml(self, xml: str) -> ProcessDefinitionBuilder:
        self._def.definition_xml = xml
        return self

    def with_metadata(self, **metadata: Any) -> ProcessDefinitionBuilder:
        self._def.metadata = metadata
        return self

    def build(self) -> Any:
        from .engine import ProcessDefinition
        return self._def
