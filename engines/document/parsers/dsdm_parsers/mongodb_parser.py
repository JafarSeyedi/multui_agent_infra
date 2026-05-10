# engines/document/parsers/dsdm_parsers/mongodb_parser.py
"""MongoDB parser with live collection fetching."""
from __future__ import annotations

import datetime as dt
import base64
from uuid import UUID
from typing import Any

# Use runtime attribute checks instead of static imports
# to avoid mypy errors caused by missing pymongo BSON types.
import bson as _bson_module  # type: ignore[import-untyped]

from .bson_parser import BSONParser
from .base_dsdm_parser import DSDMParseOptions
from .dsdm_utils import scalar_value
from ...models.dsdm_models import DataNode, DataNodeKind, DataDocument, DataValue
from ...models.msdm_models import Entity, ScalarType
from ...models.media_types import MEDIA_TYPES


class MongoDBParser(BSONParser):
    name = "mongodb"

    async def fetch_collection(
        self,
        collection,                     # MotorCollection or PyMongo collection
        query: dict = {},
        options: DSDMParseOptions | None = None,
        entity: Entity | None = None,
    ) -> DataDocument:
        entity = entity or (options.msdm_schema.entities[0] if options and options.msdm_schema and options.msdm_schema.entities else None)

        projection = {attr.name: 1 for attr in entity.attributes} if entity and entity.attributes else None
        cursor = collection.find(query, projection)
        docs = []
        async for doc in cursor:
            docs.append(doc)

        root = DataNode(node_id="node:$", kind=DataNodeKind.ARRAY, path="$", name=entity.name if entity else "documents")
        for idx, doc in enumerate(docs):
            obj_node = DataNode(node_id=f"node:$[{idx}]", kind=DataNodeKind.OBJECT,
                                path=f"$[{idx}]", name=str(idx))
            if entity:
                for attr in entity.attributes:
                    raw = doc.get(attr.name)
                    value = self._coerce_mongo_value(raw, attr)
                    if value is None and attr.required:
                        obj_node.metadata["_required_missing"] = True
                    obj_node.children.append(DataNode(
                        node_id=f"node:$[{idx}].{attr.name}",
                        kind=DataNodeKind.SCALAR,
                        path=f"$[{idx}].{attr.name}",
                        name=attr.name,
                        value=value,
                    ))
            else:
                for k, v in doc.items():
                    obj_node.children.append(self._mongo_field_to_node(k, v, idx))
            root.children.append(obj_node)

        media_type = MEDIA_TYPES.get("application/bson", MEDIA_TYPES["binary"])
        doc = DataDocument(
            title=f"MongoDB collection {entity.name if entity else collection.name}",
            document_id=f"mongo:{entity.name if entity else collection.name}",
            media_type=media_type,
            root=root,
        )
        if options and options.msdm_schema and entity:
            self._bind_schema(doc, options.msdm_schema, options.inject_defaults, options.validate_against_schema)
        return doc

    def _coerce_mongo_value(self, raw, attr) -> DataValue | None:
        # Safely obtain BSON‑specific types at runtime (they may not exist in standalone bson)
        ObjectId = getattr(_bson_module, "ObjectId", None)
        Decimal128 = getattr(_bson_module, "Decimal128", None)
        Binary = getattr(_bson_module, "Binary", None)
        Code = getattr(_bson_module, "Code", None)
        Timestamp = getattr(_bson_module, "Timestamp", None)
        DBRef = getattr(_bson_module, "DBRef", None)

        if ObjectId is not None and isinstance(raw, ObjectId):
            raw = str(raw)
        elif Decimal128 is not None and isinstance(raw, Decimal128):
            raw = raw.to_decimal()
        elif Binary is not None and isinstance(raw, Binary):
            raw = bytes(raw)
        elif Code is not None and isinstance(raw, Code):
            raw = str(raw)
        elif Timestamp is not None and isinstance(raw, Timestamp):
            raw = raw.as_datetime()
        elif DBRef is not None and isinstance(raw, DBRef):
            raw = str(raw.id)

        if raw is None:
            if attr.default_value is not None:
                return self._coerce_default_value(attr)
            return None
        dt = attr.data_type.base
        try:
            if dt == ScalarType.INT:
                if isinstance(raw, bool):
                    return DataValue(scalar_type=ScalarType.BOOLEAN, value=raw, lexical_value=str(raw))
                return DataValue(scalar_type=ScalarType.INT, value=int(raw), lexical_value=str(raw))
            if dt == ScalarType.FLOAT or dt == ScalarType.DOUBLE:
                return DataValue(scalar_type=ScalarType.FLOAT, value=float(raw), lexical_value=str(raw))
            if dt == ScalarType.BOOLEAN:
                return DataValue(scalar_type=ScalarType.BOOLEAN, value=bool(raw), lexical_value=str(raw))
            if dt == ScalarType.DATETIME:
                if isinstance(raw, dt.datetime):
                    return DataValue(scalar_type=ScalarType.DATETIME, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.DATETIME, value=str(raw), lexical_value=str(raw))
            if dt == ScalarType.DATE:
                if isinstance(raw, dt.date):
                    return DataValue(scalar_type=ScalarType.DATE, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.DATE, value=str(raw), lexical_value=str(raw))
            if dt == ScalarType.TIME:
                if isinstance(raw, dt.time):
                    return DataValue(scalar_type=ScalarType.TIME, value=raw.isoformat(), lexical_value=raw.isoformat())
                return DataValue(scalar_type=ScalarType.TIME, value=str(raw), lexical_value=str(raw))
            if dt == ScalarType.UUID:
                if isinstance(raw, UUID):
                    return DataValue(scalar_type=ScalarType.UUID, value=str(raw), lexical_value=str(raw))
                return DataValue(scalar_type=ScalarType.UUID, value=str(raw), lexical_value=str(raw))
            if dt == ScalarType.BINARY:
                if isinstance(raw, bytes):
                    b64 = base64.b64encode(raw).decode()
                    return DataValue(scalar_type=ScalarType.BINARY, value=raw, lexical_value=b64)
                return DataValue(scalar_type=ScalarType.BINARY, value=base64.b64decode(raw), lexical_value=str(raw))
            return scalar_value(raw)
        except Exception:
            return scalar_value(raw)

    def _mongo_field_to_node(self, key, val, idx) -> DataNode:
        return DataNode(
            node_id=f"node:$[{idx}].{key}",
            kind=DataNodeKind.SCALAR,
            path=f"$[{idx}].{key}",
            name=key,
            value=scalar_value(val),
        )