from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class PipelineEvent(BaseModel):
    event_id: str
    pipeline_name: str
    step_name: str
    status: Literal["started", "running", "completed", "failed", "skipped"]
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StudentStateEvent(BaseModel):
    event_id: str
    student_id: str
    state_type: Literal["engagement", "mastery", "frustration", "progress", "preference"]
    previous_state: Optional[Dict[str, Any]] = None
    current_state: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RuntimeErrorLog(BaseModel):
    error_id: str
    component: str
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MemorySnapshot(BaseModel):
    snapshot_id: str
    memory_scope: Literal["short_term", "long_term", "working", "episodic"]
    owner_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    summary: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemEvent(BaseModel):
    event_id: str
    event_type: str
    source: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
