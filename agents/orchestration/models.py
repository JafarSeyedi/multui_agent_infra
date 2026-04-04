from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from config.models.system.interaction_models import AgentMessage, PipelineStep


ScenarioType = Literal[
    "sequential",
    "broadcast",
    "round_robin",
    "selector",
    "group_chat",
]

BackendType = Literal["native", "autogen", "auto"]


class OrchestrationTask(BaseModel):
    agent_name: str
    input_payload: Dict[str, Any] = Field(default_factory=dict)
    task_id: Optional[str] = None
    description: Optional[str] = None
    depends_on: List[str] = []


class OrchestrationRequest(BaseModel):
    workflow_id: str
    scenario: ScenarioType = "sequential"
    backend: BackendType = "auto"
    tasks: List[OrchestrationTask]
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    max_rounds: int = 3
    selected_agent: Optional[str] = None
    autogen_config: Dict[str, Any] = Field(default_factory=dict)


class OrchestrationExecution(BaseModel):
    task_id: str
    agent_name: str
    status: Literal["success", "failure", "skipped"]
    output_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class OrchestrationResult(BaseModel):
    workflow_id: str
    scenario: ScenarioType
    backend_used: str
    status: Literal["success", "partial_success", "failure"]
    started_at: datetime
    completed_at: datetime
    shared_context: Dict[str, Any] = Field(default_factory=dict)
    steps: List[PipelineStep] = Field(default_factory=list)
    executions: List[OrchestrationExecution] = Field(default_factory=list)
    messages: List[AgentMessage] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
