from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

from engines.memory.models import MemoryItem
from engines.memory.models import MemoryResult


class BaseMemory(ABC):
    """High-level memory engine abstraction."""

    @abstractmethod
    async def remember(self, key: str, content: str, metadata: dict[str, Any] | None = None) -> MemoryItem:
        ...

    @abstractmethod
    async def recall(self, key: str) -> MemoryItem | None:
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> MemoryResult:
        ...

    @abstractmethod
    async def forget(self, key: str) -> bool:
        ...

    @abstractmethod
    async def stats(self) -> dict[str, Any]:
        ...
