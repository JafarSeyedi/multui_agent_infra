from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContentVersion(BaseModel):

    content_id: str

    lesson_id: str
    version: str

    type: str                 # raw / rewritten / narrative / structured / ...
    language_level: str       # سطح زبان
    body: str                 # متن محتوا
    created_at: datetime

    created_by_agent: Optional[str]

    change_summary: Optional[str]
