# engines/document/writers/msdm_writers/mongodb_schema_writer.py
"""
MongoDB Schema Writer – converts an MSDMDocument into a MongoDB JSON validator
schema (.json).  Produces a ``validator`` document with ``$jsonSchema``, and
optionally includes collection‑level options (validationLevel, etc.).
Indexes are emitted as comments for manual creation.
"""
from __future__ import annotations

import json
from typing import Any, Union

from ...models.msdm_models import Attribute
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter, ConnectionConfig
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget

try:
    from pymongo import MongoClient
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False

# ── ScalarType → BSON type ────────────────────────────────────────
_SCALAR_TO_BSON: dict[ScalarType, str] = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "int",
    ScalarType.LONG:      "long",
    ScalarType.FLOAT:     "double",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "bool",
    ScalarType.DATE:      "date",
    ScalarType.TIME:      "date",
    ScalarType.TIMESTAMP: "date",
    ScalarType.UUID:      "binData",
    ScalarType.BINARY:    "binData",
    ScalarType.DECIMAL:   "decimal",
    ScalarType.DURATION:  "long",
    ScalarType.ANY:       "object",
    ScalarType.JSON:      "object",
    ScalarType.XML:       "string",
}


class MongoDBSchemaWriter(BaseMSDMWriter):
    """Writer for MongoDB validator schemas (.json)."""
    name = "mongodb_schema"
    supported_extensions = (".json", ".validator.json")

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        doc_entities = [e for e in document.entities if e.kind == EntityKind.DOCUMENT]
        if not doc_entities:
            doc_entities = document.entities  # fallback

        results = []
        for entity in doc_entities:
            schema = self._build_validator_schema(entity)
            results.append(schema)

        output: dict | list = results[0] if len(results) == 1 else results
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        return json_str.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build validator wrapper ────────────────────────────────────
    def _build_validator_schema(self, entity: Entity) -> dict:
        """Return a MongoDB collection schema with validator, etc."""
        schema: dict[str, Any] = {}

        collection = self._get_annotation(entity, "collection")
        if collection:
            schema["collection"] = collection

        validator: dict[str, Any] = {}
        json_schema = self._entity_to_json_schema(entity)

        for ann in entity.annotations:
            if ann.key in ("validationLevel", "validationAction", "validator"):
                try:
                    val = json.loads(ann.value)
                except json.JSONDecodeError:
                    val = ann.value
                if ann.key == "validator":
                    continue
                schema[ann.key] = val

        validator["$jsonSchema"] = json_schema
        schema["validator"] = validator

        indexes = self._format_indexes(entity)
        if indexes:
            schema["_indexes"] = indexes

        return schema

    # ── Entity → $jsonSchema ───────────────────────────────────────
    def _entity_to_json_schema(self, entity: Entity) -> dict:
        json_schema: dict[str, Any] = {
            "bsonType": "object",
            "title": entity.name,
        }
        if entity.description:
            json_schema["description"] = entity.description

        add_props = self._get_annotation(entity, "additionalProperties")
        if add_props is not None:
            json_schema["additionalProperties"] = add_props == "true"
        else:
            json_schema["additionalProperties"] = True

        required = [attr.name for attr in entity.attributes if attr.required]
        if required:
            json_schema["required"] = required

        properties = {}
        for attr in entity.attributes:
            if attr.name == "_id":
                continue
            prop = self._attribute_to_bson_property(attr)
            properties[attr.name] = prop
        json_schema["properties"] = properties

        return json_schema

    # ── Attribute → BSON property schema ──────────────────────────
    def _attribute_to_bson_property(self, attr: Attribute) -> dict:
        prop: dict[str, Any] = {}

        bson_type = self._get_annotation(attr, "bsonType")
        if not bson_type:
            bson_type = self._datatype_to_bson(attr.data_type)
        prop["bsonType"] = bson_type

        if attr.description:
            prop["description"] = attr.description

        for c in attr.constraints:
            if c.type == ConstraintType.CHECK and c.expression is not None and c.expression.startswith("IN ("):
                inner = c.expression[4:].rstrip(")")
                values = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
                if values:
                    prop["enum"] = values
            elif c.type == ConstraintType.CHECK and c.expression is not None:
                existing = prop.get("description", "")
                prop["description"] = f"{existing} [CHECK: {c.expression}]".strip()

        for ann in attr.annotations:
            if ann.key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                try:
                    if ann.value.isdigit():
                        prop[ann.key] = int(ann.value)
                    else:
                        prop[ann.key] = float(ann.value)
                except (ValueError, TypeError):
                    pass
            elif ann.key == "multipleOf":
                try:
                    prop["multipleOf"] = float(ann.value)
                except ValueError:
                    pass
            elif ann.key == "minLength":
                try:
                    prop["minLength"] = int(ann.value)
                except ValueError:
                    pass
            elif ann.key == "maxLength":
                try:
                    prop["maxLength"] = int(ann.value)
                except ValueError:
                    pass
            elif ann.key == "pattern":
                prop["pattern"] = ann.value
            elif ann.key == "format":
                prop["format"] = ann.value
            elif ann.key in ("default", "uniqueItems", "minItems", "maxItems",
                             "contentMediaType", "contentEncoding"):
                try:
                    prop[ann.key] = json.loads(ann.value)
                except json.JSONDecodeError:
                    prop[ann.key] = ann.value
            elif ann.key == "bsonType":
                pass

        # Properties for nested objects
        if bson_type in ("object", "array") and attr.nested_attributes:
            if bson_type == "object":
                nested_props = {}
                nested_req = []
                for na in attr.nested_attributes:
                    nested_props[na.name] = self._attribute_to_bson_property(na)
                    if na.required:
                        nested_req.append(na.name)
                prop["properties"] = nested_props
                if nested_req:
                    prop["required"] = nested_req
            elif bson_type == "array":
                if attr.nested_attributes:
                    first = attr.nested_attributes[0]
                    prop["items"] = self._attribute_to_bson_property(first)

        # Default value
        if attr.default_value is not None:
            prop["default"] = self._parse_bson_value(attr.default_value, bson_type)

        return prop

    # ── DataType to BSON type string ───────────────────────────────
    def _datatype_to_bson(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            return "array"
        if base == ScalarType.MAP:
            return "object"
        if base == ScalarType.STRUCT:
            return "object"
        if base == ScalarType.REF:
            return "objectId"
        return _SCALAR_TO_BSON.get(base, "object")

    # ── Index formatting (as reference) ────────────────────────────
    def _format_indexes(self, entity: Entity) -> list[dict]:
        indexes = []
        for idx in entity.indexes:
            option: dict[str, str | bool] = {}
            idx_def = {
                "keys": {attr.name for attr in idx.attributes},
                "options": option,
            }
            if idx.name:
                option["name"] = idx.name
            if idx.unique:
                option["unique"] = True
            indexes.append(idx_def)
        return indexes

    # ── Helpers ────────────────────────────────────────────────────
    def _get_annotation(self, obj: Any, key: str) -> str | None:
        if isinstance(obj, Entity):
            for a in obj.annotations:
                if a.key == key:
                    return a.value
        elif isinstance(obj, Attribute):
            for a in obj.annotations:
                if a.key == key:
                    return a.value
        return None

    @staticmethod
    def _parse_bson_value(raw: str, bson_type: str) -> Any:
        """Convert a string default value to a BSON‑compatible Python literal."""
        raw = raw.strip()
        if raw == "null":
            return None
        if bson_type in ("int", "long", "double", "decimal"):
            try:
                if '.' in raw or 'e' in raw.lower():
                    return float(raw)
                return int(raw)
            except ValueError:
                return raw
        if bson_type == "bool":
            return raw.lower() == "true"
        if bson_type == "objectId":
            return raw
        if bson_type == "date":
            return {"$date": raw}
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        return raw

    async def apply_to_database(
        self,
        document: MSDMDocument,
        connection: ConnectionConfig | None = None,
    ) -> None:
        if not MONGO_AVAILABLE:
            raise ImportError("pymongo is required. pip install pymongo")
        if connection is None:
            raise ValueError("ConnectionConfig required")

        url = connection.url or f"mongodb://{connection.host or 'localhost'}:{connection.port or 27017}/"
        client: MongoClient = MongoClient(url)
        try:
            db_name = connection.database or "default"
            db = client[db_name]
            for entity in document.entities:
                if entity.kind != EntityKind.DOCUMENT:
                    continue
                collection_name = entity.name
                if collection_name not in db.list_collection_names():
                    validator_schema = self._build_validator_schema(entity)
                    db.create_collection(collection_name, validator=validator_schema)
                else:
                    validator_schema = self._build_validator_schema(entity)
                    db.command("collMod", collection_name, validator=validator_schema)
            model_collections = {e.name for e in document.entities if e.kind == EntityKind.DOCUMENT}
            existing = set(db.list_collection_names())
            for coll in existing - model_collections:
                self._handle_collection_deletion(db, coll)
        finally:
            client.close()

    def _handle_collection_deletion(self, db: Any, coll_name: str) -> None:
        if self.soft_delete_strategy == SoftDeleteStrategy.NONE:
            db.drop_collection(coll_name)
        elif self.soft_delete_strategy == SoftDeleteStrategy.PREFIX:
            new_name = f"_deleted_{coll_name}"
            db.get_collection(coll_name).rename(new_name)
        elif self.soft_delete_strategy == SoftDeleteStrategy.SUFFIX:
            new_name = f"{coll_name}_deleted"
            db.get_collection(coll_name).rename(new_name)