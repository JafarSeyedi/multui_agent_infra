# rag/research/memory/memory_store.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict


@dataclass(slots=True)
class MemoryItem:
    id: int
    query: str
    answer_summary: str
    timestamp: float
    tags: List[str]


class MemoryStore:

    def __init__(self) -> None:
        self._items: Dict[int, MemoryItem] = {}
        self._next_id = 1

    def add(self, query: str, answer_summary: str, tags: List[str], timestamp: float):
        mid = self._next_id
        self._next_id += 1

        m = MemoryItem(
            id=mid,
            query=query,
            answer_summary=answer_summary,
            tags=tags,
            timestamp=timestamp
        )

        self._items[mid] = m
        return m

    def all(self):
        return list(self._items.values())
