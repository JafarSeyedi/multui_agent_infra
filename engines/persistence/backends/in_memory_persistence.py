# engines/persistence/backends/in_memory_persistence.py
from __future__ import annotations

import math
from typing import Any, Optional

from ..plugin import IVectorStore, IBlobStorage


class InMemoryVectorStore(IVectorStore):
    name = "in_memory"

    def __init__(self) -> None:
        self._collections: dict[str, dict[str, dict[str, Any]]] = {}

    async def upsert(self, collection: str, id: str, vector: list[float], metadata: dict[str, Any]) -> None:
        if collection not in self._collections:
            self._collections[collection] = {}
        self._collections[collection][id] = {"vector": vector, "metadata": metadata}

    async def search(self, collection: str, query: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        if collection not in self._collections:
            return []
        scored: list[tuple[float, str, dict]] = []
        for id, rec in self._collections[collection].items():
            score = _cosine_similarity(query, rec["vector"])
            scored.append((score, id, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {"id": sid, "score": s, "metadata": r["metadata"]}
            for s, sid, r in scored[:top_k]
        ]

    async def delete(self, collection: str, id: str) -> None:
        if collection in self._collections:
            self._collections[collection].pop(id, None)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryBlobStorage(IBlobStorage):
    name = "in_memory"

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def upload(self, path: str, data: bytes) -> str:
        self._store[path] = data
        return path

    async def download(self, path: str) -> Optional[bytes]:
        return self._store.get(path)

    async def delete(self, path: str) -> None:
        self._store.pop(path, None)
