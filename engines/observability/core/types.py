from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Span:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"
    start_time: float = 0.0
    end_time: float = 0.0
    parent_id: str = ""
    span_id: str = ""
    trace_id: str = ""


@dataclass
class Metric:
    name: str
    value: float = 0.0
    type: str = "counter"
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class Event:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    severity: str = "info"
