# engines/consistency/backends/in_memory/in_memory_consistency.py
from __future__ import annotations

import uuid
from typing import Any

from ...models.consistency_models import Transaction, IdempotencyRecord
from ...plugin import ITransactionManager, IIdempotencyChecker


class InMemoryTransactionManager(ITransactionManager):
    name = "in_memory"

    def __init__(self) -> None:
        self._txns: dict[str, Transaction] = {}

    async def begin(self) -> str:
        txn_id = str(uuid.uuid4())
        self._txns[txn_id] = Transaction(txn_id=txn_id, status="pending")
        return txn_id

    async def commit(self, txn_id: str) -> None:
        if txn_id in self._txns:
            self._txns[txn_id].status = "committed"

    async def rollback(self, txn_id: str) -> None:
        if txn_id in self._txns:
            self._txns[txn_id].status = "rolled_back"


class InMemoryIdempotencyChecker(IIdempotencyChecker):
    name = "in_memory"

    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    async def is_processed(self, idempotency_key: str) -> bool:
        rec = self._records.get(idempotency_key)
        return rec is not None and rec.processed

    async def mark_processed(self, idempotency_key: str, result: dict[str, Any] | None = None) -> None:
        self._records[idempotency_key] = IdempotencyRecord(
            key=idempotency_key, processed=True, result=result
        )
