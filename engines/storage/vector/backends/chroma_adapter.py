# storage/vector/backends/chroma_adapter.py
from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import Metadata
from chromadb.config import Settings

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class ChromaAdapter(VectorDBAdapter):
    """Persistent Chroma adapter with a normalized result shape."""

    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents") -> None:
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True),
        )
        self.collection_name = collection_name
        self._collection: Collection | None = None  # ← fix: explicit type
        self._dimension: int | None = None

    def _sanitize_metadata(self, meta: dict[str, Any]) -> Metadata:
        """Convert metadata values to chromadb-compatible primitives."""
        result: dict[str, str | int | float | bool] = {}
        for k, v in meta.items():
            if isinstance(v, bool):
                result[k] = v
            elif isinstance(v, (int, float, str)):
                result[k] = v
            elif v is None:
                result[k] = ""        # chroma does not accept None
            else:
                result[k] = str(v)    # fallback for list, dict, etc.
        return result  # Dict[str, str|int|float|bool] is compatible with Metadata

    async def _get_or_create_collection(self, dimension: int) -> Collection:
        if self._collection is None:
            self._dimension = dimension
            try:
                self._collection = self.client.get_collection(name=self.collection_name)
            except Exception:
                self._collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    async def create_index(
        self,
        name: str,
        dimension: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.collection_name = name
        await self._get_or_create_collection(dimension=dimension)

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        if not ids:
            return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        collection = await self._get_or_create_collection(dimension=len(vectors[0]))
        normalized_vectors = [normalize_embedding(v) for v in vectors]
        sanitized = [self._sanitize_metadata(m) for m in metadata]
        collection.upsert(ids=ids, embeddings=normalized_vectors, metadatas=sanitized)

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
        if self._collection is None:
            raise RuntimeError("Collection not initialized. Call create_index or upsert first.")

        results = self._collection.query(
            query_embeddings=[normalize_embedding(vector)],
            where=filters,
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        formatted_results: list[dict[str, Any]] = []
        ids = results.get("ids", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        if not ids or not ids[0]:
            return formatted_results

        for idx, item_id in enumerate(ids[0]):
            meta = metadatas[0][idx] if metadatas and metadatas[0] else {}
            distance = distances[0][idx] if distances and distances[0] else None
            formatted_results.append(
                {
                    "_id": item_id,
                    "_score": 1.0 - float(distance) if distance is not None else 0.0,
                    **meta,
                }
            )
        return formatted_results

    async def delete(self, ids: list[str]) -> None:
        if self._collection is None or not ids:
            return
        self._collection.delete(ids=ids)
