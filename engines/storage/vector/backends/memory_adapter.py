# storage/vector/backends/memory_adapter.py
from __future__ import annotations

from typing import Any

import numpy as np

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class InMemoryVectorStore(VectorDBAdapter):
    """Simple in-memory cosine-similarity vector store for tests and local use."""

    def __init__(self) -> None:
        self._vectors: list[list[float]] = []
        self._metadatas: list[dict[str, Any]] = []
        self._ids: list[str] = []
        self._dimension: int | None = None

    async def create_index(
        self,
        name: str,
        dimension: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        self._dimension = dimension

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        if not ids:
            return
        if self._dimension is None:
            self._dimension = len(vectors[0])

        for item_id, vector, meta in zip(ids, vectors, metadata):
            normalized = normalize_embedding(vector)
            if len(normalized) != self._dimension:
                raise ValueError("Vector dimension does not match the initialized index dimension.")

            if item_id in self._ids:
                idx = self._ids.index(item_id)
                self._vectors[idx] = normalized
                self._metadatas[idx] = meta
            else:
                self._ids.append(item_id)
                self._vectors.append(normalized)
                self._metadatas.append(meta)

    async def batch_upsert(self, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        await self.upsert(
            ids=[item["id"] for item in items],
            vectors=[item["vector"] for item in items],
            metadata=[item["metadata"] for item in items],
        )

    async def query(
        self,
        vector: list[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self._vectors:
            return []
        if self._dimension is None:
            raise RuntimeError("Index not initialized.")

        normalized_query = np.array(normalize_embedding(vector), dtype="float32")
        if normalized_query.shape[0] != self._dimension:
            raise ValueError("Query vector dimension does not match the initialized index dimension.")

        matrix = np.array(self._vectors, dtype="float32")
        similarities = matrix @ normalized_query
        best_indices = np.argsort(similarities)[::-1][: min(top_k, len(self._vectors))]

        results: list[dict[str, Any]] = []
        for idx in best_indices:
            metadata = self._metadatas[idx]
            if filters and any(metadata.get(key) != value for key, value in filters.items()):
                continue
            results.append({
                "_id": self._ids[idx],
                "_score": float(similarities[idx]),
                **metadata,
            })
        return results

    async def delete(self, ids: list[str]) -> None:
        ids_to_remove = set(ids)
        if not ids_to_remove:
            return

        retained = [
            (item_id, vector, metadata)
            for item_id, vector, metadata in zip(self._ids, self._vectors, self._metadatas)
            if item_id not in ids_to_remove
        ]
        self._ids = [row[0] for row in retained]
        self._vectors = [row[1] for row in retained]
        self._metadatas = [row[2] for row in retained]
