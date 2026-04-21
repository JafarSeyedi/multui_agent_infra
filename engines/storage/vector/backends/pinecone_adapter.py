# storage/vector/backends/pinecone_adapter.py

from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class PineconeAdapter(VectorDBAdapter):
    """
    Adapter for Pinecone v3+ API.
    Uses the new Pinecone client instead of the deprecated pinecone.init() approach.
    """

    def __init__(
        self,
        api_key: str,
        environment: str,
        index_name: str = "documents",
        dimension: int = 1536,
        metric: str = "cosine",
    ) -> None:
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self._dimension = dimension
        self._metric = metric.lower()
        self._client: Pinecone = Pinecone(api_key=self.api_key)
        self._index = self._initialize_connection()

    def _initialize_connection(self):
        """Connects to the specified Pinecone index if it exists."""
        try:
            existing = [idx.name for idx in self._client.list_indexes()]
            if self.index_name in existing:
                index = self._client.Index(self.index_name)
                print(f"PineconeAdapter: Connected to index '{self.index_name}'.")
                return index
            else:
                print(f"PineconeAdapter: Index '{self.index_name}' not found. Call create_index() first.")
                return None
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to Pinecone index '{self.index_name}': {e}"
            )

    async def create_index(
        self, name: str, dimension: int, config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Creates a Pinecone index if it doesn't exist, then connects to it."""
        self.index_name = name
        self._dimension = dimension
        if config and "metric" in config:
            self._metric = config["metric"].lower()

        existing = [idx.name for idx in self._client.list_indexes()]

        if name not in existing:
            print(f"PineconeAdapter: Creating index '{name}'...")
            cloud = config.get("cloud", "aws") if config else "aws"
            region = config.get("region", self.environment) if config else self.environment

            self._client.create_index(
                name=name,
                dimension=self._dimension,
                metric=self._metric,
                spec=ServerlessSpec(cloud=cloud, region=region),
            )
            print(
                f"PineconeAdapter: Index '{name}' created "
                f"(dim={self._dimension}, metric='{self._metric}')."
            )
        else:
            print(f"PineconeAdapter: Index '{name}' already exists.")

        self._index = self._client.Index(name)

    def _require_index(self):
        """Raises if the index handle is not initialized."""
        if self._index is None:
            raise RuntimeError(
                f"Pinecone index '{self.index_name}' is not initialized. "
                "Call create_index() first."
            )

    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
    ) -> None:
        """Upserts vectors with metadata into the Pinecone index."""
        if not ids:
            return
        if len(ids) != len(vectors) or len(ids) != len(metadata):
            raise ValueError("ids, vectors, and metadata must have the same length.")

        self._require_index()

        normalized = [normalize_embedding(v) for v in vectors]
        # Pinecone v3 upsert format: list of dicts with 'id', 'values', 'metadata'
        records = [
            {"id": i, "values": v, "metadata": m}
            for i, v, m in zip(ids, normalized, metadata)
        ]

        batch_size = 100
        for start in range(0, len(records), batch_size):
            batch = records[start : start + batch_size]
            try:
                self._index.upsert(vectors=batch)
            except Exception as e:
                print(f"PineconeAdapter: Batch upsert error (batch {start // batch_size}): {e}")

        print(f"PineconeAdapter: Upserted {len(ids)} items into '{self.index_name}'.")

    async def batch_upsert(self, items: List[Dict[str, Any]]) -> None:
        """Upserts a list of dicts with 'id', 'vector', 'metadata' keys."""
        if not items:
            return
        ids = [item["id"] for item in items]
        vectors = [item["vector"] for item in items]
        metadatas = [item["metadata"] for item in items]
        await self.upsert(ids, vectors, metadatas)

    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Queries the Pinecone index for nearest neighbours."""
        self._require_index()

        normalized = normalize_embedding(vector)

        # Build Pinecone filter (metadata filter syntax)
        pinecone_filter = None
        if filters:
            pinecone_filter = {}
            for key, value in filters.items():
                if isinstance(value, dict):
                    # e.g. {"score": {"gt": 0.8}} -> {"score": {"$gt": 0.8}}
                    pinecone_filter[key] = {f"${op}": val for op, val in value.items()}
                else:
                    pinecone_filter[key] = {"$eq": value}

        try:
            results = self._index.query(
                vector=normalized,
                top_k=top_k,
                include_metadata=True,
                filter=pinecone_filter,
            )
        except Exception as e:
            print(f"PineconeAdapter: Query error: {e}")
            return []

        formatted: List[Dict[str, Any]] = []
        for match in results.get("matches", []):
            meta = match.get("metadata") or {}
            formatted.append(
                {"_id": match.get("id"), "_score": match.get("score"), **meta}
            )
        return formatted

    async def delete(self, ids: List[str]) -> None:
        """Deletes vectors by ID from the Pinecone index."""
        if not ids:
            return

        self._require_index()

        try:
            self._index.delete(ids=ids)
            print(f"PineconeAdapter: Deleted {len(ids)} items from '{self.index_name}'.")
        except Exception as e:
            print(f"PineconeAdapter: Delete error: {e}")
