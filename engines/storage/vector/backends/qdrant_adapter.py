# storage/vector/backends/qdrant_adapter.py
from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from qdrant_client import models
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class QdrantAdapter(VectorDBAdapter):
    """Adapter for Qdrant vector database."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection_name: str = "documents",
    ) -> None:
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self._dimension: int = 0

    async def create_index(
        self,
        name: str,
        dimension: int,
        config: dict[str, Any] | None = None,
    ) -> None:
        """Creates or recreates a Qdrant collection."""
        self.collection_name = name
        self._dimension = dimension

        hnsw_config = (
            models.HnswConfigDiff(
                m=int(config.get("m", 16)),
                ef_construct=int(config.get("ef_construction", 200)),
            )
            if config
            else None
        )

        vector_params = models.VectorParams(
            size=dimension,
            distance=models.Distance.COSINE,
        )

        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=vector_params,
            hnsw_config=hnsw_config,
        )
        print(
            f"QdrantAdapter: Collection '{self.collection_name}' "
            f"recreated with dimension {dimension}."
        )

    async def upsert(
        self,
        ids: list[str],
        vectors: list[list[float]],
        metadata: list[dict[str, Any]],
    ) -> None:
        """Upserts points into the Qdrant collection."""
        if not ids:
            return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("Length of ids, vectors, and metadata must match.")

        normalized_vectors = [normalize_embedding(v) for v in vectors]

        points = [
            models.PointStruct(
                id=ids[i],
                vector=normalized_vectors[i],
                payload=dict(metadata[i]),
            )
            for i in range(len(ids))
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points,
        )
        print(
            f"QdrantAdapter: Upserted {len(ids)} items "
            f"into collection '{self.collection_name}'."
        )

    async def batch_upsert(self, items: list[dict[str, Any]]) -> None:
        """Upserts items in batches."""
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
        """Queries the Qdrant collection for nearest neighbours."""
        normalized_query_vector = normalize_embedding(vector)

        qdrant_filter: models.Filter | None = None
        if filters:
            filter_conditions: list[models.FieldCondition] = []

            for key, value in filters.items():
                # ── Note: bool must be checked before int ──
                # Because bool is a subclass of int and isinstance(True, int) → True
                if isinstance(value, bool):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),  # bool مجاز است
                        )
                    )
                elif isinstance(value, int):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),  # int مجاز است
                        )
                    )
                elif isinstance(value, float):
                    # ── FIX خطا ۱: float در MatchValue مجاز نیست → Range ──
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            range=models.Range(gte=value, lte=value),
                        )
                    )
                elif isinstance(value, str):
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value),  # str مجاز است
                        )
                    )
                elif isinstance(value, dict):
                    # فیلتر range صریح: {"gte": 0.5, "lte": 0.9}
                    filter_conditions.append(
                        models.FieldCondition(
                            key=key,
                            range=models.Range(
                                gte=value.get("gte"),
                                lte=value.get("lte"),
                                gt=value.get("gt"),
                                lt=value.get("lt"),
                            ),
                        )
                    )

            if filter_conditions:
                # ── FIX خطا ۲: cast به Sequence برای رفع invariance ──
                must_seq: Sequence[models.FieldCondition] = filter_conditions
                qdrant_filter = models.Filter(must=must_seq)  # type: ignore[arg-type]

        try:
            # ── FIX خطا ۳: جایگزینی client.search با client.query_points ──
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=normalized_query_vector,
                limit=top_k,
                query_filter=qdrant_filter,
                with_payload=True,
            )
        except Exception as e:
            print(f"QdrantAdapter: Error during query: {e}")
            return []

        formatted_results: list[dict[str, Any]] = []
        raw_points = (
            search_result.points
            if hasattr(search_result, "points")
            else search_result
        )

        for hit in raw_points:
            if not isinstance(hit, ScoredPoint):
                continue  # tuple یا موارد غیرمنتظره را رد کن

            payload = hit.payload or {}
            formatted_results.append(
                {
                    "_id": hit.id,
                    "_score": hit.score,
                    **payload,
                }
            )
        return formatted_results

    async def delete(self, ids: list[str]) -> None:
        """Deletes points by their IDs."""
        if not ids:
            return

        try:
            # ── FIX خطا ۴: جایگزینی PointSelector با PointIdsList ──
            self.client.delete(
                collection_name=self.collection_name,
                wait=True,
                points_selector=models.PointIdsList(points=ids),  # type: ignore[arg-type]
            )
            print(
                f"QdrantAdapter: Deleted {len(ids)} items "
                f"from collection '{self.collection_name}'."
            )
        except Exception as e:
            print(f"QdrantAdapter: Error deleting items: {e}")
