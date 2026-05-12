"""
Process Instance Management

Manages process instance lifecycle, state transitions, and metadata.
Supports BPMN, CMMN, State Machine, and other orchestration standards.
"""

import logging
from datetime import datetime
from typing import Any, Set
from enum import Enum
from dataclasses import dataclass, field
from uuid import uuid4


logger = logging.getLogger(__name__)


class InstanceState(Enum):
    """Process instance states"""
    ACTIVE = "active"  # Instance is running
    SUSPENDED = "suspended"  # Instance is paused
    COMPLETED = "completed"  # Instance completed successfully
    TERMINATED = "terminated"  # Instance was terminated
    FAILED = "failed"  # Instance failed with error
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


class ProcessInstance:
    """
    Represents a running process instance.
    
    Tracks instance lifecycle, state, variables, and execution history.
    Supports hierarchical instances (parent-child relationships).
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
        variables: dict[str, Any] | None = None
    ) -> None:
        self.id = id
        self.definition_id = definition_id
        self.definition_key = definition_key
        self.definition_version = definition_version
        self.business_key = business_key
        self.tenant_id = tenant_id
        self.state = state
        self.instance_type = instance_type
        
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
        self.variables: dict[str, Any] = variables or {}
        
        # Activity tracking
        self.active_activities: dict[str, ActivityInstance] = {}
        self.completed_activities: list[ActivityInstance] = []
        
        # Incidents
        self.incidents: list[IncidentInfo] = []
        self.incident_count = 0
        
        # Metadata
        self.metadata: dict[str, Any] = {}
        self.delete_reason: str | None = None
        
        # Execution tracking
        self.current_activity_id: str | None = None
        self.execution_path: list[str] = []  # Track execution flow
        
        logger.debug(f"Created process instance: {id}")
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a process variable"""
        self.variables[name] = value
        logger.debug(f"Set variable '{name}' in instance {self.id}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
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
    
    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set multiple variables"""
        self.variables.update(variables)
    
    def get_all_variables(self) -> dict[str, Any]:
        """Get all variables"""
        return self.variables.copy()
    
    def suspend(self) -> None:
        """Suspend the process instance"""
        if self.state != InstanceState.ACTIVE:
            raise RuntimeError(f"Cannot suspend instance in state: {self.state}")
        
        self.state = InstanceState.SUSPENDED
        logger.info(f"Suspended instance: {self.id}")
    
    def resume(self) -> None:
        """Resume the process instance"""
        if self.state != InstanceState.SUSPENDED:
            raise RuntimeError(f"Cannot resume instance in state: {self.state}")
        
        self.state = InstanceState.ACTIVE
        logger.info(f"Resumed instance: {self.id}")
    
    def complete(self) -> None:
        """Mark the instance as completed"""
        self.state = InstanceState.COMPLETED
        self.end_time = datetime.utcnow()
        self._calculate_duration()
        logger.info(f"Completed instance: {self.id}")
    
    def terminate(self, reason: str = "Terminated") -> None:
        """Terminate the process instance"""
        self.state = InstanceState.TERMINATED
        self.end_time = datetime.utcnow()
        self.delete_reason = reason
        self._calculate_duration()
        logger.info(f"Terminated instance: {self.id} - {reason}")
    
    def fail(self, error_message: str) -> None:
        """Mark the instance as failed"""
        self.state = InstanceState.FAILED
        self.end_time = datetime.utcnow()
        self.delete_reason = error_message
        self._calculate_duration()
        logger.error(f"Failed instance: {self.id} - {error_message}")
    
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
    
    def to_dict(self) -> dict[str, Any]:
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
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "variables": self.variables,
            "active_activities": len(self.active_activities),
            "completed_activities": len(self.completed_activities),
            "incident_count": self.incident_count,
            "child_instances": len(self.child_instances),
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return (
            f"ProcessInstance(id={self.id}, definition={self.definition_key}, "
            f"state={self.state.value}, type={self.instance_type.value})"
        )


class InstanceManager:
    """
    Manages process instances across the engine.
    
    Provides instance lifecycle management, queries, and statistics.
    """
    
    def __init__(self) -> None:
        self.instances: dict[str, ProcessInstance] = {}
        self.business_key_index: dict[str, Set[str]] = {}  # business_key -> instance_ids
        self.definition_index: dict[str, Set[str]] = {}  # definition_key -> instance_ids
    
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
    
    def get_statistics(self) -> dict[str, Any]:
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
