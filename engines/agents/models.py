# agents/agent_base_models.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import Field


# message = natural data (like user message or query)
# message for human readable
# payload for machine reading
# payload = structured data Agent-specific like:
#   - search_query
#   - doc_ids
#   - intermediate_results
#   - extracted_features
# context = shared context between all agents (related to orchestration)
# metadata = tracing / routing / meta info internal info (e.g. trace_id, retry, priority)

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

# agent can return both text and data
# your program never crashes because it always has a fixed structure
# subclasses can enrich the payload
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
