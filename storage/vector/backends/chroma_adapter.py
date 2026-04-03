from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class ChromaAdapter(VectorDBAdapter):
    """Persistent Chroma adapter with a normalized result shape."""

    def __init__(self, db_path: str = "./chroma_db", collection_name: str = "documents"):
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True),
        )
        self.collection_name = collection_name
        self._collection = None
        self._dimension: Optional[int] = None

    async def _get_or_create_collection(self, dimension: int):
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
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.collection_name = name
        await self._get_or_create_collection(dimension=dimension)

    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        collection = await self._get_or_create_collection(dimension=len(vectors[0]))
        normalized_vectors = [normalize_embedding(v) for v in vectors]
        collection.upsert(ids=ids, embeddings=normalized_vectors, metadatas=metadata)

    async def batch_upsert(self, items: List[Dict[str, Any]]) -> None:
        if not items:
            return
        await self.upsert(
            ids=[item["id"] for item in items],
            vectors=[item["vector"] for item in items],
            metadata=[item["metadata"] for item in items],
        )

    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if self._collection is None:
            raise RuntimeError("Collection not initialized. Call create_index or upsert first.")

        results = self._collection.query(
            query_embeddings=[normalize_embedding(vector)],
            where=filters,
            n_results=top_k,
            include=["metadatas", "distances"],
        )

        formatted_results: List[Dict[str, Any]] = []
        ids = results.get("ids", [[]])
        metadatas = results.get("metadatas", [[]])
        distances = results.get("distances", [[]])
        if not ids or not ids[0]:
            return formatted_results

        for idx, item_id in enumerate(ids[0]):
            metadata = metadatas[0][idx] if metadatas and metadatas[0] else {}
            distance = distances[0][idx] if distances and distances[0] else None
            formatted_results.append(
                {
                    "_id": item_id,
                    "_score": 1.0 - float(distance) if distance is not None else 0.0,
                    **metadata,
                }
            )
        return formatted_results

    async def delete(self, ids: List[str]) -> None:
        if self._collection is None or not ids:
            return
        self._collection.delete(ids=ids)
