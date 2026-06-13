"""Protocols to break circular dependencies between state/context pairs.

Each state ABC needs to reference its context class in method signatures.
By defining Protocols here, state files import the Protocol instead of
the concrete context class, eliminating the circular import chain.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .engine_states import EngineState
    from .instance_states import ProcessState
    from .token_states import TokenState
    from .transaction_states import TransactionState
    from ..runtime.circuit_states import CBState


@runtime_checkable
class IEngine(Protocol):
    """Protocol for OrchestrationEngine used by engine state classes."""

    _lifecycle_state: EngineState

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def pause(self) -> None: ...
    async def resume(self) -> None: ...


@runtime_checkable
class IProcessInstance(Protocol):
    """Protocol for ProcessInstance used by process state classes."""

    id: str
    end_time: Any
    delete_reason: str | None

    def set_state(self, state: Any, state_obj: ProcessState) -> None: ...

    def _calculate_duration(self) -> None: ...


@runtime_checkable
class IToken(Protocol):
    """Protocol for Token used by token state classes."""

    token_id: str
    waiting_for: str | None
    wait_start_time: Any
    updated_at: Any
    completed_at: Any

    def set_state(self, state: Any, state_obj: TokenState) -> None: ...


@runtime_checkable
class ITransactionScope(Protocol):
    """Protocol for TransactionScope used by transaction state classes."""

    _lifecycle_state: TransactionState

    async def _do_prepare(self) -> bool: ...

    async def _do_commit(self) -> bool: ...

    async def _do_rollback(self) -> bool: ...


@runtime_checkable
class ICircuitBreaker(Protocol):
    """Protocol for CircuitBreaker used by circuit breaker state classes."""

    _state_obj: CBState
    failure_count: int
    last_failure_time: float
    half_open_calls: int
    success_count: int
    state: str
    name: str

    # Config is a nested object, typed loosely to avoid circular deps
    config: Any


@runtime_checkable
class IProcessDefinition(Protocol):
    """Protocol for ProcessDefinition used in engine_services type annotations."""
    id: str
    key: str


@runtime_checkable
class IDeployment(Protocol):
    """Protocol for Deployment used in engine_services type annotations."""
    definitions: dict[str, IProcessDefinition]

