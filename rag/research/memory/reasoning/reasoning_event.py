# rag/research/memory/reasoning/reasoning_event.py

from __future__ import annotations

import time
from typing import Optional, Dict

from .event_types import ReasoningEventType


class ReasoningEvent:
    """
    Atomic event in reasoning trace.
    """

    __slots__ = (
        "event_type",
        "message",
        "meta",
        "timestamp",
        "token_count"
    )

    def __init__(
        self,
        event_type: ReasoningEventType,
        message: str,
        *,
        meta: Optional[Dict] = None,
        token_count: Optional[int] = None
    ):
        self.event_type = event_type
        self.message = message
        self.meta = meta or {}
        self.token_count = token_count
        self.timestamp = time.time()

    def to_dict(self):

        return {
            "type": self.event_type.value,
            "message": self.message,
            "meta": self.meta,
            "token_count": self.token_count,
            "timestamp": self.timestamp
        }
