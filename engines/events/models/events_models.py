# engines/events/models/events_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class EventRecord:
    topic: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
