from __future__ import annotations

import time
from typing import List, Optional

from engines.rag.research.memory.memory_retriever import MemoryRetriever
from engines.rag.research.memory.memory_store import MemoryItem, MemoryStore
from engines.rag.research.memory.reasoning.event_types import ReasoningEventType
from engines.rag.research.memory.reasoning_memory import ReasoningMemory


class MemoryController:
    def __init__(
        self,
        memory_store: MemoryStore,
        memory_retriever: MemoryRetriever,
        reasoning_memory: Optional[ReasoningMemory] = None,
    ) -> None:
        self.store = memory_store
        self.retriever = memory_retriever
        self.reasoning = reasoning_memory or ReasoningMemory()

    def record(
        self,
        query: str,
        answer_summary: str,
        tags: Optional[List[str]] = None,
        timestamp: Optional[float] = None,
    ) -> MemoryItem:
        timestamp = time.time() if timestamp is None else timestamp
        tags = tags or []
        item = self.store.add(query=query, answer_summary=answer_summary, tags=tags, timestamp=timestamp)
        self.reasoning.log(ReasoningEventType.MEMORY_STORE, "Research result stored", meta={"query": query})
        return item

    def recall(self, query: str, limit: int = 5) -> List[MemoryItem]:
        results = self.retriever.retrieve_similar(query, limit=limit)
        self.reasoning.log(
            ReasoningEventType.MEMORY_RECALL,
            f"Retrieved {len(results)} related memories",
            meta={"query": query, "limit": limit},
        )
        return results

    def reasoning_trace(self):
        return self.reasoning.dump()

    def stats(self) -> dict:
        return {"total_memories": len(self.store.all())}
