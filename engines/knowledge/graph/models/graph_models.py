from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    url: str | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    timestamp: float | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: float | None = None
    evidence_chunk: str | None = None
    timestamp: float | None = None


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
