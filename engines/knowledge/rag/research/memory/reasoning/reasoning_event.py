# rag/research/memory/reasoning/reasoning_event.py
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import field
from typing import Any



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
    event_type: str          # .value from ReasoningEventType is stored
    level: str
    message: str
    meta: dict[str, Any] = field(default_factory=dict)
    token_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if not isinstance(d["meta"], dict):
            d["meta"] = {"value": str(d["meta"])}
        return d
