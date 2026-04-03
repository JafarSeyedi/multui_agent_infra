from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentExecutionRecord(BaseModel):
    execution_id: str
    agent_name: str
    agent_version: str
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]] = None
    status: str
    execution_time_ms: int
    error_message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskExecutionRecord(BaseModel):
    task_id: str
    task_name: str
    executor: str
    status: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    output_payload: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionRecord(BaseModel):
    workflow_id: str
    agents_executed: List[str]
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
