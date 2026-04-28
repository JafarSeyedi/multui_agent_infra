# engines/document/writers/msdm_writers/mongodb_schema_writer.py
"""
MongoDB Schema Writer – converts an MSDMDocument into a MongoDB JSON validator
schema (.json).  Produces a ``validator`` document with ``$jsonSchema``, and
optionally includes collection‑level options (validationLevel, etc.).
Indexes are emitted as comments for manual creation.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Annotation,
    EntityKind,
    ScalarType,
)

# ── ScalarType → BSON type ────────────────────────────────────────
_SCALAR_TO_BSON: Dict[ScalarType, str] = {
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
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        # Expect one DOCUMENT entity per file; if multiple, write an array
        doc_entities = [e for e in document.entities if e.kind == EntityKind.DOCUMENT]
        if not doc_entities:
            doc_entities = document.entities  # fallback

        results = []
        for entity in doc_entities:
            schema = self._build_validator_schema(entity)
            results.append(schema)

        if len(results) == 1:
            output = results[0]
        else:
            output = results

        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Build validator wrapper ────────────────────────────────────
    def _build_validator_schema(self, entity: Entity) -> dict:
        """Return a MongoDB collection schema with validator, etc."""
        schema = {}

        # Collection name (optional)
        collection = self._get_annotation(entity, "collection")
        if collection:
            schema["collection"] = collection

        # Validator
        validator = {}
        json_schema = self._entity_to_json_schema(entity)

        # If there are top-level validation options stored as annotations
        for ann in entity.annotations:
            if ann.key in ("validationLevel", "validationAction", "validator"):
                try:
                    val = json.loads(ann.value)
                except json.JSONDecodeError:
                    val = ann.value
                if ann.key == "validator":
                    # already building, skip
                    continue
                schema[ann.key] = val

        validator["$jsonSchema"] = json_schema
        schema["validator"] = validator

        # Indexes as comment? Not part of validator; we can attach as a separate annotation in the output.
        # We'll include an "indexes" field at the top level of the output for user reference.
        indexes = self._format_indexes(entity)
        if indexes:
            schema["_indexes"] = indexes   # non‑standard, but helpful; removed by consumers

        return schema

    # ── Entity → $jsonSchema ───────────────────────────────────────
    def _entity_to_json_schema(self, entity: Entity) -> dict:
        json_schema = {
            "bsonType": "object",
            "title": entity.name,
        }
        if entity.description:
            json_schema["description"] = entity.description

        # Additional properties – if annotation exists, use it; else default to true
        add_props = self._get_annotation(entity, "additionalProperties")
        if add_props is not None:
            json_schema["additionalProperties"] = add_props == "true"
        else:
            json_schema["additionalProperties"] = True

        # Required from required attributes
        required = [attr.name for attr in entity.attributes if attr.required]
        if required:
            json_schema["required"] = required

        # Properties
        properties = {}
        for attr in entity.attributes:
            if attr.name == "_id":
                continue   # skip default _id unless explicitly modelled
            prop = self._attribute_to_bson_property(attr)
            properties[attr.name] = prop
        json_schema["properties"] = properties

        return json_schema

    # ── Attribute → BSON property schema ──────────────────────────
    def _attribute_to_bson_property(self, attr: Attribute) -> dict:
        prop = {}

        # bsonType
        bson_type = self._get_annotation(attr, "bsonType")
        if not bson_type:
            bson_type = self._datatype_to_bson(attr.data_type)
        prop["bsonType"] = bson_type

        # Description
        if attr.description:
            prop["description"] = attr.description

        # Enum constraint → enum or check?
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK and c.expression.startswith("IN ("):
                # Extract enum values
                inner = c.expression[4:].rstrip(")")
                values = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
                if values:
                    prop["enum"] = values
            elif c.type == ConstraintType.CHECK:
                # Other CHECK constraints could be stored as $expr; not directly supported
                prop["description"] = prop.get("description", "") + f" [CHECK: {c.expression}]"

        # Numeric constraints (minimum, maximum)
        for ann in attr.annotations:
            if ann.key in ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum"):
                try:
                    prop[ann.key] = int(ann.value) if ann.value.isdigit() else float(ann.value)
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
            elif ann.key == "enum":
                # Already handled via constraint, but annotation might override
                pass
            elif ann.key in ("default", "uniqueItems", "minItems", "maxItems",
                             "contentMediaType", "contentEncoding"):
                try:
                    prop[ann.key] = json.loads(ann.value)
                except json.JSONDecodeError:
                    prop[ann.key] = ann.value
            elif ann.key == "bsonType":
                pass   # already set
            else:
                # Other annotations → store in a meta field? We'll skip.
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
                # If nested attributes, assume array of objects
                first = attr.nested_attributes[0] if attr.nested_attributes else None
                if first:
                    items_schema = self._attribute_to_bson_property(first)
                    prop["items"] = items_schema

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
            # ObjectId reference – could be "objectId" or "object"
            return "objectId"
        if base in _SCALAR_TO_BSON:
            return _SCALAR_TO_BSON[base]
        return "object"

    # ── Index formatting (as reference) ────────────────────────────
    def _format_indexes(self, entity: Entity) -> List[dict]:
        indexes = []
        for idx in entity.indexes:
            idx_def = {
                "keys": {attr: 1 for attr in idx.attributes},
                "options": {},
            }
            if idx.name:
                idx_def["options"]["name"] = idx.name
            if idx.unique:
                idx_def["options"]["unique"] = True
            indexes.append(idx_def)
        return indexes

    # ── Helpers ────────────────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
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
            return raw   # assume valid ObjectId string
        if bson_type == "date":
            return {"$date": raw}
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        return raw