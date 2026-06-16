# engines/artifacts/models/artifacts_models.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Artifact:
    artifact_id: str = ""
    name: str = ""
    data: bytes = b""
    metadata: dict = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
