"""Transaction subprocess and compensation handling for BPMN.

Supports BPMN transaction subprocess and cancellation/compensation semantics.
Provides OSDM-typed TransactionSubProcess support alongside backward-compatible
dict-based methods.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable

from enum import Enum

from ..runtime.compensation import CompensationManager, CompensationStep
from ..core.event_bus import Event, EventType
from ..core.engine import OrchestrationEngine

from .models.bpmn_models import (
    Artifact,
    FlowElement,
    LaneSet,
    TransactionMethod,
    TransactionSubProcess,
)


logger = logging.getLogger(__name__)


class TransactionState(str, Enum):
    ACTIVE = "active"
    CANCELLING = "cancelling"
    COMPENSATING = "compensating"
    FAILED = "failed"
    CANCELLED = "cancelled"
    COMPENSATED = "compensated"
    COMPLETED = "completed"


@dataclass(frozen=True)
class HandlerTransactionBoundary:
    transaction_id: str
    compensate: bool = True
    cancel_content: bool = True
    process_ref: str | None = None
    method: TransactionMethod = TransactionMethod.COMPENSATE
    transaction: TransactionSubProcess | None = None

    @classmethod
    def from_osdm(cls, transaction: TransactionSubProcess) -> HandlerTransactionBoundary:
        return cls(
            transaction_id=transaction.id,
            compensate=True,
            cancel_content=True,
            process_ref=None,
            method=cls.get_transaction_method(transaction),
            transaction=transaction,
        )

    @staticmethod
    def get_transaction_method(transaction: TransactionSubProcess) -> TransactionMethod:
        method = getattr(transaction, "method", None)
        if isinstance(method, TransactionMethod):
            return method
        if isinstance(method, str):
            for candidate in TransactionMethod:
                if candidate.value == method:
                    return candidate
        return TransactionMethod.COMPENSATE


@dataclass
class HandlerTransactionContext:
    transaction_id: str
    state: TransactionState = TransactionState.ACTIVE
    children: list[str] = field(default_factory=list)
    completed_children: list[str] = field(default_factory=list)
    failed_children: list[str] = field(default_factory=list)
    compensation_stack: list[str] = field(default_factory=list)
    error: str | None = None
    escalation_code: str | None = None


class TransactionHandler:
    def __init__(self, orchestration_engine: OrchestrationEngine | None = None) -> None:
        self._compensation = CompensationManager()
        self._engine = orchestration_engine
        self._contexts: dict[str, HandlerTransactionContext] = {}

    def begin(self, boundary: HandlerTransactionBoundary) -> HandlerTransactionContext:
        ctx = HandlerTransactionContext(transaction_id=boundary.transaction_id)
        self._contexts[boundary.transaction_id] = ctx
        self._compensation.register(
            CompensationStep(name=f"rollback:{boundary.transaction_id}", action=lambda: self._do_compensate(boundary.transaction_id))
        )
        return ctx

    def begin_from_osdm(self, transaction: TransactionSubProcess) -> HandlerTransactionContext:
        boundary = HandlerTransactionBoundary.from_osdm(transaction)
        ctx = self.begin(boundary)
        children = list(transaction.flow_elements.keys()) if transaction.flow_elements else []
        for child_id in children:
            ctx.children.append(child_id)
        return ctx

    def get_context(self, transaction_id: str) -> HandlerTransactionContext | None:
        return self._contexts.get(transaction_id)

    def register_child(self, transaction_id: str, child_id: str) -> None:
        ctx = self._contexts.get(transaction_id)
        if ctx is not None:
            ctx.children.append(child_id)

    def complete_child(self, transaction_id: str, child_id: str) -> None:
        ctx = self._contexts.get(transaction_id)
        if ctx is not None and child_id not in ctx.completed_children:
            ctx.completed_children.append(child_id)

    def fail_child(self, transaction_id: str, child_id: str) -> None:
        ctx = self._contexts.get(transaction_id)
        if ctx is not None and child_id not in ctx.failed_children:
            ctx.failed_children.append(child_id)

    def commit(self, transaction_id: str) -> bool:
        ctx = self._contexts.get(transaction_id)
        if ctx is None:
            return False
        ctx.state = TransactionState.COMPLETED
        self._compensation.unregister(f"rollback:{transaction_id}")
        return True

    def rollback(self, transaction_id: str, reason: str = "") -> list[str]:
        ctx = self._contexts.get(transaction_id)
        if ctx is None:
            return [f"Transaction {transaction_id} not found"]
        ctx.state = TransactionState.COMPENSATING
        ctx.error = reason
        compensated = list(reversed(ctx.completed_children))
        for child_id in compensated:
            ctx.compensation_stack.append(child_id)
        ctx.state = TransactionState.COMPENSATED
        return compensated

    def cancel(self, transaction_id: str, reason: str = "") -> list[str]:
        ctx = self._contexts.get(transaction_id)
        if ctx is None:
            return [f"Transaction {transaction_id} not found"]
        ctx.state = TransactionState.CANCELLING
        ctx.error = reason
        cancelled = [c for c in ctx.children if c not in ctx.completed_children]
        ctx.state = TransactionState.CANCELLED
        return cancelled

    def _do_compensate(self, transaction_id: str) -> None:
        self.rollback(transaction_id, "compensation_triggered")

    def is_active(self, transaction_id: str) -> bool:
        ctx = self._contexts.get(transaction_id)
        return ctx is not None and ctx.state == TransactionState.ACTIVE

    def get_statistics(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ctx in self._contexts.values():
            counts[ctx.state.value] = counts.get(ctx.state.value, 0) + 1
        return counts
