from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    message_id: str
    sender: str
    recipient: str
    message_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PipelineStep(BaseModel):
    step_id: str
    pipeline_name: str
    step_name: str
    sequence: int
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentInteraction(BaseModel):
    interaction_id: str
    user_id: Optional[str] = None
    agent_name: str
    request: Dict[str, Any] = Field(default_factory=dict)
    response: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationTurn(BaseModel):
    conversation_id: str
    speaker: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
