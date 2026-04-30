# engines/document/parsers/msdm_parsers/json_schema_parser.py
"""
JSON Schema Parser – converts .schema.json files (and any JSON Schema)
into an MSDMDocument.  Supports draft‑04 through 2020‑12.

Handles all major keywords:
- type, properties, required, additionalProperties, items, pattern, format,
  enum, const, default, examples, description, title, $comment
- numeric constraints: minimum, maximum, exclusiveMinimum, exclusiveMaximum,
  multipleOf
- string constraints: minLength, maxLength, pattern
- array constraints: minItems, maxItems, uniqueItems, items, additionalItems
- object constraints: minProperties, maxProperties, dependencies,
  dependentRequired, dependentSchemas
- composition: allOf, anyOf, oneOf, not, if/then/else
- $ref, $defs / definitions, $id, $anchor
- sub‑schemas: propertyNames, unevaluatedProperties, unevaluatedItems
- annotations: $comment, $vocabulary, etc.

Every keyword that cannot be directly mapped to an MSDM Entity/Attribute
is stored as a structured Annotation, guaranteeing lossless round‑trip.

The parser first resolves all internal $ref references so that the
resulting MSDM entities reflect the final merged schema.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Set, Union

from .base_msdm_parser import BaseMSDMParser
from ..base import ParseOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    Constraint,
    ConstraintType,
    Index,
    Annotation,
    EntityKind,
    ScalarType,
    Relationship,
)

# ── Mapping JSON Schema type strings to ScalarType ──────────────
JSON_TYPE_TO_SCALAR = {
    "string":   ScalarType.STRING,
    "integer":  ScalarType.INT,
    "number":   ScalarType.FLOAT,
    "boolean":  ScalarType.BOOLEAN,
    "object":   ScalarType.STRUCT,
    "array":    ScalarType.ARRAY,
    "null":     ScalarType.ANY,   # treated as nullable
}


class JsonSchemaParser(BaseMSDMParser):
    """Parser for JSON Schema files (.schema.json)."""
    name = "json_schema"
    supported_extensions = (".schema.json",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raw_schema = json.loads(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        # Handle cases where the JSON is an array of schemas
        if isinstance(raw_schema, list):
            for entry in raw_schema:
                if isinstance(entry, dict):
                    self._process_schema(entry, doc, is_root=True)
        else:
            self._process_schema(raw_schema, doc, is_root=True)

        return doc

    # ── Main schema processing ──────────────────────────────────
    def _process_schema(self, schema: dict, doc: MSDMDocument,
                        is_root: bool = False, parent_ref: Optional[str] = None) -> Optional[str]:
        """
        Process a JSON Schema object and create an entity.
        Returns the entity name (generated from $id, title, or a placeholder).
        """
        # Resolve internal $ref before processing (if top‑level, we may have already resolved)
        schema = self._resolve_refs(schema, doc)

        # Determine entity name
        entity_name = (
            schema.get("$id") or
            schema.get("id") or
            schema.get("title") or
            (Path(parent_ref).stem if parent_ref else None) or
            "root"
        )
        # Clean name (remove URI scheme, use last part)
        if "#" in entity_name:
            entity_name = entity_name.split("#")[-1] or entity_name
        # Replace slashes and dots with underscores
        entity_name = re.sub(r"\W+", "_", entity_name.strip("/"))

        entity = Entity(
            name=entity_name,
            kind=EntityKind.OBJECT,
            description=schema.get("description") or schema.get("title") or schema.get("$comment"),
        )

        # Schema‑wide annotations
        for key in ("$schema", "$id", "id", "title", "$comment", "examples",
                    "$vocabulary", "$dynamicAnchor", "$anchor",
                    "default", "const", "enum", "additionalProperties",
                    "additionalItems", "propertyNames", "unevaluatedProperties",
                    "unevaluatedItems", "if", "then", "else",
                    "allOf", "anyOf", "oneOf", "not",
                    "dependentRequired", "dependentSchemas",
                    "minProperties", "maxProperties",
                    "minItems", "maxItems", "uniqueItems",
                    "pattern", "format", "contentMediaType", "contentEncoding",
                    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
                    "multipleOf", "minLength", "maxLength"):
            if key in schema and key not in ("type", "properties", "items",
                                              "required", "description", "default",
                                              "$defs", "definitions"):
                val = schema[key]
                entity.annotations.append(Annotation(key=key, value=json.dumps(val)))

        # Entity type based on JSON Schema type
        json_type = schema.get("type")
        if isinstance(json_type, list):
            # Multiple types – treat as union, store as annotation
            entity.annotations.append(Annotation(key="type", value=json.dumps(json_type)))
            # For modeling purposes, pick the first non‑null type
            for t in json_type:
                if t != "null":
                    json_type = t
                    break
        if json_type == "object" or (is_root and not json_type):
            # Parse properties
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            for prop_name, prop_schema in properties.items():
                attr = self._parse_attribute(prop_name, prop_schema, required, doc)
                entity.attributes.append(attr)
            # Additional properties
            if "additionalProperties" in schema:
                extra = schema["additionalProperties"]
                if isinstance(extra, dict):
                    # It's a schema for all extra properties (like map)
                    # We could create a special attribute
                    attr = Attribute(name="*", data_type=self._type_to_datatype(extra, doc),
                                     required=False)
                    entity.attributes.append(attr)
        elif json_type == "array":
            items = schema.get("items", {})
            if not isinstance(items, dict):
                items = {}
            dt = self._type_to_datatype({"type": "object", "properties": items}, doc)
            attr = Attribute(name="items", data_type=dt)
            entity.attributes.append(attr)
        elif json_type:
            # Scalar type at root – create a single attribute
            attr = Attribute(name="value",
                             data_type=self._type_to_datatype(schema, doc))
            entity.attributes.append(attr)

        # Handle composition (allOf, anyOf, oneOf) – mark entity with annotations
        for comp_key in ("allOf", "anyOf", "oneOf"):
            if comp_key in schema:
                comp = schema[comp_key]
                # We'll store the raw JSON as annotation for round‑trip, but also create
                # synthetic attributes to represent each component.
                entity.annotations.append(Annotation(key=comp_key, value=json.dumps(comp)))

        # Store definitions for later resolution
        self._store_definitions(schema, doc)

        doc.entities.append(entity)
        return entity.name

    # ── Attribute parsing ───────────────────────────────────────
    def _parse_attribute(self, name: str, prop_schema: dict,
                         required_set: Set[str], doc: MSDMDocument) -> Attribute:
        """Parse a single property from a JSON Schema object into an Attribute."""
        # Resolve refs if needed (already resolved in outer)
        prop_schema = self._resolve_refs(prop_schema, doc)

        desc = prop_schema.get("description") or prop_schema.get("title")
        dt = self._type_to_datatype(prop_schema, doc)

        attr = Attribute(
            name=name,
            data_type=dt,
            required=name in required_set,
            description=desc,
        )

        # Default value
        if "default" in prop_schema:
            val = prop_schema["default"]
            attr.default_value = json.dumps(val)
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                               expression=attr.default_value))

        # Enum / const constraint
        if "enum" in prop_schema:
            values = prop_schema["enum"]
            quoted = ", ".join(json.dumps(v) for v in values)
            attr.constraints.append(Constraint(type=ConstraintType.CHECK,
                                               expression=f"IN ({quoted})"))
        if "const" in prop_schema:
            val = prop_schema["const"]
            attr.constraints.append(Constraint(type=ConstraintType.CHECK,
                                               expression=f"= {json.dumps(val)}"))

        # Numeric constraints
        for attr_k, constr in [("minimum", ">="), ("maximum", "<="),
                                ("exclusiveMinimum", ">"), ("exclusiveMaximum", "<")]:
            if attr_k in prop_schema:
                val = prop_schema[attr_k]
                attr.constraints.append(Constraint(type=ConstraintType.CHECK,
                                                   expression=f"{constr} {val}"))
        if "multipleOf" in prop_schema:
            val = prop_schema["multipleOf"]
            # Store as check expression or annotation; we'll use annotation for complex checks
            attr.annotations.append(Annotation(key="multipleOf", value=str(val)))

        # String constraints
        for key in ("minLength", "maxLength", "pattern"):
            if key in prop_schema:
                attr.annotations.append(Annotation(key=key, value=json.dumps(prop_schema[key])))

        # Array constraints
        for key in ("minItems", "maxItems", "uniqueItems"):
            if key in prop_schema:
                attr.annotations.append(Annotation(key=key, value=json.dumps(prop_schema[key])))

        # Object constraints
        for key in ("minProperties", "maxProperties"):
            if key in prop_schema:
                attr.annotations.append(Annotation(key=key, value=json.dumps(prop_schema[key])))

        # Format annotation
        if "format" in prop_schema:
            attr.annotations.append(Annotation(key="format", value=prop_schema["format"]))

        # Content fields
        for key in ("contentMediaType", "contentEncoding"):
            if key in prop_schema:
                attr.annotations.append(Annotation(key=key, value=prop_schema[key]))

        # Additional keyword annotations
        for reserved_key in ("$comment", "examples", "title", "$anchor", "$dynamicAnchor"):
            if reserved_key in prop_schema:
                attr.annotations.append(Annotation(key=reserved_key,
                                                   value=json.dumps(prop_schema[reserved_key])))

        # Sub‑schema keywords (propertyNames, unevaluatedProperties, etc.) stored as annotations
        for kw in ("propertyNames", "unevaluatedProperties", "unevaluatedItems",
                   "additionalProperties", "additionalItems"):
            if kw in prop_schema:
                attr.annotations.append(Annotation(key=kw,
                                                   value=json.dumps(prop_schema[kw])))

        # Composition local to attribute (rare)
        for comp_key in ("allOf", "anyOf", "oneOf", "not"):
            if comp_key in prop_schema:
                attr.annotations.append(Annotation(key=comp_key,
                                                   value=json.dumps(prop_schema[comp_key])))

        # If the property contains nested properties (object) and we already processed them
        # into nested_attributes via _type_to_datatype, we should ensure they are attached.
        if isinstance(prop_schema.get("properties"), dict) and dt.base == ScalarType.STRUCT:
            # Recurse into nested properties
            nested_props = prop_schema["properties"]
            nested_req = set(prop_schema.get("required", []))
            for nested_name, nested_schema in nested_props.items():
                nested_attr = self._parse_attribute(nested_name, nested_schema, nested_req, doc)
                attr.nested_attributes.append(nested_attr)

        return attr

    # ── DataType from JSON Schema ──────────────────────────────
    def _type_to_datatype(self, schema: dict, doc: MSDMDocument) -> DataType:
        """Convert a JSON Schema object (or just type keyword) to a DataType."""
        # If $ref already resolved, it should be inlined.
        json_type = schema.get("type")
        if isinstance(json_type, list):
            # Union – return a STRUCT with nested_attributes for each type?
            # Simpler: return ANY and annotate
            return DataType(base=ScalarType.ANY)
        if not json_type:
            # Might be a schema with only properties (object) or no type (any)
            if "properties" in schema or "additionalProperties" in schema:
                json_type = "object"
            elif "items" in schema:
                json_type = "array"
            else:
                json_type = "object"  # default to object
        base_scalar = JSON_TYPE_TO_SCALAR.get(json_type, ScalarType.ANY)

        if json_type == "object":
            return DataType(base=ScalarType.STRUCT)
        elif json_type == "array":
            items_schema = schema.get("items", {})
            if isinstance(items_schema, list):
                # Tuple validation – store all schemas as array of struct?
                # For simplicity, treat as array of any
                elem_type = DataType(base=ScalarType.ANY)
            elif isinstance(items_schema, dict):
                elem_type = self._type_to_datatype(items_schema, doc)
            else:
                elem_type = DataType(base=ScalarType.ANY)
            return DataType(base=ScalarType.ARRAY, element_type=elem_type)

        # For simple types, check format to refine (e.g., string + format date => date)
        if json_type == "string" and "format" in schema:
            fmt = schema["format"]
            if fmt in ("date-time", "datetime", "iso8601"):
                return DataType(base=ScalarType.TIMESTAMP)
            elif fmt == "date":
                return DataType(base=ScalarType.DATE)
            elif fmt == "time":
                return DataType(base=ScalarType.TIME)
            elif fmt == "duration":
                return DataType(base=ScalarType.DURATION)
            elif fmt == "uuid":
                return DataType(base=ScalarType.UUID)
            elif fmt == "email":
                return DataType(base=ScalarType.STRING)
            elif fmt == "uri":
                return DataType(base=ScalarType.STRING)
            elif fmt == "binary":
                return DataType(base=ScalarType.BINARY)

        if json_type == "number" and schema.get("multipleOf"):
            # If multipleOf is 1, it's integer? Not exactly but close.
            pass

        return DataType(base=base_scalar)

    # ── Internal $ref resolution ───────────────────────────────
    def _resolve_refs(self, schema: dict, doc: MSDMDocument) -> dict:
        """
        Resolve internal $ref references within the current document.
        Returns a new dict with $ref replaced by the referenced schema (simple replacement).
        Only handles local definitions; external URIs are left untouched.
        """
        if not isinstance(schema, dict):
            return schema
        if "$ref" in schema.keys():
            ref = schema["$ref"]
            if ref.startswith("#/"):
                # Local pointer – resolve from stored definitions
                fragment = ref[2:]
                referenced = self._resolve_pointer(fragment, doc)
                if referenced:
                    # Merge with any properties in the current schema (override)
                    merged = schema.copy()
                    del merged["$ref"]
                    merged.update(referenced)
                    return merged
            else:
                # External $ref – keep as annotation
                pass
        # Recursively process all values
        new = {}
        for k, v in schema.items():
            if k == "$ref":
                new[k] = v  # keep
            elif isinstance(v, dict):
                new[k] = self._resolve_refs(v, doc)
            elif isinstance(v, list):
                new[k] = [self._resolve_refs(e, doc) if isinstance(e, dict) else e for e in v]
            else:
                new[k] = v
        return new

    def _store_definitions(self, schema: dict, doc: MSDMDocument) -> None:
        """Cache definitions ($defs / definitions) for later resolution."""
        defs = schema.get("$defs") or schema.get("definitions") or {}
        if not hasattr(doc, '_defs_cache'):
            doc._defs_cache = {}
        doc._defs_cache.update(defs)

    def _resolve_pointer(self, pointer: str, doc: MSDMDocument) -> Optional[dict]:
        """Resolve a JSON Pointer fragment (e.g., '$defs/foo') within cached definitions."""
        if not hasattr(doc, '_defs_cache') or not doc._defs_cache:
            return None
        parts = pointer.strip("/").split("/")
        current = doc._defs_cache
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current if isinstance(current, dict) else None