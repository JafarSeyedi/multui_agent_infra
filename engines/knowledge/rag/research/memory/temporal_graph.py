# rag/research/graph/temporal_graph.py
from __future__ import annotations

import time


class TemporalGraph:

    def __init__(self) -> None:
        self.nodes: dict[str, float] = {}
        self.edges: list[dict] = []

    def add_entity(self, name: str):
        now = time.time()
        self.nodes[name] = now

    def add_relation(self, src, dst, relation):
        now = time.time()
        self.edges.append({
            "src": src,
            "dst": dst,
            "relation": relation,
            "timestamp": now
        })

    def recent_relations(self, window_seconds: int = 86400):
        now = time.time()
        return [
            e for e in self.edges
            if now - e["timestamp"] <= window_seconds
        ]
