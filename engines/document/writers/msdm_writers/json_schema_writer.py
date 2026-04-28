# engines/document/writers/msdm_writers/json_schema_writer.py
"""
JSON Schema Writer – converts an MSDMDocument into a JSON Schema document.
Supports draft‑04 through 2020‑12.  Faithfully reproduces schema keywords
either directly from the model or from round‑trip annotations stored by the
parser.  Soft‑delete is ignored.
"""

from __future__ import annotations
import json
from typing import Optional, Dict, Any, List, Set, Union

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

# ── JSON Schema keywords that can appear at the schema / object level ──
_TOP_KEYWORDS: Set[str] = {
    "$schema", "$id", "$ref", "$defs", "definitions",
    "title", "description", "type",
    "properties", "required", "additionalProperties",
    "minProperties", "maxProperties",
    "dependencies", "dependentRequired", "dependentSchemas",
    "patternProperties",
    "allOf", "anyOf", "oneOf", "not",
    "if", "then", "else",
    "propertyNames", "unevaluatedProperties", "unevaluatedItems",
    "$comment", "$vocabulary", "$dynamicRef",
}

# ── Property‑level JSON Schema keywords ────────────────────────────
_PROPERTY_KEYWORDS: Set[str] = _TOP_KEYWORDS | {
    "items", "additionalItems", "contains",
    "minItems", "maxItems", "uniqueItems",
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "multipleOf",
    "minLength", "maxLength", "pattern",
    "format",
    "enum", "const",
    "default", "examples",
    "contentMediaType", "contentEncoding",
    "description",
    "properties",
    "required",
}

# ── ScalarType → default JSON Schema type ─────────────────────────
_SCALAR_TO_JSON_TYPE: Dict[ScalarType, str] = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "integer",
    ScalarType.LONG:      "integer",
    ScalarType.FLOAT:     "number",
    ScalarType.DOUBLE:    "number",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.DATE:      "string",
    ScalarType.TIME:      "string",
    ScalarType.TIMESTAMP: "string",
    ScalarType.DURATION:  "string",
    ScalarType.UUID:      "string",
    ScalarType.BINARY:    "string",
    ScalarType.DECIMAL:   "number",
    ScalarType.ANY:       None,          # "type" omitted or "object"
}

# ── ScalarType → format hint ─────────────────────────────────────
_SCALAR_TO_FORMAT: Dict[ScalarType, str] = {
    ScalarType.DATE:      "date",
    ScalarType.TIME:      "time",
    ScalarType.TIMESTAMP: "date-time",
    ScalarType.DURATION:  "duration",
    ScalarType.UUID:      "uuid",
    ScalarType.BINARY:    "byte",        # not standard but hints
}


class JsonSchemaWriter(BaseMSDMWriter):
    """Writer for JSON Schema files (.schema.json)."""
    name = "json_schema"
    supported_extensions = (".schema.json",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        # Use the first entity as the main schema, or generate a wrapper
        if not document.entities:
            schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        else:
            entity = document.entities[0]
            schema = self._entity_to_schema(entity, document)

        json_str = json.dumps(schema, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["application/schema+json"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity → JSON Schema object ────────────────────────────────
    def _entity_to_schema(self, entity: Entity, doc: MSDMDocument) -> Dict[str, Any]:
        schema: Dict[str, Any] = {}

        # 1. Schema‑level annotations (the parser stored $schema, $id, etc. as annotations)
        for ann in entity.annotations:
            if ann.key in _TOP_KEYWORDS:
                self._apply_annotation_to_schema(schema, ann)

        # 2. Title & description from entity fields
        if entity.name and "title" not in schema:
            schema["title"] = entity.name
        if entity.description and "description" not in schema:
            schema["description"] = entity.description

        # 3. Type – prefer annotation, then infer from entity kind
        if "type" not in schema:
            schema["type"] = "object"   # default

        # 4. Properties and required – always rebuild from model to ensure consistency
        properties = {}
        required = []
        for attr in entity.attributes:
            prop_schema = self._attribute_to_property_schema(attr)
            # Overlay any attribute annotations that are JSON Schema keywords
            self._overlay_attribute_annotations(prop_schema, attr)
            properties[attr.name] = prop_schema
            if attr.required:
                required.append(attr.name)

        if properties:
            schema["properties"] = properties
        if required:
            schema["required"] = required

        # 5. Composition keywords (allOf, etc.) may already be in schema from annotations.
        #    We keep them as is.

        # 6. $defs / definitions – if the document stored them as annotations, add them.
        #    The parser might have stored them on the document object; we'll check doc.annotations.
        defs = self._extract_defs(doc)
        if defs:
            schema["$defs"] = defs

        return schema

    # ── Attribute → property schema ────────────────────────────────
    def _attribute_to_property_schema(self, attr: Attribute) -> Dict[str, Any]:
        prop: Dict[str, Any] = {}

        # Determine type from DataType (overridden by annotation later)
        dt = attr.data_type
        base = dt.base

        if base == ScalarType.ARRAY:
            prop["type"] = "array"
            if dt.element_type:
                items = {}
                self._add_type_to_property(items, dt.element_type)
                if items:
                    prop["items"] = items
        elif base == ScalarType.MAP:
            prop["type"] = "object"
            # JSON Schema doesn't have native map; we can output patternProperties or additionalProperties
            # For simplicity, we output additionalProperties with the value type
            val_schema = self._datatype_to_basic_property(dt.value_type) if dt.value_type else {}
            if val_schema:
                prop["additionalProperties"] = val_schema
        elif base == ScalarType.REF:
            prop["$ref"] = f"#/$defs/{dt.ref_entity}" if dt.ref_entity else "#"
        elif base == ScalarType.STRUCT:
            prop["type"] = "object"
            # Nested attributes are not directly available here; they are on the attribute's nested_attributes.
            # We'll handle specially below.
        else:
            self._add_type_to_property(prop, dt)

        # Description
        if attr.description:
            prop["description"] = attr.description

        # Default value
        if attr.default_value is not None:
            prop["default"] = self._parse_json_value(attr.default_value)

        # Constraints from model (these may be duplicated in annotations; we'll set here and let overlay override)
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK:
                # Store as annotation later; not directly convertible
                pass
            elif c.type == ConstraintType.DEFAULT:
                pass   # already handled

        # Nested properties for STRUCT
        if base == ScalarType.STRUCT and attr.nested_attributes:
            nested_props = {}
            nested_req = []
            for na in attr.nested_attributes:
                nested_props[na.name] = self._attribute_to_property_schema(na)
                if na.required:
                    nested_req.append(na.name)
            prop["properties"] = nested_props
            if nested_req:
                prop["required"] = nested_req

        return prop

    def _overlay_attribute_annotations(self, prop_schema: Dict[str, Any], attr: Attribute) -> None:
        """Merge JSON Schema keywords from annotations into the property schema."""
        for ann in attr.annotations:
            if ann.key in _PROPERTY_KEYWORDS:
                # Deserialise the value from its string representation
                try:
                    val = json.loads(ann.value)
                except (json.JSONDecodeError, TypeError):
                    val = ann.value
                # Special merge for certain keywords (like "enum" array)
                if ann.key == "enum" and "enum" in prop_schema:
                    # Avoid overwriting if already present from model? We'll trust annotation
                    pass
                prop_schema[ann.key] = val

    def _apply_annotation_to_schema(self, schema: Dict[str, Any], ann: Annotation) -> None:
        """Parse an annotation value and insert it into the schema dict."""
        try:
            val = json.loads(ann.value)
        except (json.JSONDecodeError, TypeError):
            val = ann.value
        # Avoid overwriting properties/required that we built from model
        if ann.key in ("properties", "required"):
            return
        schema[ann.key] = val

    # ── Type mapping helpers ───────────────────────────────────────
    @staticmethod
    def _add_type_to_property(prop: Dict[str, Any], dt: DataType) -> None:
        """Set 'type' and optionally 'format' for a scalar DataType."""
        base = dt.base
        json_type = _SCALAR_TO_JSON_TYPE.get(base)
        if json_type:
            prop["type"] = json_type
        fmt = _SCALAR_TO_FORMAT.get(base)
        if fmt:
            prop["format"] = fmt

    @staticmethod
    def _datatype_to_basic_property(dt: Optional[DataType]) -> Dict[str, Any]:
        """Create a minimal property dict for a value type (used in map/array)."""
        if dt is None:
            return {}
        prop = {}
        JsonSchemaWriter._add_type_to_property(prop, dt)
        return prop

    @staticmethod
    def _parse_json_value(raw: str) -> Any:
        """Convert a default value string to a JSON literal."""
        raw = raw.strip()
        if raw == "null":
            return None
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        if raw.lower() in ("true", "false"):
            return raw.lower() == "true"
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            return raw[1:-1]
        return raw

    def _extract_defs(self, doc: MSDMDocument) -> Optional[Dict[str, Any]]:
        """Extract $defs/definitions from document annotations (round‑trip)."""
        for ann in doc.annotations:
            if ann.key in ("$defs", "definitions"):
                try:
                    return json.loads(ann.value)
                except json.JSONDecodeError:
                    return None
        return None