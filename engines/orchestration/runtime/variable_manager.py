"""Runtime variable lifecycle and conflict handling."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

from ..persistence.variable_repository import VariableRepository


@dataclass(frozen=True)
class VariableConflictError(ValueError):
    """Raised when a variable set/read conflict is detected."""


class VariableManager:
    """Concurrent-safe variable dictionary manager with optional persistence."""

    def __init__(self, repository: VariableRepository | None = None) -> None:
        self._vars: dict[str, Any] = {}
        self._lock = Lock()
        self.repository = repository

    def get(self, name: str, *, default: Any = None) -> Any:
        with self._lock:
            return self._vars.get(name, default)

    def set(self, name: str, value: Any, *, overwrite: bool = True) -> None:
        with self._lock:
            if not overwrite and name in self._vars:
                raise VariableConflictError(f"Variable already exists: {name}")
            self._vars[name] = value

    async def set_persisted(
        self,
        instance_id: str,
        scope_id: str,
        name: str,
        value: Any,
        *,
        value_type: str | None = None,
        overwrite: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        self.set(name, value, overwrite=overwrite)
        if self.repository is None:
            return None
        payload = {
            "instance_id": instance_id,
            "scope_id": scope_id,
            "name": name,
            "value": value,
            "value_type": value_type or type(value).__name__,
            "updated_at": metadata.get("updated_at") if metadata else None,
            "payload": dict(metadata or {}),
        }
        if payload["updated_at"] is None:
            payload.pop("updated_at")
        return await self.repository.save_persisted(f"{instance_id}:{scope_id}:{name}", payload)

    def pop(self, name: str) -> Any:
        with self._lock:
            return self._vars.pop(name)

    async def pop_persisted(self, instance_id: str, scope_id: str, name: str) -> Any:
        value = self.pop(name)
        if self.repository is not None:
            await self.repository.delete_persisted(f"{instance_id}:{scope_id}:{name}")
        return value

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._vars)

    def restore(self, values: dict[str, Any]) -> None:
        with self._lock:
            self._vars = dict(values)

    async def restore_persisted(self, instance_id: str, scope_id: str | None = None) -> dict[str, Any]:
        if self.repository is None:
            return self.snapshot()
        rows = (
            self.repository.get_by_scope(instance_id, scope_id)
            if scope_id is not None
            else self.repository.get_by_instance(instance_id)
        )
        restored = {str(row["name"]): row.get("value") for row in rows if "name" in row}
        self.restore(restored)
        return restored

    def clear(self) -> None:
        with self._lock:
            self._vars.clear()
