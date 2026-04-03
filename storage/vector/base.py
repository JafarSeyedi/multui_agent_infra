from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class VectorDBAdapter(ABC):
    """Common async contract for vector database adapters."""

    @abstractmethod
    async def create_index(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create or initialize an index/collection."""

    @abstractmethod
    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Insert or update vectors and associated metadata."""

    @abstractmethod
    async def batch_upsert(self, items: List[Dict[str, Any]]) -> None:
        """Insert or update a batch of vector items."""

    @abstractmethod
    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search nearest neighbours and return normalized result dicts."""

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """Delete vectors by ID."""

    async def search(
        self,
        embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Compatibility wrapper for callers that use `search`."""
        return await self.query(vector=embedding, top_k=top_k, filters=filters)

    async def add_embeddings(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Compatibility wrapper for older indexing code."""
        await self.upsert(ids=ids, vectors=embeddings, metadata=metadata)

    async def delete_embeddings(self, ids: List[str]) -> None:
        """Compatibility wrapper for older deletion code."""
        await self.delete(ids)
