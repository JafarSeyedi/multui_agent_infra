# storage/vector/backends/weaviate_adapter.py

from __future__ import annotations

import json
import asyncio
from typing import Any, Dict, List, Optional

import weaviate
import weaviate.classes as wvc
from weaviate.auth import AuthApiKey

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class WeaviateAdapter(VectorDBAdapter):
    """Adapter for Weaviate v4 client API."""

    def __init__(
        self,
        url: str = "http://localhost:8080",
        api_key: Optional[str] = None,
        class_name: str = "Document",
        dim: int = 1536,
    ) -> None:
        auth = AuthApiKey(api_key) if api_key else None

        self.client = weaviate.connect_to_custom(
            http_host=url.replace("http://", "").replace("https://", "").split(":")[0],
            http_port=int(url.split(":")[-1]) if ":" in url.split("//")[-1] else 8080,
            http_secure=url.startswith("https"),
            grpc_host=url.replace("http://", "").replace("https://", "").split(":")[0],
            grpc_port=50051,
            grpc_secure=False,
            auth_credentials=auth,
        )
        self.class_name = class_name
        self._dimension = dim

    async def _get_or_create_collection(self) -> Any:
        """Ensures the Weaviate collection exists."""
        def _sync() -> Any:
            if self.client.collections.exists(self.class_name):
                return self.client.collections.get(self.class_name)
            return self.client.collections.create(
                name=self.class_name,
                vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                    distance_metric=wvc.config.VectorDistances.COSINE,
                ),
                properties=[
                    wvc.config.Property(
                        name="metadata",
                        data_type=wvc.config.DataType.TEXT,
                    ),
                ],
            )

        return await asyncio.to_thread(_sync)

    async def create_index(
        self, name: str, dimension: int, config: Optional[Dict] = None
    ) -> None:
        self.class_name = name
        self._dimension = dimension
        await self._get_or_create_collection()

    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict],
    ) -> None:
        if not ids:
            return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        collection = await self._get_or_create_collection()
        normalized = [normalize_embedding(v) for v in vectors]

        def _sync() -> None:
            with collection.batch.dynamic() as batch:
                for uid, vec, meta in zip(ids, normalized, metadata):
                    batch.add_object(
                        properties={"metadata": json.dumps(meta)},
                        uuid=uid,
                        vector=vec,
                    )

        await asyncio.to_thread(_sync)

    async def batch_upsert(self, items: List[Dict]) -> None:
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
    ) -> List[Dict]:
        collection = await self._get_or_create_collection()
        normalized = normalize_embedding(vector)

        def _sync() -> List[Dict]:
            response = collection.query.near_vector(
                near_vector=normalized,
                limit=top_k,
                return_metadata=wvc.query.MetadataQuery(distance=True),
            )
            results = []
            for obj in response.objects:
                meta = json.loads(obj.properties.get("metadata", "{}"))
                distance = obj.metadata.distance if obj.metadata else None
                results.append({
                    "_id": str(obj.uuid),
                    "_score": 1.0 - distance if distance is not None else None,
                    **meta,
                })
            return results

        return await asyncio.to_thread(_sync)

    async def delete(self, ids: List[str]) -> None:
        if not ids:
            return
        collection = await self._get_or_create_collection()

        def _sync() -> None:
            for uid in ids:
                collection.data.delete_by_id(uid)

        await asyncio.to_thread(_sync)

    def close(self) -> None:
        """باید در پایان کار فراخوانی شود."""
        self.client.close()
