"""Definition repository adapter with lookup helpers."""

from __future__ import annotations

from typing import Any

from .repository import InMemoryRepository


class DefinitionRepository(InMemoryRepository):
    def get_by_key(self, key: str) -> list[dict[str, Any]]:
        return self.list(predicate=lambda row: row.get("key") == key)

    def get_latest(self, key: str) -> dict[str, Any] | None:
        candidates = self.get_by_key(key)
        if not candidates:
            return None
        return sorted(candidates, key=lambda row: int(row.get("version", 0)), reverse=True)[0]
