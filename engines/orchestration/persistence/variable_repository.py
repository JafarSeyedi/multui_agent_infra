"""Variable value repository."""

from __future__ import annotations

from typing import Any

from ..runtime.runtime_records import VARIABLE_RECORD
from .repository import PersistentRuntimeRepository


class VariableRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=VARIABLE_RECORD,
            key_prefix="orchestration:variables:",
            measurement="orchestration_variables",
            **kwargs,
        )

    def get_by_instance(self, instance_id: str) -> list[dict[str, str | int | float | bool | None]]:
        return self.list(predicate=lambda row: row.get("instance_id") == instance_id)  # type: ignore[return-value]

    def get_by_scope(self, instance_id: str, scope_id: str) -> list[dict[str, Any]]:
        return self.list(
            predicate=lambda row: row.get("instance_id") == instance_id and row.get("scope_id") == scope_id
        )
