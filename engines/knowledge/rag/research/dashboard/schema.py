from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class TokenUsage(BaseModel):
    module: str
    tokens: int = Field(ge=0)


class TokenBreakdownResponse(BaseModel):
    total_tokens: int = Field(ge=0)
    modules: list[TokenUsage]


class RetrievalChunkStat(BaseModel):
    chunk_id: str
    hits: int = Field(ge=0)


class RetrievalHeatmapResponse(BaseModel):
    chunks: list[RetrievalChunkStat]


class GraphPath(BaseModel):
    nodes: list[str]


class GraphPathsResponse(BaseModel):
    paths: list[GraphPath]


class FailureEvent(BaseModel):
    module: str
    error: str


class FailureResponse(BaseModel):
    failures: list[FailureEvent]


class MemoryUsageResponse(BaseModel):
    rss_bytes: int = Field(ge=0)


class TelemetryEventResponse(BaseModel):
    name: str
    payload: dict
    timestamp: float
