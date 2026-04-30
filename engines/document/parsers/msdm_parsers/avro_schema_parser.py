# engines/document/parsers/msdm_parsers/avro_schema_parser.py
"""
Avro Schema Parser – converts .avsc files into MSDMDocument.
Supports all Avro types: primitives, logical types, records, enums,
fixed, arrays, maps, unions, and recursive schemas.
Maps every detail faithfully for lossless round‑trip.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple

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
    AvroLogicalType,
)

# ── Mappings ────────────────────────────────────────────────────
AVRO_PRIMITIVES = {
    "null":    ScalarType.ANY,          # null is a valid primitive in unions
    "boolean": ScalarType.BOOLEAN,
    "int":     ScalarType.INT,
    "long":    ScalarType.LONG,
    "float":   ScalarType.FLOAT,
    "double":  ScalarType.DOUBLE,
    "bytes":   ScalarType.BINARY,
    "string":  ScalarType.STRING,
}

LOGICAL_TYPE_MAP = {
    "decimal":            AvroLogicalType.DECIMAL,
    "date":               AvroLogicalType.DATE,
    "time-millis":        AvroLogicalType.TIME_MILLIS,
    "time-micros":        AvroLogicalType.TIME_MICROS,
    "timestamp-millis":   AvroLogicalType.TIMESTAMP_MILLIS,
    "timestamp-micros":   AvroLogicalType.TIMESTAMP_MICROS,
    "duration":           AvroLogicalType.DURATION,
    "uuid":               AvroLogicalType.UUID,
}


class AvroSchemaParser(BaseMSDMParser):
    """Parser for Apache Avro Schema files (.avsc)."""
    name = "avro_schema"
    supported_extensions = (".avsc",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raw_schema = json.loads(text)

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem   # fallback namespace

        # Avro schema can be a single definition, a list, or an unnamed type
        if isinstance(raw_schema, list):
            for entry in raw_schema:
                self._process_schema_entry(entry, doc)
        elif isinstance(raw_schema, dict):
            self._process_schema_entry(raw_schema, doc)
        else:
            # primitive type only – create a placeholder entity
            dt = self._parse_type(raw_schema, doc, doc.namespace)
            entity = Entity(name="root", kind=EntityKind.OBJECT)
            entity.attributes.append(Attribute(name="value", data_type=dt))
            doc.entities.append(entity)

        return doc

    # ── Top‑level dispatch ──────────────────────────────────────
    def _process_schema_entry(self, obj: dict, doc: MSDMDocument) -> None:
        """
        Dispatch a single top‑level schema entry.
        It may be a record, enum, fixed, or a named type with namespace.
        """
        avro_type = obj.get("type")
        if isinstance(avro_type, str):
            if avro_type == "record":
                self._parse_record(obj, doc)
            elif avro_type == "enum":
                self._parse_enum(obj, doc)
            elif avro_type == "fixed":
                self._parse_fixed(obj, doc)
        elif isinstance(avro_type, dict):
            # Inline type definition (record/enum/fixed) without a top-level name
            # We'll treat it as an anonymous entity
            self._parse_inline_type(avro_type, doc, doc.namespace, "anonymous")
        elif isinstance(avro_type, list):
            # Union at top-level is unusual; create a wrapper entity
            entity = Entity(name="root", kind=EntityKind.OBJECT)
            attr = self._field_from_union(avro_type, doc, doc.namespace, "value")
            entity.attributes.append(attr)
            doc.entities.append(entity)

    # ── Parsing named types ─────────────────────────────────────
    def _parse_record(self, obj: dict, doc: MSDMDocument) -> Entity:
        name = obj["name"]
        namespace = obj.get("namespace", doc.namespace)
        full_name = f"{namespace}.{name}" if namespace else name
        doc_str = obj.get("doc")

        entity = Entity(
            name=full_name,
            kind=EntityKind.OBJECT,
            description=doc_str,
            namespace=namespace,
        )
        # Aliases
        if "aliases" in obj:
            entity.annotations.append(Annotation(key="aliases", value=",".join(obj["aliases"])))

        # Fields
        for field in obj.get("fields", []):
            attr = self._parse_field(field, doc, namespace, full_name)
            entity.attributes.append(attr)

        doc.entities.append(entity)
        return entity

    def _parse_enum(self, obj: dict, doc: MSDMDocument) -> Entity:
        name = obj["name"]
        namespace = obj.get("namespace", doc.namespace)
        full_name = f"{namespace}.{name}" if namespace else name
        desc = obj.get("doc")

        entity = Entity(
            name=full_name,
            kind=EntityKind.OBJECT,
            description=desc,
            namespace=namespace,
        )
        if "aliases" in obj:
            entity.annotations.append(Annotation(key="aliases", value=",".join(obj["aliases"])))

        symbols = obj.get("symbols", [])
        # Represent enum as an entity with one attribute "value" and a CHECK constraint
        attr = Attribute(
            name="value",
            data_type=DataType(base=ScalarType.STRING),
            required=True,
        )
        if symbols:
            quoted = ", ".join(repr(s) for s in symbols)
            attr.constraints.append(Constraint(
                type=ConstraintType.CHECK,
                expression=f"IN ({quoted})",
                name=f"enum_{full_name}_values"
            ))
        entity.attributes.append(attr)
        doc.entities.append(entity)
        return entity

    def _parse_fixed(self, obj: dict, doc: MSDMDocument) -> Entity:
        name = obj["name"]
        namespace = obj.get("namespace", doc.namespace)
        full_name = f"{namespace}.{name}" if namespace else name
        size = obj.get("size", 0)
        desc = obj.get("doc")

        entity = Entity(
            name=full_name,
            kind=EntityKind.OBJECT,
            description=desc,
            namespace=namespace,
        )
        if "aliases" in obj:
            entity.annotations.append(Annotation(key="aliases", value=",".join(obj["aliases"])))

        attr = Attribute(
            name="bytes",
            data_type=DataType(base=ScalarType.BINARY, max_length=size),
            required=True,
        )
        entity.attributes.append(attr)
        doc.entities.append(entity)
        return entity

    # ── Field parsing ───────────────────────────────────────────
    def _parse_field(self, field: dict, doc: MSDMDocument, namespace: str,
                     parent_full_name: str) -> Attribute:
        name = field["name"]
        desc = field.get("doc")
        type_obj = field["type"]

        # Determine if the field is nullable (union with null)
        nullable, remaining_types = self._extract_null_from_union(type_obj)
        if nullable and len(remaining_types) == 1:
            # Only one non-null type
            data_type = self._parse_type(remaining_types[0], doc, namespace)
        else:
            data_type = self._parse_type(type_obj, doc, namespace)

        attr = Attribute(
            name=name,
            data_type=data_type,
            required=not nullable,
            description=desc,
        )

        # Default value
        if "default" in field:
            default_val = field["default"]
            if default_val is not None:
                attr.default_value = str(default_val)
            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                               expression=json.dumps(default_val)))

        # Logical type (either on the field directly or on the type object)
        logical = field.get("logicalType")
        if logical:
            attr.avro_logical_type = LOGICAL_TYPE_MAP.get(logical)
        elif isinstance(type_obj, dict) and "logicalType" in type_obj:
            attr.avro_logical_type = LOGICAL_TYPE_MAP.get(type_obj["logicalType"])

        # Field ordering (order attribute in Avro)
        order = field.get("order")
        if order:
            attr.annotations.append(Annotation(key="order", value=order))

        # Aliases on field
        aliases = field.get("aliases")
        if aliases:
            attr.annotations.append(Annotation(key="aliases", value=",".join(aliases)))

        # If the field's data type is STRUCT and was derived from a union, we need to store
        # the union details (nested attributes) inside attr.nested_attributes.
        # However, _parse_type may have already built a synthetic struct entity for unions.
        # We'll ensure _parse_type for unions returns a STRUCT with a linked entity or nested_attributes.
        if isinstance(type_obj, list) and not nullable:
            # Pure union (no null) – handle as special
            attr.nested_attributes = self._build_union_nested_attrs(type_obj, doc, namespace)
            attr.data_type = DataType(base=ScalarType.STRUCT)
        elif nullable and len(remaining_types) > 1:
            # Multiple non-null union members – also needs struct
            attr.nested_attributes = self._build_union_nested_attrs(remaining_types, doc, namespace)
            # data_type already set to STRUCT by _parse_type
            attr.data_type = DataType(base=ScalarType.STRUCT)

        return attr

    # ── Type parsing ────────────────────────────────────────────
    def _parse_type(self, type_obj, doc: MSDMDocument, namespace: str) -> DataType:
        """
        Convert an Avro type (string, dict, or list) to a DataType.
        """
        if isinstance(type_obj, str):
            if type_obj in AVRO_PRIMITIVES:
                return DataType(base=AVRO_PRIMITIVES[type_obj])
            else:
                # Named type reference
                return DataType(base=ScalarType.REF, ref_entity=type_obj)

        if isinstance(type_obj, list):
            # Union – unwrap null and treat remaining
            nullable, remaining = self._extract_null_from_union(type_obj)
            if len(remaining) == 1:
                # Only one non-null type
                return self._parse_type(remaining[0], doc, namespace)
            elif len(remaining) == 0:
                return DataType(base=ScalarType.ANY)   # only null
            else:
                # Multiple non-null types – represent as struct
                return DataType(base=ScalarType.STRUCT)

        if isinstance(type_obj, dict):
            typ = type_obj.get("type")
            if typ == "array":
                items = type_obj["items"]
                elem_type = self._parse_type(items, doc, namespace)
                return DataType(base=ScalarType.ARRAY, element_type=elem_type)
            elif typ == "map":
                values = type_obj["values"]
                val_type = self._parse_type(values, doc, namespace)
                return DataType(base=ScalarType.MAP,
                                key_type=DataType(base=ScalarType.STRING),
                                value_type=val_type)
            elif typ == "enum":
                entity = self._parse_enum(type_obj, doc)
                return DataType(base=ScalarType.REF, ref_entity=entity.name)
            elif typ == "record":
                entity = self._parse_record(type_obj, doc)
                return DataType(base=ScalarType.REF, ref_entity=entity.name)
            elif typ == "fixed":
                entity = self._parse_fixed(type_obj, doc)
                return DataType(base=ScalarType.REF, ref_entity=entity.name)
            else:
                # Unknown, fallback
                return DataType(base=ScalarType.ANY)

        return DataType(base=ScalarType.ANY)

    # ── Union helpers ──────────────────────────────────────────
    @staticmethod
    def _extract_null_from_union(type_obj) -> Tuple[bool, list]:
        """Check if a type is a union containing null, and return (has_null, remaining_types)."""
        if isinstance(type_obj, list):
            has_null = any(t == "null" for t in type_obj)
            remaining = [t for t in type_obj if t != "null"]
            return has_null, remaining
        return False, []

    def _build_union_nested_attrs(self, types: list, doc: MSDMDocument,
                                  namespace: str) -> List[Attribute]:
        """
        Create nested attributes for each member of a union (excluding null).
        Each attribute is optional.
        """
        attrs = []
        for i, member in enumerate(types):
            if member == "null":
                continue
            dt = self._parse_type(member, doc, namespace)
            attr = Attribute(
                name=f"member_{i}",
                data_type=dt,
                required=False,
            )
            attrs.append(attr)
        return attrs

    # ── Inline type (anonymous) ─────────────────────────────────
    def _parse_inline_type(self, obj: dict, doc: MSDMDocument, namespace: str,
                           base_name: str) -> Entity:
        """Parse an inline record/enum/fixed and create an entity with a generated name."""
        typ = obj.get("type")
        name = obj.get("name", f"{base_name}_{typ}")
        # Temporarily set a name and parse
        obj = obj.copy()
        obj["name"] = name
        if typ == "record":
            return self._parse_record(obj, doc)
        elif typ == "enum":
            return self._parse_enum(obj, doc)
        elif typ == "fixed":
            return self._parse_fixed(obj, doc)
        else:
            # Should not happen
            raise ValueError(f"Unknown inline type: {typ}")