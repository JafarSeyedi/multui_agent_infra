"""Token repository adapter."""

from __future__ import annotations

from typing import Any

from ..runtime.runtime_records import TOKEN_RECORD
from .repository import PersistentRuntimeRepository


class TokenRepository(PersistentRuntimeRepository):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            record_type=TOKEN_RECORD,
            key_prefix="orchestration:tokens:",
            measurement="orchestration_tokens",
            **kwargs,
        )

    def get_by_instance(self, instance_id: str) -> list[dict[str, Any]]:
        return self.list(predicate=lambda row: row.get("instance_id") == instance_id)
