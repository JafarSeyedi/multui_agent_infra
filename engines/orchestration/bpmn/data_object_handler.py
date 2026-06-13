"""Data object read/write bridge for BPMN process contexts.

Binds BPMN data objects, data stores, messages, and data associations
to MSDM schema definitions and DSDM persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...document.models.dsdm_models import DataDocument, DataSchemaReference, SchemaBinding
from ...document.models.msdm_models import Entity, Attribute, DataType, ScalarType
from engines.orchestration.models.osdm_models import (
    DataObject,
    DataObjectReference,
    DataStore,
    DataStoreReference,
    DataAssociation,
    DataInputAssociation,
    DataOutputAssociation,
    DataInput,
    DataOutput,
    DataState,
    InputSet,
    OutputSet,
    ItemDefinition,
    Message as OSDMMessage,
    Property,
    Assignment,
    InputOutputBinding,
)


@dataclass(frozen=True)
class HandlerDataObject:
    object_id: str
    value: Any
    item_definition_ref: str | None = None
    data_state: str | None = None
    is_collection: bool = False
    schema_binding: SchemaBinding | None = None
    msdm_entity: Entity | None = None
    osdm_object: DataObject | None = None


@dataclass(frozen=True)
class HandlerDataStoreRef:
    store_id: str
    store_name: str | None = None
    item_definition_ref: str | None = None
    data_state: str | None = None
    is_unlimited: bool = True
    osdm_store: DataStoreReference | None = None


@dataclass(frozen=True)
class HandlerMessageObject:
    message_id: str
    name: str | None = None
    item_definition_ref: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    osdm_message: OSDMMessage | None = None


@dataclass(frozen=True)
class HandlerDataAssociation:
    source_ref: str
    target_ref: str
    transformation: str | None = None
    association_id: str | None = None
    osdm_association: DataAssociation | None = None


class DataObjectHandler:
    def __init__(self) -> None:
        self._objects: dict[str, HandlerDataObject] = {}
        self._data_stores: dict[str, HandlerDataStoreRef] = {}
        self._messages: dict[str, HandlerMessageObject] = {}
        self._associations: list[HandlerDataAssociation] = []
        self._schema_registry: dict[str, Entity] = {}
        self._osdm_objects: dict[str, DataObject] = {}

    # ── Existing dict-based API (backward compatible) ─────────────

    def set(self, object_id: str, value: Any, **kwargs) -> HandlerDataObject:
        obj = HandlerDataObject(object_id=object_id, value=value, **kwargs)
        self._objects[object_id] = obj
        return obj

    def get(self, object_id: str) -> Any:
        obj = self._objects.get(object_id)
        return obj.value if obj is not None else None

    def get_object(self, object_id: str) -> HandlerDataObject | None:
        return self._objects.get(object_id)

    def read_map(self) -> dict[str, Any]:
        return {key: item.value for key, item in self._objects.items()}

    def clear(self) -> None:
        self._objects.clear()

    def remove(self, object_id: str) -> bool:
        return self._objects.pop(object_id, None) is not None

    def list_objects(self) -> list[HandlerDataObject]:
        return list(self._objects.values())

    def register_schema(self, name: str, entity: Entity) -> None:
        self._schema_registry[name] = entity

    def get_schema(self, name: str) -> Entity | None:
        return self._schema_registry.get(name)

    def bind_schema_to_object(self, object_id: str, entity: Entity) -> bool:
        obj = self._objects.get(object_id)
        if obj is None:
            return False
        binding = SchemaBinding(entity=entity, attribute=None, source_schema=None)
        self._objects[object_id] = HandlerDataObject(
            object_id=obj.object_id, value=obj.value, item_definition_ref=obj.item_definition_ref,
            data_state=obj.data_state, is_collection=obj.is_collection,
            schema_binding=binding, msdm_entity=entity,
        )
        return True

    def register_data_store(self, store_id: str, **kwargs) -> HandlerDataStoreRef:
        store = HandlerDataStoreRef(store_id=store_id, **kwargs)
        self._data_stores[store_id] = store
        return store

    def get_data_store(self, store_id: str) -> HandlerDataStoreRef | None:
        return self._data_stores.get(store_id)

    def register_message(self, message_id: str, **kwargs) -> HandlerMessageObject:
        msg = HandlerMessageObject(message_id=message_id, **kwargs)
        self._messages[message_id] = msg
        return msg

    def get_message(self, message_id: str) -> HandlerMessageObject | None:
        return self._messages.get(message_id)

    def add_association(self, source: str, target: str, **kwargs) -> HandlerDataAssociation:
        assoc = HandlerDataAssociation(source_ref=source, target_ref=target, **kwargs)
        self._associations.append(assoc)
        return assoc

    def resolve_associations(self, source_ref: str) -> list[HandlerDataAssociation]:
        return [a for a in self._associations if a.source_ref == source_ref]

    def get_statistics(self) -> dict[str, Any]:
        return {
            "total_objects": len(self._objects),
            "total_data_stores": len(self._data_stores),
            "total_messages": len(self._messages),
            "total_associations": len(self._associations),
        }

    # ── OSDM-typed API ────────────────────────────────────────────

    def set_osdm(self, data_object: DataObject, value: Any) -> HandlerDataObject:
        """Store a value keyed by an OSDM DataObject.

        Extracts ``id``, ``name``, ``is_collection``, ``item_subject_ref``,
        and ``data_state`` from the OSDM object, using ``.id`` on ref fields
        when they are objects.
        """
        obj_id = data_object.id
        item_ref: str | None = None
        if data_object.item_subject_ref is not None:
            item_ref = (
                data_object.item_subject_ref.id
                if hasattr(data_object.item_subject_ref, "id")
                else str(data_object.item_subject_ref)
            )
        state: str | None = None
        if data_object.data_state is not None:
            state = (
                data_object.data_state.id
                if hasattr(data_object.data_state, "id")
                else str(data_object.data_state)
            )
        obj = HandlerDataObject(
            object_id=obj_id,
            value=value,
            item_definition_ref=item_ref,
            data_state=state,
            is_collection=data_object.is_collection,
            osdm_object=data_object,
        )
        self._objects[obj_id] = obj
        self._osdm_objects[obj_id] = data_object
        return obj

    def get_osdm(self, data_object: DataObject) -> DataObject | None:
        """Retrieve the OSDM DataObject previously stored via ``set_osdm``.

        Looks up by the DataObject's ``id`` field.
        """
        return self._osdm_objects.get(data_object.id)

    def bind_schema_osdm(self, data_object: DataObject, entity: Entity) -> bool:
        """Bind an MSDM Entity schema to an OSDM DataObject.

        Finds the existing handler entry for the DataObject (by id) and
        attaches a ``SchemaBinding`` referencing the given entity.  If no
        handler entry exists, registers the schema and returns ``False``.
        """
        obj_id = data_object.id
        obj = self._objects.get(obj_id)
        if obj is None:
            return False
        binding = SchemaBinding(entity=entity, attribute=None, source_schema=None)
        self._objects[obj_id] = HandlerDataObject(
            object_id=obj.object_id,
            value=obj.value,
            item_definition_ref=obj.item_definition_ref,
            data_state=obj.data_state,
            is_collection=obj.is_collection,
            schema_binding=binding,
            msdm_entity=entity,
            osdm_object=data_object,
        )
        self._schema_registry[obj_id] = entity
        return True
