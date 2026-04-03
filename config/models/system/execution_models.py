from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime


class AgentExecutionRecord(BaseModel):

    execution_id: str

    agent_name: str
    agent_version: str

    input_payload: Dict
    output_payload: Optional[Dict]

    status: str  # success | failure

    execution_time_ms: int

    error_message: Optional[str]

    timestamp: datetime

class WorkflowExecutionRecord(BaseModel):

    workflow_id: str

    agents_executed: list[str]

    status: str

    start_time: datetime
    end_time: Optional[datetime]

    metadata: Optional[Dict]
