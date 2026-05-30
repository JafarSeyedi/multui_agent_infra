"""Case file item persistence model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaseFileItem:
    item_id: str
    value: object


class CaseFileManager:
    def __init__(self) -> None:
        self._items: dict[str, CaseFileItem] = {}

    def add(self, item_id: str, value: object) -> None:
        self._items[item_id] = CaseFileItem(item_id=item_id, value=value)

    def get(self, item_id: str) -> object | None:
        item = self._items.get(item_id)
        return item.value if item else None

    def list_ids(self) -> list[str]:
        return sorted(self._items.keys())
