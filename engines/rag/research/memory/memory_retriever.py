# rag/research/memory/memory_retriever.py
from __future__ import annotations

import math
from typing import List
from engines.rag.research.memory.memory_store import MemoryStore, MemoryItem


class MemoryRetriever:

    def __init__(self, store: MemoryStore):
        self.store = store

    def retrieve_similar(self, query: str, limit: int = 5) -> List[MemoryItem]:

        scored = []

        for item in self.store.all():

            overlap = self._token_overlap(query, item.query)
            recency = self._recency_weight(item.timestamp)

            score = 0.7 * overlap + 0.3 * recency

            if score > 0.1:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [x[1] for x in scored[:limit]]

    def _token_overlap(self, q1, q2):
        s1 = set(q1.lower().split())
        s2 = set(q2.lower().split())
        return len(s1 & s2) / max(1, len(s1 | s2))

    def _recency_weight(self, ts):
        return 1 / (1 + math.exp(-0.00001 * ts))
