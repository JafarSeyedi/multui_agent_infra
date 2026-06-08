# agents/agent_definition_models.py
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Avoid circular import by using string annotation for StateMachineDocument
# from engines.document.models.osdm_models import StateMachineDocument


class AgentType(str, Enum):
    INTERACTION = "interaction_agent"
    SKILL = "skill_call_agent"
    STATE_MACHINE = "state_machine_agent"


class AgentDefinition(BaseModel):
    """Definition of an agent, used to instantiate agent instances."""
    name: str = Field(..., description="Unique name of the agent")
    description: str = Field(..., description="Human-readable description of the agent")
    type: AgentType = Field(..., description="Type of agent")
    # For SKILL type: the skill identifier (relative path to SKILL.md)
    skill_id: Optional[str] = Field(
        None,
        description="For skill_call_agent: the skill identifier (relative path to SKILL.md)"
    )
    # For STATE_MACHINE type: the state machine definition
    state_machine: Optional[Any] = Field(  # We'll use Any to avoid importing StateMachineDocument
        None,
        description="For state_machine_agent: the state machine definition that orchestrates skills"
    )
    # Optional configuration
    config: dict[str, Any] = Field(default_factory=dict, description="Additional agent-specific configuration")


# Existing models for runtime messaging (kept for compatibility)
class AgentInput(BaseModel):
    agent_name: str

    # Main message or Objective
    message: str | None = None

    # Structured inputs
    payload: dict[str, Any] = Field(default_factory=dict)

    # Shared context
    context: dict[str, Any] = Field(default_factory=dict)

    # Additional information → tracing, routing, strategy, priority
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    agent_id: str | None = None
    agent_name: str

    # Agent's main output (LLM response or processing result)
    message: str | None = None

    # Structured output
    payload: dict[str, Any] = Field(default_factory=dict)

    # Error (if any)
    error: str | None = None

    # For orchestration and tracing
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentExecutionRecord(BaseModel):
    execution_id: str
    agent_name: str
    agent_version: str
    input_payload: dict[str, Any]
    output_payload: dict[str, Any] | None = None
    status: str
    execution_time_ms: int
    error_message: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
