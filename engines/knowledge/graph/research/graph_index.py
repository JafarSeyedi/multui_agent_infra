from __future__ import annotations

import time
from collections import defaultdict
from collections import deque
from collections.abc import Iterable
from typing import Deque

from engines.document.models.ksdm_models import GraphNode, GraphEdge


class GraphIndex:
    def __init__(self) -> None:
        self.nodes: dict[str, GraphNode] = {}
        self.adj: dict[str, list[GraphEdge]] = defaultdict(list)

    def add_entities(self, entities: Iterable[GraphNode]) -> None:
        for entity in entities:
            key = entity.id.lower()
            existing = self.nodes.get(key)
            if existing is None or existing.type != entity.type:
                self.nodes[key] = GraphNode(
                    id=entity.id,
                    label=entity.label,
                    type=entity.type,
                    timestamp=entity.timestamp or time.time(),
                )

    def add_relation(
        self,
        src: str,
        dst: str,
        relation: str,
        confidence: float,
        evidence_chunk: str,
    ) -> None:
        src_key = src.lower()
        dst_key = dst.lower()
        if src_key not in self.nodes or dst_key not in self.nodes:
            return
        self.adj[src_key].append(
            GraphEdge(
                source=src,
                target=dst,
                relation=relation,
                confidence=confidence,
                evidence_chunk=evidence_chunk,
                timestamp=time.time(),
            )
        )

    def get_neighbors(self, entity: str, depth: int = 2) -> list[GraphEdge]:
        start = entity.lower()
        if start not in self.nodes:
            return []

        visited: set[str] = {start}
        frontier: Deque[tuple[str, int]] = deque([(start, 0)])
        results: list[GraphEdge] = []

        while frontier:
            node, hop = frontier.popleft()
            if hop >= depth:
                continue
            for edge in self.adj.get(node, []):
                next_node = edge.target.lower()
                results.append(edge)
                if next_node not in visited:
                    visited.add(next_node)
                    frontier.append((next_node, hop + 1))
        return results
