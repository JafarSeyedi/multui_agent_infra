from __future__ import annotations

from typing import Any, List

from rag.research.memory.reasoning.event_types import ReasoningEventType
from rag.research.memory.reasoning_memory import ReasoningMemory


class GraphRetriever:
    def __init__(self, graph_store: Any, reasoning: ReasoningMemory | None = None):
        self.store = graph_store
        self.reasoning = reasoning or ReasoningMemory()
        self.link_strengths = {}

    async def retrieve(self, entity_id: str, hops: int = 2):
        visited = set()
        frontier = [entity_id]
        results: List[Any] = []

        for hop in range(hops):
            new_frontier = []
            for node_id in frontier:
                if node_id in visited:
                    continue
                visited.add(node_id)
                neighbors = await self.store.neighbors(node_id)
                for neighbor in neighbors:
                    results.append(neighbor)
                    new_frontier.append(neighbor.id)
                    self.link_strengths[str(getattr(neighbor, "id", ""))] = float(
                        getattr(neighbor, "score", getattr(neighbor, "weight", 1.0))
                    )
            frontier = new_frontier
            self.reasoning.log(
                ReasoningEventType.GRAPH_TRAVERSAL,
                f"Graph traversal executed for hop {hop + 1}",
                meta={"hops": hop + 1, "frontier_size": len(frontier)},
            )
            if not frontier:
                break
        return results

    async def search(self, query: str, top_k: int = 5):
        return (await self.retrieve(query, hops=1))[:top_k]
