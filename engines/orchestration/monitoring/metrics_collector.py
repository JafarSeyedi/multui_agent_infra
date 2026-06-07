"""Metrics collection for orchestration runtime.

Collects process, activity, and instance metrics per Camunda Optimize/
Flowable Control/CIB ins7ght patterns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class HealthCheckType(str, Enum):
    ENGINE = "engine"
    SCHEDULER = "scheduler"
    PERSISTENCE = "persistence"
    CORRELATION = "correlation"
    JOB_EXECUTOR = "job_executor"
    EXTERNAL_TASKS = "external_tasks"
    CONNECTORS = "connectors"


@dataclass
class HealthStatus:
    component: str = ""
    component_type: str = ""
    status: str = "healthy"
    message: str = ""
    response_time_ms: float = 0.0
    last_checked: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthCheck:
    check_id: str = ""
    check_type: str = ""
    status: str = "healthy"
    component: str = ""
    message: str = ""
    response_time_ms: float = 0.0
    last_checked: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActivityMetrics:
    activity_id: str = ""
    activity_name: str | None = None
    activity_type: str = ""
    execution_count: int = 0
    average_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    failure_count: int = 0
    failure_rate: float = 0.0

    def record_execution(self, duration_ms: float, success: bool = True) -> None:
        self.execution_count += 1
        if self.execution_count == 1:
            self.average_duration_ms = duration_ms
            self.min_duration_ms = duration_ms
            self.max_duration_ms = duration_ms
        else:
            total = self.average_duration_ms * (self.execution_count - 1) + duration_ms
            self.average_duration_ms = total / self.execution_count
            self.min_duration_ms = min(self.min_duration_ms, duration_ms)
            self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        if not success:
            self.failure_count += 1
        if self.execution_count > 0:
            self.failure_rate = self.failure_count / self.execution_count


@dataclass
class ProcessMetrics:
    definition_key: str = ""
    definition_name: str | None = None
    definition_version: int = 0
    total_instances: int = 0
    active_instances: int = 0
    completed_instances: int = 0
    failed_instances: int = 0
    terminated_instances: int = 0
    suspended_instances: int = 0
    average_completion_time_ms: float = 0.0
    activity_metrics: dict[str, ActivityMetrics] = field(default_factory=dict)

    def record_instance_completion(self, duration_ms: float) -> None:
        self.completed_instances += 1
        self.active_instances = max(0, self.active_instances - 1)
        n = self.completed_instances
        self.average_completion_time_ms = (
            (self.average_completion_time_ms * (n - 1) + duration_ms) / n
        )

    def record_instance_failure(self) -> None:
        self.failed_instances += 1
        self.active_instances = max(0, self.active_instances - 1)

    def record_instance_termination(self) -> None:
        self.terminated_instances += 1
        self.active_instances = max(0, self.active_instances - 1)

    def record_activity_execution(self, activity_id: str, activity_name: str | None, activity_type: str, duration_ms: float, success: bool = True) -> None:
        if activity_id not in self.activity_metrics:
            self.activity_metrics[activity_id] = ActivityMetrics(
                activity_id=activity_id,
                activity_name=activity_name,
                activity_type=activity_type,
            )
        self.activity_metrics[activity_id].record_execution(duration_ms, success)


@dataclass
class InstanceMetrics:
    instance_id: str = ""
    definition_key: str = ""
    state: str = ""
    current_activity_id: str | None = None
    duration_ms: float = 0.0
    activity_count: int = 0
    completed_activity_count: int = 0
    failed_activity_count: int = 0
    variables_count: int = 0
    incidents_count: int = 0


class MetricsCollector:
    """Collects and aggregates runtime metrics."""

    def __init__(self) -> None:
        self._process_metrics: dict[str, ProcessMetrics] = {}
        self._instance_metrics: dict[str, InstanceMetrics] = {}
        self._health_checks: dict[str, HealthCheck] = {}
        self._start_time = time.time()

    def record_instance_start(self, instance_id: str, definition_key: str, variable_count: int = 0) -> None:
        self._instance_metrics[instance_id] = InstanceMetrics(
            instance_id=instance_id,
            definition_key=definition_key,
            state="active",
            variables_count=variable_count,
        )
        pm = self._get_or_create_process_metrics(definition_key)
        pm.total_instances += 1
        pm.active_instances += 1

    def record_instance_completion(self, instance_id: str, definition_key: str, duration_ms: float) -> None:
        im = self._instance_metrics.get(instance_id)
        if im:
            im.state = "completed"
            im.duration_ms = duration_ms
        pm = self._process_metrics.get(definition_key)
        if pm:
            pm.record_instance_completion(duration_ms)

    def record_instance_failure(self, instance_id: str, definition_key: str) -> None:
        im = self._instance_metrics.get(instance_id)
        if im:
            im.state = "failed"
        pm = self._process_metrics.get(definition_key)
        if pm:
            pm.record_instance_failure()

    def record_instance_termination(self, instance_id: str, definition_key: str) -> None:
        im = self._instance_metrics.get(instance_id)
        if im:
            im.state = "terminated"
        pm = self._process_metrics.get(definition_key)
        if pm:
            pm.record_instance_termination()

    def record_activity_execution(
        self,
        instance_id: str,
        definition_key: str,
        activity_id: str,
        activity_name: str | None,
        activity_type: str,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        im = self._instance_metrics.get(instance_id)
        if im:
            im.activity_count += 1
            im.current_activity_id = activity_id
            if success:
                im.completed_activity_count += 1
            else:
                im.failed_activity_count += 1
        pm = self._process_metrics.get(definition_key)
        if pm:
            pm.record_activity_execution(activity_id, activity_name, activity_type, duration_ms, success)

    def record_incident(self, instance_id: str) -> None:
        im = self._instance_metrics.get(instance_id)
        if im:
            im.incidents_count += 1

    def record_health_check(self, check: HealthCheck) -> None:
        key = f"{check.check_type}:{check.component}"
        self._health_checks[key] = check

    def get_process_metrics(self, definition_key: str) -> ProcessMetrics | None:
        return self._process_metrics.get(definition_key)

    def get_all_process_metrics(self) -> list[ProcessMetrics]:
        return list(self._process_metrics.values())

    def get_instance_metrics(self, instance_id: str) -> InstanceMetrics | None:
        return self._instance_metrics.get(instance_id)

    def get_health_status(self) -> dict[str, HealthCheck]:
        return dict(self._health_checks)

    def get_overall_health(self) -> str:
        checks = list(self._health_checks.values())
        if not checks:
            return "unknown"
        if all(c.status == "healthy" for c in checks):
            return "healthy"
        if any(c.status == "unhealthy" for c in checks):
            return "unhealthy"
        return "degraded"

    def get_summary(self) -> dict[str, Any]:
        total_instances = sum(pm.total_instances for pm in self._process_metrics.values())
        active_instances = sum(pm.active_instances for pm in self._process_metrics.values())
        completed_instances = sum(pm.completed_instances for pm in self._process_metrics.values())
        failed_instances = sum(pm.failed_instances for pm in self._process_metrics.values())
        return {
            "uptime_seconds": time.time() - self._start_time,
            "total_definitions": len(self._process_metrics),
            "total_instances": total_instances,
            "active_instances": active_instances,
            "completed_instances": completed_instances,
            "failed_instances": failed_instances,
            "health": self.get_overall_health(),
        }

    def observe(self, name: str, value: float) -> None:
        self._observations: dict[str, list[float]] = getattr(self, '_observations', {})
        if name not in self._observations:
            self._observations[name] = []
        self._observations[name].append(value)

    def snapshot(self) -> dict[str, object]:
        obs = getattr(self, '_observations', {})
        return {
            name: {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0.0,
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0,
            }
            for name, values in obs.items()
        }

    def _get_or_create_process_metrics(self, definition_key: str) -> ProcessMetrics:
        if definition_key not in self._process_metrics:
            self._process_metrics[definition_key] = ProcessMetrics(definition_key=definition_key)
        return self._process_metrics[definition_key]
