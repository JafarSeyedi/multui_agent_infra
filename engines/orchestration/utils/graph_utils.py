"""Graph utilities for process/state navigation and validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, TypeVar

NodeId = TypeVar("NodeId", bound=str)


@dataclass(frozen=True)
class GraphNode:
    """Directed graph node."""

    node_id: str
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class Edge:
    """Directed graph edge."""

    source: str
    target: str
    condition: str | None = None


def _build_index(edges: Iterable[Edge]) -> tuple[dict[str, list[Edge]], dict[str, int]]:
    adjacency: dict[str, list[Edge]] = {}
    indegree: dict[str, int] = {}
    for edge in edges:
        adjacency.setdefault(edge.source, []).append(edge)
        indegree.setdefault(edge.source, 0)
        indegree[edge.target] = indegree.get(edge.target, 0) + 1
        if edge.target not in adjacency:
            adjacency[edge.target] = []
    return adjacency, indegree


def topological_sort(nodes: Iterable[GraphNode], edges: Iterable[Edge]) -> list[str]:
    """Return nodes in topological order; raises on cycles."""
    node_ids = {node.node_id for node in nodes}
    adjacency, indegree = _build_index(edges)
    queue = [node_id for node_id in node_ids if indegree.get(node_id, 0) == 0]
    result: list[str] = []

    while queue:
        node_id = queue.pop()
        result.append(node_id)
        for edge in adjacency.get(node_id, []):
            indegree[edge.target] -= 1
            if indegree[edge.target] == 0:
                queue.append(edge.target)

    if len(result) != len(node_ids):
        raise ValueError("Cycle detected in graph")
    return result


def has_cycle(nodes: Iterable[GraphNode], edges: Iterable[Edge]) -> bool:
    """Check if directed graph has a cycle."""
    try:
        topological_sort(nodes, edges)
        return False
    except ValueError:
        return True


def shortest_path(nodes: Iterable[GraphNode], edges: Iterable[Edge], start: str, end: str) -> list[str]:
    """Find shortest path via BFS on an unweighted graph."""
    adjacency, _ = _build_index(edges)
    available = {node.node_id for node in nodes}
    if start not in available or end not in available:
        return []

    queue = [(start, [start])]
    seen = {start}

    while queue:
        current, path = queue.pop(0)
        if current == end:
            return path
        for edge in adjacency.get(current, []):
            nxt = edge.target
            if nxt in seen:
                continue
            seen.add(nxt)
            queue.append((nxt, path + [nxt]))
    return []
