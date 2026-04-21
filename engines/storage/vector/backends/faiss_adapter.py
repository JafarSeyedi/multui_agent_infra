# storage/vector/backends/faiss_adapter.py

import faiss # type: ignore[import-untyped, import-not-found]
import numpy as np
from typing import List, Dict, Any, Optional

from ..base import VectorDBAdapter
from ..embedding_utils import normalize_embedding


class FaissAdapter(VectorDBAdapter):
    """
    FAISS vector database adapter.

    Designed for:
    - Local high performance retrieval
    - Large scale embeddings
    - Offline RAG systems
    """

    def __init__(self) -> None:
        self.index: Optional[Any] = None
        self.dimension: Optional[int] = None

        self.id_map: Dict[int, str] = {}
        self.metadata_store: Dict[str, Dict[str, Any]] = {}

        self._next_internal_id: int = 0

    async def create_index(
        self,
        name: str,
        dimension: int,
        config: Optional[Dict[str, Any]] = None
    ) -> None:

        self.dimension = dimension

        index_type = "flat"

        if config and "type" in config:
            index_type = config["type"]

        if index_type == "ivf":

            if config:
                nlist = config.get("nlist", 100)

            quantizer = faiss.IndexFlatIP(dimension)

            index = faiss.IndexIVFFlat(
                quantizer,
                dimension,
                nlist,
                faiss.METRIC_INNER_PRODUCT
            )

        else:

            index = faiss.IndexFlatIP(dimension)

        self.index = index

        print(f"FAISS index created (type={index_type}, dim={dimension})")

    async def upsert(
        self,
        ids: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> None:

        if self.index is None:
            raise RuntimeError("Index not initialized")

        if len(ids) != len(vectors):
            raise ValueError("IDs and vectors mismatch")

        vectors_list: List[Any] = []
        for v in vectors:
            vec = normalize_embedding(v)
            vectors_list.append(vec)
        vectors_np = np.array(vectors_list).astype("float32")

        internal_ids = []

        for i, external_id in enumerate(ids):

            internal_id = self._next_internal_id
            self._next_internal_id += 1

            self.id_map[internal_id] = external_id
            self.metadata_store[external_id] = metadata[i]

            internal_ids.append(internal_id)

        internal_ids_np = np.array(internal_ids)

        if isinstance(self.index, faiss.IndexIVFFlat) and not self.index.is_trained:
            self.index.train(vectors_np)

        self.index.add_with_ids(vectors_np, internal_ids_np)

    async def batch_upsert(
        self,
        items: List[Dict[str, Any]]
    ) -> None:

        ids = [x["id"] for x in items]
        vectors = [x["vector"] for x in items]
        metadata = [x["metadata"] for x in items]

        await self.upsert(ids, vectors, metadata)

    async def query(
        self,
        vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:

        if self.index is None:
            raise RuntimeError("Index not initialized")

        vec = normalize_embedding(vector)

        vec = np.array([vec]).astype("float32")

        scores, ids = self.index.search(vec, top_k)

        results = []

        for score, internal_id in zip(scores[0], ids[0]):

            if internal_id == -1:
                continue

            external_id = self.id_map.get(int(internal_id))
            if external_id is None:
                continue

            meta = self.metadata_store.get(external_id, {})

            if filters:
                match = all(meta.get(k) == v for k, v in filters.items())
                if not match:
                    continue

            results.append({"_id": external_id, "_score": float(score), **meta})
            
        return results

    async def delete(self, ids: List[str]) -> None:

        if self.index is None:
            return

        reverse_map = {v: k for k, v in self.id_map.items()}

        remove_ids = []

        for external_id in ids:

            internal_id = reverse_map.get(external_id)

            if internal_id is not None:
                remove_ids.append(internal_id)

                self.metadata_store.pop(external_id, None)

        if not remove_ids:
            return

        remove_ids_np = np.array(remove_ids)

        self.index.remove_ids(remove_ids_np)

        for iid in remove_ids:
            self.id_map.pop(iid, None)

        print(f"FAISS deleted {len(remove_ids)} vectors")
