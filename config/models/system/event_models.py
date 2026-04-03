from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

# مثال eventها:
# 
# lesson_started
# question_answered
# agent_failed
# memory_updated
# rag_retrieval


class SystemEvent(BaseModel):

    event_id: str

    event_type: str

    source: str

    payload: Dict

    timestamp: datetime


