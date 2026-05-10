# engines/storage/vector/base.py
# embeddings
# semantic search
# similarity
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import Any

class VectorDBAdapter(ABC):
    """Common async contract for vector database adapters."""

    @abstractmethod
    async def create_index(
        self,
        name: str,
        dimension: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Create or initialize an index/collection."""

    @abstractmethod
    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        """Insert or update vectors and associated metadata."""
        ...

    @abstractmethod
    async def batch_upsert(self, items: list[dict[str, Any]]) -> None:
        """Insert or update a batch of vector items."""

    @abstractmethod
    async def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search nearest neighbours and return normalized result dicts."""

    @abstractmethod
    async def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        ...

    async def search(
        self,
        embedding: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Compatibility wrapper for callers that use `search`."""
        return await self.query(vector=embedding, top_k=top_k, filters=filters)

    async def add_embeddings(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        """Compatibility wrapper for older indexing code."""
        await self.upsert(ids=ids, vectors=embeddings, metadata=metadata)

    async def delete_embeddings(self, ids: list[str]) -> None:
        """Compatibility wrapper for older deletion code."""
        await self.delete(ids)




# engines/storage/vector/base.py

from abc import ABC, abstractmethod
from engines.storage.base_storage import BaseStorage


class VectorStorage(BaseStorage, ABC):
    """
    Vector index storage abstraction.
    """

    @abstractmethod
    async def upsert(
        self,
        id: str,
        vector: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        pass

    @abstractmethod
    async def delete(self, id: str) -> None:
        pass

    @abstractmethod
    async def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        pass
