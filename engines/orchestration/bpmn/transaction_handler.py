"""Transaction subprocess and compensation handling for BPMN."""

from __future__ import annotations

from dataclasses import dataclass

from ..runtime.compensation import CompensationManager, CompensationStep


@dataclass(frozen=True)
class TransactionBoundary:
    transaction_id: str
    compensate: bool


class TransactionHandler:
    def __init__(self) -> None:
        self._compensation = CompensationManager()

    def begin(self, boundary: TransactionBoundary) -> None:
        self._compensation.register(CompensationStep(name=f"rollback:{boundary.transaction_id}", action=lambda: None))

    def commit(self) -> None:
        self._compensation.clear()

    def rollback(self) -> list[str]:
        return self._compensation.rollback()
