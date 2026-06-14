"""
Process Instance Management

Manages process instance lifecycle, state transitions, and metadata.
Supports BPMN, CMMN, State Machine, and other orchestration standards.
Aligned with OSDM instance semantics.
Uses State pattern for lifecycle transitions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, cast
from uuid import uuid4

from ..._types import Metadata, RawData, VariableValue
from ...document.models.dsdm_models import DataDocument
from ...document.models.media_types import MEDIA_TYPES
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bpmn.models.bpmn_models import Process
    from ..cmmn.models.cmmn_models import Stage
    from ..dmn.models.dmn_models import Decision
    from ..state_machine.models.state_machine_models import StateMachineModel

from .instance_states import ProcessState


logger = logging.getLogger(__name__)


class InstanceState(Enum):
    """Process instance states — includes BPMN, CMMN, and State Machine states."""
    ACTIVE = "active"  # Instance is running
    SUSPENDED = "suspended"  # Instance is paused
    COMPLETED = "completed"  # Instance completed successfully
    TERMINATED = "terminated"  # Instance was terminated
    FAILED = "failed"  # Instance failed
    DRAFT = "draft"  # CMMN: Case created but not yet active (§5.2)
    CLOSED = "closed"  # CMMN: Case archived after completion/termination (§5.2)
    COMPENSATING = "compensating"  # Instance is compensating
    MIGRATING = "migrating"  # Instance is being migrated


class InstanceType(Enum):
    """Types of process instances"""
    ROOT = "root"  # Root process instance
    SUBPROCESS = "subprocess"  # Subprocess instance
    CALL_ACTIVITY = "call_activity"  # Called process instance
    EVENT_SUBPROCESS = "event_subprocess"  # Event subprocess instance
    TRANSACTION = "transaction"  # Transaction subprocess


@dataclass
class IncidentInfo:
    """Information about a process incident"""
    id: str
    type: str  # failed_job, failed_external_task, etc.
    message: str
    timestamp: datetime
    activity_id: str | None = None
    job_id: str | None = None
    exception_message: str | None = None
    exception_stacktrace: str | None = None
    resolved: bool = False
    resolved_at: datetime | None = None

    def to_dict(self) -> RawData:
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "activity_id": self.activity_id,
            "job_id": self.job_id,
            "exception_message": self.exception_message,
            "exception_stacktrace": self.exception_stacktrace,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }

    @classmethod
    def from_dict(cls, payload: RawData) -> IncidentInfo:
        return cls(
            id=str(payload["id"]),
            type=str(payload["type"]),
            message=str(payload["message"]),
            timestamp=_parse_datetime(payload.get("timestamp")),
            activity_id=_optional_str(payload.get("activity_id")),
            job_id=_optional_str(payload.get("job_id")),
            exception_message=_optional_str(payload.get("exception_message")),
            exception_stacktrace=_optional_str(payload.get("exception_stacktrace")),
            resolved=bool(payload.get("resolved", False)),
            resolved_at=_parse_datetime(payload.get("resolved_at")) if payload.get("resolved_at") else None,
        )


@dataclass
class ActivityInstance:
    """Information about an activity instance"""
    id: str
    activity_id: str
    activity_name: str
    activity_type: str
    start_time: datetime
    end_time: datetime | None = None
    state: str = "active"
    incident_count: int = 0

    def to_dict(self) -> RawData:
        return {
            "id": self.id,
            "activity_id": self.activity_id,
            "activity_name": self.activity_name,
            "activity_type": self.activity_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "state": self.state,
            "incident_count": self.incident_count,
        }

    @classmethod
    def from_dict(cls, payload: RawData) -> ActivityInstance:
        return cls(
            id=str(payload["id"]),
            activity_id=str(payload["activity_id"]),
            activity_name=str(payload["activity_name"]),
            activity_type=str(payload["activity_type"]),
            start_time=_parse_datetime(payload.get("start_time")),
            end_time=_parse_datetime(payload.get("end_time")) if payload.get("end_time") else None,
            state=str(payload.get("state", "active")),
            incident_count=int(payload.get("incident_count", 0)),
        )


class ProcessInstance:
    """
    Represents a running process instance.

    Tracks instance lifecycle, state, variables, and execution history.
    Supports hierarchical instances (parent-child relationships).
    Aligned with OSDM Process/Stage/Decision/StateMachineModel semantics.
    """

    def __init__(
        self,
        id: str,
        definition_id: str,
        definition_key: str,
        definition_version: int,
        business_key: str | None = None,
        tenant_id: str | None = None,
        state: InstanceState = InstanceState.ACTIVE,
        instance_type: InstanceType = InstanceType.ROOT,
        parent_id: str | None = None,
        root_instance_id: str | None = None,
        super_instance_id: str | None = None,
        start_time: datetime | None = None,
        variables: dict[str, VariableValue] | None = None
    ) -> None:
        self.id = id
        self.definition_id = definition_id
        self.definition_key = definition_key
        self.definition_version = definition_version
        self.business_key = business_key
        self.tenant_id = tenant_id
        self.state = state
        self.instance_type = instance_type
        self._state: ProcessState | None = None

        # OSDM model references (lazy-loaded)
        self._osdm_process_ref: Process | None = None
        self._osdm_stage_ref: Stage | None = None
        self._osdm_decision_ref: Decision | None = None
        self._osdm_state_machine_ref: StateMachineModel | None = None

        # Hierarchy
        self.parent_id = parent_id
        self.root_instance_id = root_instance_id or id
        self.super_instance_id = super_instance_id
        self.child_instances: list[str] = []

        # Timing
        self.start_time = start_time or datetime.utcnow()
        self.end_time: datetime | None = None
        self.duration_ms: int | None = None

        # Variables
        self.variables: dict[str, VariableValue] = variables or {}
        
        # Activity tracking
        self.active_activities: dict[str, ActivityInstance] = {}
        self.completed_activities: list[ActivityInstance] = []
        
        # Incidents
        self.incidents: list[IncidentInfo] = []
        self.incident_count = 0
        
        # Metadata
        self.metadata: Metadata = {}
        self.delete_reason: str | None = None
        
        # Execution tracking
        self.current_activity_id: str | None = None
        self.execution_path: list[str] = []  # Track execution flow
        
        logger.debug(f"Created process instance: {id}")
    
    def set_variable(self, name: str, value: VariableValue) -> None:
        """Set a process variable"""
        self.variables[name] = value
        logger.debug(f"Set variable '{name}' in instance {self.id}")
    
    def get_variable(self, name: str, default: VariableValue | None = None) -> VariableValue | None:
        """Get a process variable"""
        return self.variables.get(name, default)
    
    def has_variable(self, name: str) -> bool:
        """Check if a variable exists"""
        return name in self.variables
    
    def remove_variable(self, name: str) -> bool:
        """Remove a process variable"""
        if name in self.variables:
            del self.variables[name]
            logger.debug(f"Removed variable '{name}' from instance {self.id}")
            return True
        return False
    
    def set_variables(self, variables: dict[str, VariableValue]) -> None:
        """Set multiple variables"""
        self.variables.update(variables)
    
    def get_all_variables(self) -> dict[str, VariableValue]:
        """Get all variables"""
        return self.variables.copy()
    
    def _get_state(self) -> ProcessState:
        from .instance_states import state_for
        if self._state is None:
            self._state = state_for(self.state.value)
        return self._state

    def set_state(self, enum_state: InstanceState, state_obj: ProcessState | None = None) -> None:
        """Set the state enum and optional state object."""
        self.state = enum_state
        if state_obj is not None:
            self._state = state_obj
        else:
            from .instance_states import state_for
            self._state = state_for(enum_state.value)

    def suspend(self) -> None:
        """Suspend the process instance (delegates to state object)."""
        self._get_state().suspend(self)
    
    def resume(self) -> None:
        """Resume the process instance (delegates to state object)."""
        self._get_state().resume(self)
    
    def complete(self) -> None:
        """Mark the instance as completed (delegates to state object)."""
        self._get_state().complete(self)
    
    def terminate(self, reason: str = "Terminated") -> None:
        """Terminate the process instance (delegates to state object)."""
        self._get_state().terminate(self, reason)
    
    def fail(self, error_message: str) -> None:
        """Mark the instance as failed (delegates to state object)."""
        self._get_state().fail(self, error_message)
    
    def _calculate_duration(self) -> None:
        """Calculate instance duration"""
        if self.end_time:
            delta = self.end_time - self.start_time
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def start_activity(
        self,
        activity_id: str,
        activity_name: str,
        activity_type: str
    ) -> ActivityInstance:
        """Start an activity instance"""
        activity_instance = ActivityInstance(
            id=str(uuid4()),
            activity_id=activity_id,
            activity_name=activity_name,
            activity_type=activity_type,
            start_time=datetime.utcnow()
        )
        
        self.active_activities[activity_id] = activity_instance
        self.current_activity_id = activity_id
        self.execution_path.append(activity_id)
        
        logger.debug(f"Started activity '{activity_id}' in instance {self.id}")
        return activity_instance
    
    def complete_activity(self, activity_id: str) -> None:
        """Complete an activity instance"""
        if activity_id not in self.active_activities:
            logger.warning(f"Activity '{activity_id}' not found in active activities")
            return
        
        activity = self.active_activities.pop(activity_id)
        activity.end_time = datetime.utcnow()
        activity.state = "completed"
        self.completed_activities.append(activity)
        
        logger.debug(f"Completed activity '{activity_id}' in instance {self.id}")
    
    def fail_activity(self, activity_id: str, error_message: str) -> None:
        """Fail an activity instance"""
        if activity_id in self.active_activities:
            activity = self.active_activities[activity_id]
            activity.state = "failed"
            activity.incident_count += 1
    
    def create_incident(
        self,
        incident_type: str,
        message: str,
        activity_id: str | None = None,
        exception_message: str | None = None,
        exception_stacktrace: str | None = None
    ) -> IncidentInfo:
        """Create an incident"""
        incident = IncidentInfo(
            id=str(uuid4()),
            type=incident_type,
            message=message,
            timestamp=datetime.utcnow(),
            activity_id=activity_id,
            exception_message=exception_message,
            exception_stacktrace=exception_stacktrace
        )
        
        self.incidents.append(incident)
        self.incident_count += 1
        
        if activity_id and activity_id in self.active_activities:
            self.active_activities[activity_id].incident_count += 1
        
        logger.warning(f"Created incident in instance {self.id}: {message}")
        return incident
    
    def resolve_incident(self, incident_id: str) -> bool:
        """Resolve an incident"""
        for incident in self.incidents:
            if incident.id == incident_id and not incident.resolved:
                incident.resolved = True
                incident.resolved_at = datetime.utcnow()
                logger.info(f"Resolved incident {incident_id} in instance {self.id}")
                return True
        return False
    
    def get_active_incidents(self) -> list[IncidentInfo]:
        """Get all active (unresolved) incidents"""
        return [inc for inc in self.incidents if not inc.resolved]
    
    def add_child_instance(self, child_id: str) -> None:
        """Add a child instance"""
        if child_id not in self.child_instances:
            self.child_instances.append(child_id)
    
    def is_root_instance(self) -> bool:
        """Check if this is a root instance"""
        return self.instance_type == InstanceType.ROOT and self.parent_id is None
    
    def is_subprocess(self) -> bool:
        """Check if this is a subprocess instance"""
        return self.instance_type in (
            InstanceType.SUBPROCESS,
            InstanceType.CALL_ACTIVITY,
            InstanceType.EVENT_SUBPROCESS
        )
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value"""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        self.metadata[key] = value
    
    def to_dict(self) -> RawData:
        """Convert instance to dictionary representation"""
        return {
            "id": self.id,
            "definition_id": self.definition_id,
            "definition_key": self.definition_key,
            "definition_version": self.definition_version,
            "business_key": self.business_key,
            "tenant_id": self.tenant_id,
            "state": self.state.value,
            "instance_type": self.instance_type.value,
            "parent_id": self.parent_id,
            "root_instance_id": self.root_instance_id,
            "super_instance_id": self.super_instance_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "variables": self.variables,
            "active_activity_instances": {
                key: value.to_dict() for key, value in self.active_activities.items()
            },
            "completed_activity_instances": [activity.to_dict() for activity in self.completed_activities],
            "incidents": [incident.to_dict() for incident in self.incidents],
            "active_activities": len(self.active_activities),
            "completed_activities": len(self.completed_activities),
            "incident_count": self.incident_count,
            "child_instances": list(self.child_instances),
            "current_activity_id": self.current_activity_id,
            "execution_path": list(self.execution_path),
            "delete_reason": self.delete_reason,
            "metadata": self.metadata
        }

    def to_record_payload(self) -> RawData:
        payload = self.to_dict()
        payload["instance_id"] = self.id
        payload["payload"] = {
            "variables": dict(self.variables),
            "active_activity_instances": payload.pop("active_activity_instances"),
            "completed_activity_instances": payload.pop("completed_activity_instances"),
            "incidents": payload.pop("incidents"),
            "metadata": dict(self.metadata),
            "execution_path": payload.pop("execution_path"),
            "current_activity_id": payload.pop("current_activity_id"),
            "delete_reason": payload.pop("delete_reason"),
            "child_instances": payload["child_instances"],
        }
        return payload

    @classmethod
    def from_record_payload(cls, payload: RawData) -> ProcessInstance:
        nested_payload = cast(dict[str, Any], payload.get("payload")) if isinstance(payload.get("payload"), dict) else {}
        instance = cls(
            id=str(payload.get("instance_id") or payload.get("id")),
            definition_id=str(payload.get("definition_id", "")),
            definition_key=str(payload.get("definition_key", "")),
            definition_version=int(payload.get("definition_version", 0)),
            business_key=_optional_str(payload.get("business_key")),
            tenant_id=_optional_str(payload.get("tenant_id")),
            state=InstanceState(str(payload.get("state", InstanceState.ACTIVE.value))),
            instance_type=InstanceType(str(payload.get("instance_type", InstanceType.ROOT.value))),
            parent_id=_optional_str(payload.get("parent_id")),
            root_instance_id=_optional_str(payload.get("root_instance_id")),
            super_instance_id=_optional_str(payload.get("super_instance_id")),
            start_time=_parse_datetime(payload.get("start_time")),
            variables=dict(nested_payload.get("variables") or payload.get("variables") or {}),
        )
        instance.end_time = _parse_datetime(payload.get("end_time")) if payload.get("end_time") else None
        instance.duration_ms = int(payload["duration_ms"]) if payload.get("duration_ms") is not None else None
        instance.child_instances = list(nested_payload.get("child_instances") or payload.get("child_instances") or [])
        instance.current_activity_id = _optional_str(nested_payload.get("current_activity_id"))
        instance.execution_path = list(nested_payload.get("execution_path") or [])
        instance.delete_reason = _optional_str(nested_payload.get("delete_reason"))
        instance.metadata = dict(nested_payload.get("metadata") or payload.get("metadata") or {})
        instance.incidents = [
            IncidentInfo.from_dict(item) for item in list(nested_payload.get("incidents") or [])
            if isinstance(item, dict)
        ]
        instance.incident_count = len(instance.incidents)
        active_payload = nested_payload.get("active_activity_instances") or {}
        if isinstance(active_payload, dict):
            instance.active_activities = {
                key: ActivityInstance.from_dict(value)
                for key, value in active_payload.items()
                if isinstance(value, dict)
            }
        completed_payload = nested_payload.get("completed_activity_instances") or []
        instance.completed_activities = [
            ActivityInstance.from_dict(item)
            for item in completed_payload
            if isinstance(item, dict)
        ]
        return instance

    # ---------------------------------------------------------------------------
    # OSDM/DSDM serialization support
    # ---------------------------------------------------------------------------

    async def serialize_to_dsdm(self, *, variable_data: dict[str, VariableValue] | None = None) -> DataDocument:
        """Serialize this instance to a DSDM DataDocument with MSDM schema binding."""
        from ...document.models.dsdm_models import DataDocument
        from ...document.parsers.dsdm_parsers.dsdm_utils import build_node_from_python
        payload = variable_data or dict(self.variables)
        payload.update({
            "instance_id": self.id,
            "definition_id": self.definition_id,
            "definition_key": self.definition_key,
            "state": self.state.value,
            "instance_type": self.instance_type.value,
        })
        node = build_node_from_python(payload, path="$.instance", name="process_instance")
        return DataDocument(
            title=f"Process Instance {self.id}",
            document_id=f"instance:{self.id}",
            media_type=MEDIA_TYPES["json"],
            root=node,
        )

    async def to_dsdm_json(self) -> str:
        """Serialize this instance to JSON via DSDM serialization."""
        from ...document.writers.dsdm_writers.json_writer import JSONWriter
        doc = await self.serialize_to_dsdm()
        raw = await JSONWriter().write(doc)
        return raw.decode("utf-8")

    def __repr__(self) -> str:
        return (
            f"ProcessInstance(id={self.id}, definition={self.definition_key}, "
            f"state={self.state.value}, type={self.instance_type.value})"
        )


class _InstanceRepository(Protocol):
    async def save_persisted(self, instance_id: str, payload: RawData) -> RawData: ...
    def save(self, instance_id: str, payload: RawData) -> RawData: ...
    async def get_persisted(self, instance_id: str) -> RawData | None: ...
    def get(self, instance_id: str) -> RawData | None: ...
    def list(self) -> list[RawData]: ...


class InstanceManager:
    """
    Manages process instances across the engine.
    
    Provides instance lifecycle management, queries, and statistics.
    """
    
    def __init__(self, repository: _InstanceRepository | None = None) -> None:
        self.instances: dict[str, ProcessInstance] = {}
        self.business_key_index: dict[str, set[str]] = {}  # business_key -> instance_ids
        self.definition_index: dict[str, set[str]] = {}  # definition_key -> instance_ids
        self.repository = repository
    
    def add_instance(self, instance: ProcessInstance) -> None:
        """Add an instance to the manager"""
        self.instances[instance.id] = instance
        
        # Update indexes
        if instance.business_key:
            if instance.business_key not in self.business_key_index:
                self.business_key_index[instance.business_key] = set()
            self.business_key_index[instance.business_key].add(instance.id)
        
        if instance.definition_key not in self.definition_index:
            self.definition_index[instance.definition_key] = set()
        self.definition_index[instance.definition_key].add(instance.id)
    
    def get_instance(self, instance_id: str) -> ProcessInstance | None:
        """Get an instance by ID"""
        return self.instances.get(instance_id)
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance"""
        instance = self.instances.pop(instance_id, None)
        if not instance:
            return False
        
        # Update indexes
        if instance.business_key:
            if instance.business_key in self.business_key_index:
                self.business_key_index[instance.business_key].discard(instance_id)
        
        if instance.definition_key in self.definition_index:
            self.definition_index[instance.definition_key].discard(instance_id)
        
        return True
    
    def find_by_business_key(self, business_key: str) -> list[ProcessInstance]:
        """Find instances by business key"""
        instance_ids = self.business_key_index.get(business_key, set())
        return [self.instances[iid] for iid in instance_ids if iid in self.instances]
    
    def find_by_definition(self, definition_key: str) -> list[ProcessInstance]:
        """Find instances by definition key"""
        instance_ids = self.definition_index.get(definition_key, set())
        return [self.instances[iid] for iid in instance_ids if iid in self.instances]
    
    def find_by_state(self, state: InstanceState) -> list[ProcessInstance]:
        """Find instances by state"""
        return [inst for inst in self.instances.values() if inst.state == state]
    
    def get_statistics(self) -> RawData:
        """Get instance statistics"""
        state_counts: dict[str, int] = {}
        for instance in self.instances.values():
            state = instance.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        return {
            "total_instances": len(self.instances),
            "state_distribution": state_counts,
            "definitions": len(self.definition_index),
            "business_keys": len(self.business_key_index)
        }

    async def persist_instance(self, instance_id: str) -> RawData | None:
        if self.repository is None:
            return None
        instance = self.get_instance(instance_id)
        if instance is None:
            return None
        if hasattr(self.repository, "save_persisted"):
            return await self.repository.save_persisted(instance_id, instance.to_record_payload())
        return self.repository.save(instance_id, instance.to_record_payload())

    async def load_instance(self, instance_id: str) -> ProcessInstance | None:
        if self.repository is None:
            return self.get_instance(instance_id)
        if hasattr(self.repository, "get_persisted"):
            payload = await self.repository.get_persisted(instance_id)
        else:
            payload = self.repository.get(instance_id)
        if payload is None:
            return None
        instance = ProcessInstance.from_record_payload(payload)
        self.add_instance(instance)
        return instance

    async def load_all_instances(self) -> list[ProcessInstance]:
        if self.repository is None:
            return list(self.instances.values())
        payloads = self.repository.list()
        loaded: list[ProcessInstance] = []
        for payload in payloads:
            instance = ProcessInstance.from_record_payload(payload)
            self.add_instance(instance)
            loaded.append(instance)
        return loaded


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)
