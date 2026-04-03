from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContentVersion(BaseModel):

    content_id: str

    version: str

    created_at: datetime

    created_by_agent: Optional[str]

    change_summary: Optional[str]
