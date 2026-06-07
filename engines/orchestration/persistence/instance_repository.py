"""Process instance repository adapter."""

from __future__ import annotations

from typing import Any

from .runtime_records import INSTANCE_RECORD
from .repository import PersistentRuntimeRepository


class InstanceRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=INSTANCE_RECORD,
            key_prefix="orchestration:instances:",
            measurement="orchestration_instances",
            **kwargs,
        )

    def get_by_definition(self, definition_id: str) -> list[dict[str, Any]]:
        return self.list(predicate=lambda row: row.get("definition_id") == definition_id)

    def get_active(self) -> list[dict[str, Any]]:
        return self.list(predicate=lambda row: row.get("state") == "active")
