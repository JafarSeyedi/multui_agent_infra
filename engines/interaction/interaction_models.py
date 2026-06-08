# agents/interaction/interaction_models.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from engines.communication.buses.message_models import AgentMessage
from ..agent.base_agents.base_agent import BaseAgent

from ..agent.models import AgentOutput


class InteractionRequest(BaseModel):
    """Main input to InteractionAgent"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario: str = "pipeline"
    agents: list[BaseAgent]

    # Common context for all strategies
    context: dict[str, Any] = Field(default_factory=dict)

    # Supplementary metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

class InteractionResult(BaseModel):
    """Complete orchestration output"""
    workflow_id: str | None = None
    scenario: str | None = None

    results: list[AgentOutput]
    success: bool = True

    # Final context updated by strategies
    final_context: dict[str, Any] = Field(default_factory=dict)

    # Execution tracking
    backend_used: str = "native"
    status: Literal["success", "partial", "failed"] = "success"
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Notes and logs
    notes: list[str] = Field(default_factory=list)

    metadata: dict[str, Any] = Field(default_factory=dict)