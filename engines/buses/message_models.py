from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class AgentMessage(BaseModel):
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
