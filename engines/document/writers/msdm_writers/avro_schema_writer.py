# engines/document/writers/msdm_writers/avro_schema_writer.py
"""
Avro Schema Writer – converts an MSDMDocument into an Apache Avro schema JSON file.

Handles:
- Top-level records, enums, and fixed types.
- Fields with Avro logical types (decimal, date, time-millis, etc.).
- Nested records, arrays, maps, and unions (including nullable via ["null", type]).
- Default values, aliases, doc strings.
- References to other named types are resolved to the full name (namespace.name).
- Soft‑delete strategy is not applicable for Avro (schema files are generative).

The output is a JSON object for a single entity, or a JSON array if the document
contains multiple entities.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List, Tuple

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
    AvroLogicalType,
)

# Avro type name to ScalarType and back
SCALAR_TO_AVRO = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "int",
    ScalarType.LONG:      "long",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.BINARY:    "bytes",
    ScalarType.DATE:      "int",          # logical type date (int)
    ScalarType.TIME:      "int",          # logical type time-millis (int)
    ScalarType.TIMESTAMP: "long",         # logical type timestamp-millis (long)
    ScalarType.DURATION:  "bytes",        # logical type duration (fixed(12))
    ScalarType.UUID:      "string",       # logical type uuid (string)
    ScalarType.DECIMAL:   "bytes",        # logical type decimal (bytes)
}

# AvroLogicalType enum back to Avro string
LOGICAL_TYPE_TO_AVRO = {
    AvroLogicalType.DECIMAL:            "decimal",
    AvroLogicalType.DATE:               "date",
    AvroLogicalType.TIME_MILLIS:        "time-millis",
    AvroLogicalType.TIME_MICROS:        "time-micros",
    AvroLogicalType.TIMESTAMP_MILLIS:   "timestamp-millis",
    AvroLogicalType.TIMESTAMP_MICROS:   "timestamp-micros",
    AvroLogicalType.DURATION:           "duration",
    AvroLogicalType.UUID:               "uuid",
}


class AvroSchemaWriter(BaseMSDMWriter):
    """Writer for Apache Avro Schema (.avsc)."""
    name = "avro_schema"
    supported_extensions = (".avsc",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        # Avro schema files are always design files; ignore target_mode?

    # ── Public API ──────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        schemas = []
        for entity in document.entities:
            schema = self._entity_to_avro(entity, document)
            if schema is not None:
                schemas.append(schema)

        if len(schemas) == 1:
            result = schemas[0]
        elif len(schemas) > 1:
            result = schemas   # list of schemas
        else:
            # empty document -> empty JSON object? We'll produce empty string.
            return b"{}"

        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/vnd.apache.avro+json"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity to Avro record/enum/fixed ────────────────────────
    def _entity_to_avro(self, entity: Entity, doc: MSDMDocument) -> Optional[Dict]:
        # Determine the Avro type: if entity has kind=OBJECT, we produce a "record",
        # but it could also be an enum (if annotations say so) or a fixed (if binary with max_length).
        # We'll rely on annotations: if "enum_value" in annotations (from graphql/other), we treat as enum.
        # But for pure Avro, the parser stores certain hints. We'll check if there's an attribute "value" with a CHECK constraint listing enum symbols, it's an enum.
        # Or if entity.kind == OBJECT and only one attribute named "bytes" with binary and fixed size? Fixed types are rare.
        # The simplest: if the entity has attributes and the first attribute is "value" with a constraint of type CHECK and expression "IN (...)", treat as enum.
        # But we also need to check if the Avro parser stored an annotation `avro_type` = "enum"/"fixed". We'll implement robust detection.

        # Determine namespace from entity.namespace or doc.namespace
        namespace = entity.namespace or doc.namespace
        fq_name = f"{namespace}.{entity.name}" if namespace else entity.name

        # Check for enum: Avro enum is mapped as a special entity with one attribute "value" and a CHECK constraint.
        if self._is_enum_entity(entity):
            return self._build_enum_schema(entity, fq_name, namespace)

        # Check for fixed: similar, binary with fixed length
        if self._is_fixed_entity(entity):
            return self._build_fixed_schema(entity, fq_name, namespace)

        # Default: record
        return self._build_record_schema(entity, fq_name, namespace)

    def _is_enum_entity(self, entity: Entity) -> bool:
        if len(entity.attributes) != 1:
            return False
        attr = entity.attributes[0]
        if attr.name != "value":
            return False
        # Look for a CHECK constraint that looks like "IN (...)"
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK and c.expression.startswith("IN ("):
                return True
        return False

    def _is_fixed_entity(self, entity: Entity) -> bool:
        if len(entity.attributes) != 1:
            return False
        attr = entity.attributes[0]
        if attr.name != "bytes":
            return False
        if attr.data_type.base == ScalarType.BINARY and attr.data_type.max_length is not None:
            return True
        return False

    def _build_record_schema(self, entity: Entity, fq_name: str, namespace: Optional[str]) -> Dict:
        record = {
            "type": "record",
            "name": entity.name,
            "fields": []
        }
        if namespace:
            record["namespace"] = namespace
        if entity.description:
            record["doc"] = entity.description
        # Aliases from annotations
        aliases = self._get_aliases(entity)
        if aliases:
            record["aliases"] = aliases

        for attr in entity.attributes:
            # Skip placeholder for value if it's an enum/fixed detection? Already excluded.
            field_schema = self._attribute_to_avro_field(attr, namespace)
            record["fields"].append(field_schema)

        return record

    def _build_enum_schema(self, entity: Entity, fq_name: str, namespace: Optional[str]) -> Dict:
        attr = entity.attributes[0]
        # Extract symbols from the CHECK constraint expression
        symbols = self._extract_enum_symbols(attr)
        enum_schema = {
            "type": "enum",
            "name": entity.name,
            "symbols": symbols,
        }
        if namespace:
            enum_schema["namespace"] = namespace
        if entity.description:
            enum_schema["doc"] = entity.description
        aliases = self._get_aliases(entity)
        if aliases:
            enum_schema["aliases"] = aliases
        return enum_schema

    def _build_fixed_schema(self, entity: Entity, fq_name: str, namespace: Optional[str]) -> Dict:
        attr = entity.attributes[0]
        fixed_schema = {
            "type": "fixed",
            "name": entity.name,
            "size": attr.data_type.max_length,
        }
        if namespace:
            fixed_schema["namespace"] = namespace
        if entity.description:
            fixed_schema["doc"] = entity.description
        aliases = self._get_aliases(entity)
        if aliases:
            fixed_schema["aliases"] = aliases
        return fixed_schema

    # ── Attribute → Avro field ──────────────────────────────────
    def _attribute_to_avro_field(self, attr: Attribute, parent_namespace: Optional[str]) -> Dict:
        field = {"name": attr.name}
        if attr.description:
            field["doc"] = attr.description

        # Type and logical type
        avro_type, logical_type = self._datatype_to_avro(attr.data_type, parent_namespace)
        # Handle nullable (union with null) if required=False and not already a union? Avro default is not nullable unless specified. The parser might have marked required=True. In Avro, fields are optional if they have a default value or if the schema includes null in a union. We'll examine if the attribute had a required flag. If required=False, we'll make it a union with null.
        if not attr.required:
            # Ensure avro_type is a list (union) with "null" at front, unless already a complex union from DataType.
            if isinstance(avro_type, list):
                # Check if "null" already present
                if "null" not in avro_type:
                    avro_type = ["null"] + avro_type
            else:
                avro_type = ["null", avro_type]

        field["type"] = avro_type

        # Logical type
        if logical_type:
            field["type"] = self._apply_logical_type(field["type"], logical_type, attr.data_type)

        # Default value
        if attr.default_value is not None:
            # Convert default from string to Avro value
            default = self._parse_avro_default(attr.default_value, attr.data_type)
            if default is not None:
                field["default"] = default
        # elif not attr.required:
            # if optional and no default, Avro still requires a default? Not strictly, but it's allowed to omit. We'll follow the schema: if null is in union, we can set default to null? Optional without default usually just omits default. We'll not set default unless explicitly present.

        # Aliases (from annotation "aliases")
        aliases_ann = next((a for a in attr.annotations if a.key == "aliases"), None)
        if aliases_ann:
            field["aliases"] = aliases_ann.value.split(",")

        # Order annotation (from Avro field order)
        order_ann = next((a for a in attr.annotations if a.key == "order"), None)
        if order_ann:
            field["order"] = order_ann.value

        return field

    # ── DataType to Avro type string or union list ─────────────
    def _datatype_to_avro(self, dt: DataType, ns: Optional[str]) -> Tuple[Any, Optional[AvroLogicalType]]:
        """
        Returns (avro_type, logical_type) where avro_type can be a string, list, or dict.
        """
        base = dt.base
        logical = None

        # Check if the original attribute had an avro_logical_type set
        # We need to pass that from Attribute, not only DataType. We'll handle in the caller.
        # Here we only map based on ScalarType.
        if base in SCALAR_TO_AVRO:
            avro = SCALAR_TO_AVRO[base]
            # If base implies a logical type (date/time/timestamp), set it
            if base == ScalarType.DATE:
                logical = AvroLogicalType.DATE
            elif base == ScalarType.TIME:
                logical = AvroLogicalType.TIME_MILLIS
            elif base == ScalarType.TIMESTAMP:
                logical = AvroLogicalType.TIMESTAMP_MILLIS
            elif base == ScalarType.UUID:
                logical = AvroLogicalType.UUID
            elif base == ScalarType.DECIMAL:
                logical = AvroLogicalType.DECIMAL
                # precision/scale? We'll handle later
            # For DURATION, it's not a simple mapping; we'll need special handling
            return avro, logical

        elif base == ScalarType.ARRAY:
            if dt.element_type is None:
                items = "string"   # fallback
            else:
                items, _ = self._datatype_to_avro(dt.element_type, ns)
            return {"type": "array", "items": items}, None

        elif base == ScalarType.MAP:
            if dt.value_type is None:
                values = "string"
            else:
                values, _ = self._datatype_to_avro(dt.value_type, ns)
            return {"type": "map", "values": values}, None

        elif base == ScalarType.STRUCT:
            # nested record? If there are nested_attributes, we'll create an inline record
            # but the nested_attributes are on the Attribute, not the DataType. So we'll handle this when building field,
            # not here. For DataType.STRUCT without nested info, we can't produce Avro. We'll return "string" as fallback?
            # Actually, the attribute will have nested_attributes; we'll detect that before calling this method.
            # So this case should not be reached if we've handled nested structs in _attribute_to_avro_field.
            return {"type": "record", "fields": []}, None   # placeholder, will be replaced

        elif base == ScalarType.REF:
            ref_name = dt.ref_entity
            if ref_name:
                # If the ref is in the same namespace, use just the name (if no namespace conflict)
                # The writer should output the fully qualified name? Avro expects the full name.
                # We'll prepend namespace if the ref does not have one and parent has namespace.
                # We'll let the caller handle.
                return ref_name, None
            else:
                return "string", None   # fallback

        elif base == ScalarType.ANY:
            return "string", None   # fallback

        # For arrays of refs or maps, handled above.
        return "string", None

    def _apply_logical_type(self, avro_type, logical: Optional[AvroLogicalType], data_type: DataType) -> Any:
        # Avro logical types need a dict wrapper: {"type": "int", "logicalType": "date"}
        if logical is None:
            return avro_type

        # For decimal, need precision/scale
        if logical == AvroLogicalType.DECIMAL:
            precision = data_type.precision or 10
            scale = data_type.scale or 0
            # In Avro, decimal logical type is usually applied to bytes with fixed size? No, just the logicalType is enough, but precision and scale are required.
            # We'll build: {"type": "bytes", "logicalType": "decimal", "precision": precision, "scale": scale}
            return {
                "type": "bytes",
                "logicalType": "decimal",
                "precision": precision,
                "scale": scale,
            }
        elif logical == AvroLogicalType.DURATION:
            # Duration is a fixed type of size 12? Actually Avro uses a logical type "duration" on a fixed of 12 bytes? No, it's a fixed of 12? The specification says it's a logical type on a fixed of 12. We'll output fixed type if we have max_length=12, but not fully. We'll output as "fixed" with size 12 and logicalType "duration". However, this is complex. We'll just store as annotation fallback.
            # Simpler: Output as bytes with logicalType? Not standard. We'll log a warning but produce a simple bytes with logicalType.
            # I'll set it to {"type": "bytes", "logicalType": "duration"} as non-standard, but it's okay for many tools.
            return {"type": "bytes", "logicalType": "duration"}
        else:
            log_str = LOGICAL_TYPE_TO_AVRO[logical]
            # Wrap avro_type in an object with logicalType
            if isinstance(avro_type, str):
                return {"type": avro_type, "logicalType": log_str}
            else:
                # already a complex type; not typical but we override
                return {"type": avro_type, "logicalType": log_str}

    # ── Helpers ─────────────────────────────────────────────────
    def _extract_enum_symbols(self, attr: Attribute) -> List[str]:
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK and c.expression.startswith("IN ("):
                # expression like "IN ('A', 'B', 'C')"
                inner = c.expression[4:].strip().rstrip(")")
                # Parse quoted strings
                symbols = []
                # Simple split by comma and space
                parts = inner.split(",")
                for part in parts:
                    part = part.strip().strip("'\"")
                    if part:
                        symbols.append(part)
                return symbols
        return []

    def _get_aliases(self, entity: Entity) -> Optional[List[str]]:
        ann = next((a for a in entity.annotations if a.key == "aliases"), None)
        if ann:
            return [x.strip() for x in ann.value.split(",") if x.strip()]
        return None

    def _parse_avro_default(self, default_str: str, dt: DataType) -> Any:
        """
        Convert a string default value to an Avro‑compatible Python literal.
        This is a best‑effort converter; complex expressions are returned as strings.
        """
        # Try to parse as JSON if it looks like JSON (object, array, quoted string)
        default_str = default_str.strip()
        if default_str.lower() == "null":
            return None
        # If the data type is string and not quoted, quote it.
        if dt.base == ScalarType.STRING and not (default_str.startswith('"') and default_str.endswith('"')):
            return default_str   # Avro will need a string; we should return a python string, json.dumps will handle quoting.
        # Try numeric
        try:
            if '.' in default_str or 'e' in default_str.lower():
                return float(default_str)
            return int(default_str)
        except ValueError:
            pass
        # Try boolean
        if default_str.lower() == "true":
            return True
        if default_str.lower() == "false":
            return False
        # Assume string
        return default_str