# engines/gateway/models/gateway_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ApiRequest:
    method: str = "GET"
    path: str = "/"
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


@dataclass
class ApiResponse:
    status_code: int = 200
    body: Any = None
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class RateLimitState:
    key: str = ""
    count: int = 0
    window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
