"""Incident management for orchestration runtime.

Handles incident creation, retry with exponential backoff, dead letter queue,
and incident resolution per Camunda/Flowable patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional
from uuid import uuid4

from ...core.instance import InstanceState


logger = logging.getLogger(__name__)


class IncidentType(str, Enum):
    JOB_EXECUTION_FAILED = "job_execution_failed"
    EXTERNAL_TASK_FAILED = "external_task_failed"
    CONDITION_EVALUATION_FAILED = "condition_evaluation_failed"
    TIMER_PROCESSING_FAILED = "timer_processing_failed"
    PROCESS_EXECUTION_FAILED = "process_execution_failed"
    MIGRATION_FAILED = "migration_failed"
    CONNECTOR_INVOCATION_FAILED = "connector_invocation_failed"
    RETRY_EXHAUSTED = "retry_exhausted"
    TIMEOUT = "timeout"


class IncidentState(str, Enum):
    OPEN = "open"
    RETRYING = "retrying"
    RESOLVED = "resolved"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


@dataclass
class RetryPolicy:
    max_retries: int = 3
    initial_delay_ms: int = 1000
    backoff_multiplier: float = 2.0
    max_delay_ms: int = 60000
    jitter_factor: float = 0.1

    def get_delay(self, attempt: int) -> float:
        import random
        delay = self.initial_delay_ms * (self.backoff_multiplier ** attempt)
        delay = min(delay, self.max_delay_ms)
        jitter = delay * self.jitter_factor * (random.random() - 0.5)
        return max(0, (delay + jitter) / 1000.0)


@dataclass
class Incident:
    incident_id: str
    incident_type: str
    instance_id: str
    activity_id: str | None = None
    error_message: str = ""
    error_stack: str = ""
    state: str = IncidentState.OPEN
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""
    last_occurrence: str = ""
    resolved_at: str | None = None
    resolution: str | None = None
    job_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
            self.last_occurrence = self.created_at
        if not self.incident_id:
            self.incident_id = str(uuid4())


@dataclass
class IncidentQuery:
    instance_id: str | None = None
    incident_type: str | None = None
    state: str | None = None
    created_after: str | None = None
    created_before: str | None = None
    limit: int = 100
    offset: int = 0


class IncidentManager:
    def __init__(self, retry_policy: RetryPolicy | None = None) -> None:
        self._policy = retry_policy or RetryPolicy()
        self._incidents: dict[str, Incident] = {}
        self._instance_incidents: dict[str, list[str]] = {}
        self._retry_callbacks: dict[str, Callable[..., Any]] = {}
        self._dead_letter_queue: list[str] = []

    def create_incident(
        self,
        incident_type: str,
        instance_id: str,
        error_message: str,
        activity_id: str | None = None,
        error_stack: str = "",
        max_retries: int | None = None,
        job_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Incident:
        incident = Incident(
            incident_id=str(uuid4()),
            incident_type=incident_type,
            instance_id=instance_id,
            activity_id=activity_id,
            error_message=error_message,
            error_stack=error_stack,
            state=IncidentState.OPEN,
            retry_count=0,
            max_retries=max_retries if max_retries is not None else self._policy.max_retries,
            job_id=job_id,
            metadata=metadata or {},
        )

        self._incidents[incident.incident_id] = incident
        if instance_id not in self._instance_incidents:
            self._instance_incidents[instance_id] = []
        self._instance_incidents[instance_id].append(incident.incident_id)

        logger.warning("Incident created: %s (%s) for instance %s: %s",
                       incident.incident_id, incident_type, instance_id, error_message)
        return incident

    def resolve_incident(self, incident_id: str, resolution: str = "manual") -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return None
        incident.state = IncidentState.RESOLVED
        incident.resolved_at = datetime.utcnow().isoformat()
        incident.resolution = resolution
        logger.info("Incident resolved: %s (%s)", incident_id, resolution)
        return incident

    def cancel_incident(self, incident_id: str) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return None
        incident.state = IncidentState.CANCELLED
        incident.resolved_at = datetime.utcnow().isoformat()
        return incident

    def move_to_dead_letter(self, incident_id: str) -> Incident | None:
        incident = self._incidents.get(incident_id)
        if incident is None:
            return None
        incident.state = IncidentState.DEAD_LETTER
        self._dead_letter_queue.append(incident_id)
        logger.error("Incident moved to dead letter queue: %s", incident_id)
        return incident

    def get_incident(self, incident_id: str) -> Incident | None:
        return self._incidents.get(incident_id)

    def query_incidents(self, query: IncidentQuery) -> list[Incident]:
        results: list[Incident] = []
        for incident in self._incidents.values():
            if query.instance_id and incident.instance_id != query.instance_id:
                continue
            if query.incident_type and incident.incident_type != query.incident_type:
                continue
            if query.state and incident.state != query.state:
                continue
            if query.created_after and incident.created_at < query.created_after:
                continue
            if query.created_before and incident.created_at > query.created_before:
                continue
            results.append(incident)
        results.sort(key=lambda i: i.created_at, reverse=True)
        return results[query.offset:query.offset + query.limit]

    def get_open_incidents(self, instance_id: str | None = None) -> list[Incident]:
        query = IncidentQuery(state=IncidentState.OPEN, instance_id=instance_id, limit=10000)
        return self.query_incidents(query)

    def get_dead_letter_incidents(self) -> list[Incident]:
        return [self._incidents[iid] for iid in self._dead_letter_queue if iid in self._incidents]

    def clear_instance_incidents(self, instance_id: str) -> int:
        incident_ids = self._instance_incidents.pop(instance_id, [])
        count = 0
        for iid in incident_ids:
            if iid in self._incidents:
                del self._incidents[iid]
                count += 1
        return count

    def get_statistics(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for incident in self._incidents.values():
            stats[incident.state] = stats.get(incident.state, 0) + 1
        stats["dead_letter"] = len(self._dead_letter_queue)
        stats["total"] = len(self._incidents)
        return stats
