"""Data object read/write bridge for BPMN process contexts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DataObject:
    object_id: str
    value: Any


class DataObjectHandler:
    def __init__(self) -> None:
        self._objects: dict[str, DataObject] = {}

    def set(self, object_id: str, value: Any) -> None:
        self._objects[object_id] = DataObject(object_id=object_id, value=value)

    def get(self, object_id: str) -> Any:
        return self._objects.get(object_id)

    def read_map(self) -> dict[str, Any]:
        return {key: item.value for key, item in self._objects.items()}

    def clear(self) -> None:
        self._objects.clear()
