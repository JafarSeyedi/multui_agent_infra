# rag/research/memory/reasoning/reasoning_event.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

from .event_types import ReasoningEventType


@dataclass
class ReasoningEvent:
    """
    Atomic event in reasoning trace.
    """
    id: str
    timestamp: float
    session_id: str
    group: str
    step: int
    phase: str
    event_type: str          # مقدار .value از ReasoningEventType ذخیره می‌شه
    level: str
    message: str
    meta: Dict[str, Any] = field(default_factory=dict)
    token_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not isinstance(d["meta"], dict):
            d["meta"] = {"value": str(d["meta"])}
        return d
