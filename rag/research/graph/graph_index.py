from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Iterable, List, Set


@dataclass
class GraphNode:
    name: str
    type: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class GraphEdge:
    src: str
    dst: str
    relation: str
    confidence: float
    evidence_chunk: str
    timestamp: float = field(default_factory=time.time)


class GraphIndex:
    def __init__(self) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.adj: Dict[str, List[GraphEdge]] = defaultdict(list)

    def add_entities(self, entities: Iterable[GraphNode]) -> None:
        for entity in entities:
            key = entity.name.lower()
            existing = self.nodes.get(key)
            if existing is None or existing.type != entity.type:
                self.nodes[key] = GraphNode(name=entity.name, type=entity.type)

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
                src=src,
                dst=dst,
                relation=relation,
                confidence=confidence,
                evidence_chunk=evidence_chunk,
            )
        )

    def get_neighbors(self, entity: str, depth: int = 2) -> List[GraphEdge]:
        start = entity.lower()
        if start not in self.nodes:
            return []

        visited: Set[str] = {start}
        frontier: Deque[tuple[str, int]] = deque([(start, 0)])
        results: List[GraphEdge] = []

        while frontier:
            node, hop = frontier.popleft()
            if hop >= depth:
                continue
            for edge in self.adj.get(node, []):
                next_node = edge.dst.lower()
                results.append(edge)
                if next_node not in visited:
                    visited.add(next_node)
                    frontier.append((next_node, hop + 1))
        return results
