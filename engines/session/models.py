from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventActions(BaseModel):
    state_delta: dict[str, Any] = Field(default_factory=dict)
    artifact_delta: dict[str, Any] = Field(default_factory=dict)
    skip_summarization: bool = False


class Event(BaseModel):
    id: str = ""
    invocation_id: str = ""
    author: str = "user"
    content: dict[str, Any] | None = None
    actions: EventActions = Field(default_factory=EventActions)
    timestamp: datetime = Field(default_factory=_utcnow)


class Session(BaseModel):
    id: str
    app_name: str
    user_id: str
    session_id: str
    state: dict[str, Any] = Field(default_factory=dict)
    events: list[Event] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
