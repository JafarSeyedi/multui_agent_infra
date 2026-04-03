from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict


class AgentInteraction(BaseModel):

    interaction_id: str

    user_id: Optional[str]

    agent_name: str

    request: Dict
    response: Optional[Dict]

    timestamp: datetime

class ConversationTurn(BaseModel):

    conversation_id: str

    speaker: str  # user | agent | system

    message: str

    metadata: Optional[Dict]

    timestamp: datetime

