# engines/persistence/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class IVectorStore(ABC):
    name: str = "base"

    @abstractmethod
    async def upsert(self, collection: str, id: str, vector: list[float], metadata: dict[str, Any]) -> None: ...

    @abstractmethod
    async def search(self, collection: str, query: list[float], top_k: int = 10) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def delete(self, collection: str, id: str) -> None: ...


class IBlobStorage(ABC):
    name: str = "base"

    @abstractmethod
    async def upload(self, path: str, data: bytes) -> str: ...

    @abstractmethod
    async def download(self, path: str) -> Optional[bytes]: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...
