"""State pattern for ProcessInstance lifecycle.

Each state encapsulates the valid transitions and behavior
for that state, replacing enum + conditional guards.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .instance import ProcessInstance, ActivityInstance

logger = logging.getLogger(__name__)


class ProcessState(ABC):
    """Base class for process instance states."""

    @abstractmethod
    def suspend(self, instance: ProcessInstance) -> None: ...
    @abstractmethod
    def resume(self, instance: ProcessInstance) -> None: ...
    @abstractmethod
    def complete(self, instance: ProcessInstance) -> None: ...
    @abstractmethod
    def terminate(self, instance: ProcessInstance, reason: str) -> None: ...
    @abstractmethod
    def fail(self, instance: ProcessInstance, error_message: str) -> None: ...


class _ActiveState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.SUSPENDED, _SuspendedState())
        logger.info("Suspended instance: %s", instance.id)

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume instance {instance.id}: already active")

    def complete(self, instance: ProcessInstance) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.COMPLETED, _CompletedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance._calculate_duration()
        logger.info("Completed instance: %s", instance.id)

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = reason
        instance._calculate_duration()
        logger.info("Terminated instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.FAILED, _FailedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = error_message
        instance._calculate_duration()
        logger.error("Failed instance: %s - %s", instance.id, error_message)


class _SuspendedState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend instance {instance.id}: already suspended")

    def resume(self, instance: ProcessInstance) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.ACTIVE, _ActiveState())
        logger.info("Resumed instance: %s", instance.id)

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot complete suspended instance {instance.id}: resume first")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = reason
        instance._calculate_duration()
        logger.info("Terminated (from suspended) instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.FAILED, _FailedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = error_message
        instance._calculate_duration()
        logger.error("Failed (from suspended) instance: %s - %s", instance.id, error_message)


class _CompletedState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend completed instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume completed instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Instance {instance.id} is already completed")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        raise RuntimeError(f"Cannot terminate completed instance {instance.id}")

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        raise RuntimeError(f"Cannot fail completed instance {instance.id}")


class _FailedState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend failed instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume failed instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot complete failed instance {instance.id}")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        logger.info("Terminated (from failed) instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        raise RuntimeError(f"Instance {instance.id} already failed: {error_message}")


class _TerminatedState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend terminated instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume terminated instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot complete terminated instance {instance.id}")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        raise RuntimeError(f"Instance {instance.id} is already terminated")

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        raise RuntimeError(f"Cannot fail terminated instance {instance.id}")


class _DraftState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend draft instance {instance.id}: activate first")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume draft instance {instance.id}: not suspended")

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot complete draft instance {instance.id}: activate first")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = reason
        instance._calculate_duration()
        logger.info("Terminated draft instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.FAILED, _FailedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = error_message
        instance._calculate_duration()
        logger.error("Failed draft instance: %s - %s", instance.id, error_message)


class _ClosedState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend closed instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume closed instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot complete closed instance {instance.id}")

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        raise RuntimeError(f"Cannot terminate closed instance {instance.id}")

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        raise RuntimeError(f"Cannot fail closed instance {instance.id}")


class _CompensatingState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend compensating instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume compensating instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.COMPLETED, _CompletedState())
        logger.info("Completed (from compensating) instance: %s", instance.id)

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = reason
        instance._calculate_duration()
        logger.info("Terminated compensating instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.FAILED, _FailedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = error_message
        instance._calculate_duration()
        logger.error("Failed compensating instance: %s - %s", instance.id, error_message)


class _MigratingState(ProcessState):
    def suspend(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot suspend migrating instance {instance.id}")

    def resume(self, instance: ProcessInstance) -> None:
        raise RuntimeError(f"Cannot resume migrating instance {instance.id}")

    def complete(self, instance: ProcessInstance) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.COMPLETED, _CompletedState())
        logger.info("Completed (from migrating) instance: %s", instance.id)

    def terminate(self, instance: ProcessInstance, reason: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.TERMINATED, _TerminatedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = reason
        instance._calculate_duration()
        logger.info("Terminated migrating instance: %s - %s", instance.id, reason)

    def fail(self, instance: ProcessInstance, error_message: str) -> None:
        from .instance import InstanceState
        instance.set_state(InstanceState.FAILED, _FailedState())
        import datetime
        instance.end_time = datetime.datetime.utcnow()
        instance.delete_reason = error_message
        instance._calculate_duration()
        logger.error("Failed migrating instance: %s - %s", instance.id, error_message)


# State registry: maps InstanceState enum values to default state instances
_STATE_MAP: dict[str, ProcessState] = {}

def state_for(enum_value: str) -> ProcessState:
    """Get the state instance for a given InstanceState enum value."""
    global _STATE_MAP
    if not _STATE_MAP:
        from .instance import InstanceState
        _STATE_MAP = {
            InstanceState.ACTIVE.value: _ActiveState(),
            InstanceState.SUSPENDED.value: _SuspendedState(),
            InstanceState.COMPLETED.value: _CompletedState(),
            InstanceState.FAILED.value: _FailedState(),
            InstanceState.TERMINATED.value: _TerminatedState(),
            InstanceState.DRAFT.value: _DraftState(),
            InstanceState.CLOSED.value: _ClosedState(),
            InstanceState.COMPENSATING.value: _CompensatingState(),
            InstanceState.MIGRATING.value: _MigratingState(),
        }
    return _STATE_MAP[enum_value]
