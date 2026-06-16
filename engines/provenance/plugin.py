# engines/provenance/plugin.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IProvenanceTracker(ABC):
    name: str = "base"

    @abstractmethod
    async def record(self, entity_id: str, action: str, actor: str, metadata: dict[str, Any] | None = None) -> str: ...

    @abstractmethod
    async def get_lineage(self, entity_id: str) -> list[dict[str, Any]]: ...
