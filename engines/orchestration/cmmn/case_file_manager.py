"""Case file management for CMMN.

Binds case file items/data to MSDM/DSDM models and persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ....document.models.msdm_models import Entity, Attribute, DataType, ScalarType


@dataclass
class CaseFileItem:
    item_id: str
    name: str | None = None
    definition_ref: str | None = None
    value: Any = None
    data_state: str | None = None
    source_ref: str | None = None
    owner_ref: str | None = None
    is_collection: bool = False
    multiplicity: str = "ZeroOrOne"
    msdm_entity: Entity | None = None


@dataclass
class CaseFileDefinition:
    definition_id: str
    name: str | None = None
    properties: list[CaseFileItem] = field(default_factory=list)
    allowed_types: list[str] = field(default_factory=list)


class CaseFileManager:
    def __init__(self) -> None:
        self._items: dict[str, CaseFileItem] = {}
        self._definitions: dict[str, CaseFileDefinition] = {}

    def set_item(self, item_id: str, value: Any, **kwargs: Any) -> CaseFileItem:
        item = CaseFileItem(item_id=item_id, value=value, **kwargs)
        self._items[item_id] = item
        return item

    def get_item(self, item_id: str) -> CaseFileItem | None:
        return self._items.get(item_id)

    def get_value(self, item_id: str) -> Any:
        item = self._items.get(item_id)
        return item.value if item else None

    def remove_item(self, item_id: str) -> bool:
        return self._items.pop(item_id, None) is not None

    def get_all(self) -> dict[str, Any]:
        return {key: item.value for key, item in self._items.items()}

    def get_items(self) -> list[CaseFileItem]:
        return list(self._items.values())

    def clear(self) -> None:
        self._items.clear()

    def register_definition(self, definition: CaseFileDefinition) -> None:
        self._definitions[definition.definition_id] = definition

    def get_definition(self, definition_id: str) -> CaseFileDefinition | None:
        return self._definitions.get(definition_id)

    def get_by_state(self, state: str) -> list[CaseFileItem]:
        return [item for item in self._items.values() if item.data_state == state]

    def get_by_owner(self, owner_ref: str) -> list[CaseFileItem]:
        return [item for item in self._items.values() if item.owner_ref == owner_ref]

    def get_collection_items(self) -> list[CaseFileItem]:
        return [item for item in self._items.values() if item.is_collection]

    def update_data_state(self, item_id: str, new_state: str) -> bool:
        item = self._items.get(item_id)
        if item is None:
            return False
        item.data_state = new_state
        return True

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._items)
        states: dict[str, int] = {}
        for item in self._items.values():
            state = item.data_state or "none"
            states[state] = states.get(state, 0) + 1
        return {
            "total_items": total,
            "collection_items": sum(1 for i in self._items.values() if i.is_collection),
            "definitions": len(self._definitions),
            "states": states,
        }
