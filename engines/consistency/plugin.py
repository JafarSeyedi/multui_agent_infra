# engines/consistency/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ITransactionManager(ABC):
    name: str = "base"

    @abstractmethod
    async def begin(self) -> str: ...

    @abstractmethod
    async def commit(self, txn_id: str) -> None: ...

    @abstractmethod
    async def rollback(self, txn_id: str) -> None: ...


class IIdempotencyChecker(ABC):
    name: str = "base"

    @abstractmethod
    async def is_processed(self, idempotency_key: str) -> bool: ...

    @abstractmethod
    async def mark_processed(self, idempotency_key: str, result: dict[str, Any] | None = None) -> None: ...
