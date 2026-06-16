# engines/ui_backend/models/ui_backend_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class UIComponent:
    name: str = ""
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class UIAction:
    action: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    session_id: str = ""
    user_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
