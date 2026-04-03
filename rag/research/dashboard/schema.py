from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    module: str
    tokens: int = Field(ge=0)


class TokenBreakdownResponse(BaseModel):
    total_tokens: int = Field(ge=0)
    modules: List[TokenUsage]


class RetrievalChunkStat(BaseModel):
    chunk_id: str
    hits: int = Field(ge=0)


class RetrievalHeatmapResponse(BaseModel):
    chunks: List[RetrievalChunkStat]


class GraphPath(BaseModel):
    nodes: List[str]


class GraphPathsResponse(BaseModel):
    paths: List[GraphPath]


class FailureEvent(BaseModel):
    module: str
    error: str


class FailureResponse(BaseModel):
    failures: List[FailureEvent]


class MemoryUsageResponse(BaseModel):
    rss_bytes: int = Field(ge=0)


class TelemetryEventResponse(BaseModel):
    name: str
    payload: dict
    timestamp: float
