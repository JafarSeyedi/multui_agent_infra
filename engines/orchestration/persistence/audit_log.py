"""Comprehensive audit logging for orchestration runtime.

Tracks all user operations and system events per Camunda/RuoyiOffice patterns.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


logger = logging.getLogger(__name__)


class AuditOperationType(str, Enum):
    DEPLOYMENT_CREATE = "deployment.create"
    DEPLOYMENT_DELETE = "deployment.delete"
    PROCESS_INSTANCE_START = "process_instance.start"
    PROCESS_INSTANCE_COMPLETE = "process_instance.complete"
    PROCESS_INSTANCE_TERMINATE = "process_instance.terminate"
    PROCESS_INSTANCE_MIGRATE = "process_instance.migrate"
    PROCESS_INSTANCE_MODIFY = "process_instance.modify"
    ACTIVITY_START = "activity.start"
    ACTIVITY_COMPLETE = "activity.complete"
    ACTIVITY_FAIL = "activity.fail"
    TASK_CLAIM = "task.claim"
    TASK_COMPLETE = "task.complete"
    TASK_DELEGATE = "task.delegate"
    TASK_ESCALATE = "task.escalate"
    VARIABLE_SET = "variable.set"
    VARIABLE_REMOVE = "variable.remove"
    INCIDENT_CREATE = "incident.create"
    INCIDENT_RESOLVE = "incident.resolve"
    INCIDENT_RETRY = "incident.retry"
    SIGNAL_SEND = "signal.send"
    MESSAGE_SEND = "message.send"
    BATCH_OPERATION = "batch.operation"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATE = "user.create"
    USER_DELETE = "user.delete"
    TENANT_CREATE = "tenant.create"
    TENANT_DEACTIVATE = "tenant.deactivate"


@dataclass
class AuditEntry:
    entry_id: str = ""
    operation_type: str = ""
    user_id: str | None = None
    instance_id: str | None = None
    activity_id: str | None = None
    definition_key: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    source_ip: str | None = None
    result: str = "success"
    error_message: str | None = None

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.entry_id:
            from uuid import uuid4
            self.entry_id = str(uuid4())


@dataclass
class AuditQuery:
    operation_type: str | None = None
    user_id: str | None = None
    instance_id: str | None = None
    definition_key: str | None = None
    after: str | None = None
    before: str | None = None
    result: str | None = None
    limit: int = 100
    offset: int = 0


class AuditLog:
    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []

    def log(
        self,
        operation_type: str,
        user_id: str | None = None,
        instance_id: str | None = None,
        activity_id: str | None = None,
        definition_key: str | None = None,
        details: dict[str, Any] | None = None,
        result: str = "success",
        error_message: str | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            operation_type=operation_type,
            user_id=user_id,
            instance_id=instance_id,
            activity_id=activity_id,
            definition_key=definition_key,
            details=details or {},
            result=result,
            error_message=error_message,
        )
        self._entries.append(entry)
        logger.debug("Audit: %s by %s on %s", operation_type, user_id, instance_id)
        return entry

    def query(self, query: AuditQuery) -> list[AuditEntry]:
        results = self._entries
        if query.operation_type:
            results = [e for e in results if e.operation_type == query.operation_type]
        if query.user_id:
            results = [e for e in results if e.user_id == query.user_id]
        if query.instance_id:
            results = [e for e in results if e.instance_id == query.instance_id]
        if query.definition_key:
            results = [e for e in results if e.definition_key == query.definition_key]
        if query.after:
            results = [e for e in results if e.timestamp >= query.after]
        if query.before:
            results = [e for e in results if e.timestamp <= query.before]
        if query.result:
            results = [e for e in results if e.result == query.result]
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[query.offset:query.offset + query.limit]

    def get_entries_for_instance(self, instance_id: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.instance_id == instance_id]

    def get_entries_for_user(self, user_id: str) -> list[AuditEntry]:
        return [e for e in self._entries if e.user_id == user_id]

    def get_operation_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._entries:
            counts[entry.operation_type] = counts.get(entry.operation_type, 0) + 1
        return counts

    def clear(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count
