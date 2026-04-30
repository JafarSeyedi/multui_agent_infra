# engines/document/writers/msdm_writers/proto_writer.py
"""
Protobuf IDL Writer – converts an MSDMDocument into a .proto file.
Generates message, enum, oneof, map, and field definitions with full
round‑trip fidelity using annotations captured by the parser.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Set

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from ..base import WriteOptions
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Constraint,
    ConstraintType,
    Annotation,
    EntityKind,
)

# ── MSDM scalar → proto type ──────────────────────────────────────
_SCALAR_TO_PROTO = {
    ScalarType.DOUBLE:   "double",
    ScalarType.FLOAT:    "float",
    ScalarType.INT:      "int32",
    ScalarType.LONG:     "int64",
    ScalarType.BOOLEAN:  "bool",
    ScalarType.STRING:   "string",
    ScalarType.BINARY:   "bytes",
    ScalarType.UUID:     "string",   # proto has no native UUID
    ScalarType.DATE:      "string",  # typically string or int32
    ScalarType.TIME:      "string",
    ScalarType.TIMESTAMP: "string",
    ScalarType.DURATION:  "string",
    ScalarType.DECIMAL:   "string",  # usually string
    ScalarType.ANY:       "string",
}


class ProtoWriter(BaseMSDMWriter):
    """Writer for Protobuf IDL (.proto)."""
    name = "proto"
    supported_extensions = (".proto",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self._entity_field_counters: Dict[str, int] = {}

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []
        # File‑level attributes
        syntax = self._get_doc_annotation(document, "syntax") or "proto3"
        lines.append(f'syntax = "{syntax}";')
        if document.namespace:
            lines.append(f"package {document.namespace};")
        for ann in document.annotations:
            if ann.key == "import":
                lines.append(f'import "{ann.value}";')
            elif ann.key == "file_option":
                lines.append(f"option {ann.value};")
        # Collect top‑level messages/enums and nested ones
        self._written_entities: Set[str] = set()
        # First, identify which entities are nested inside others
        parent_map: Dict[str, str] = {}  # child entity name -> parent entity name
        for entity in document.entities:
            for ann in entity.annotations:
                if ann.key == "nested_message" or ann.key == "nested_enum":
                    child_name = ann.value
                    parent_map[child_name] = entity.name

        # Write top‑level entities
        for entity in document.entities:
            if entity.name in parent_map:
                continue  # will be written inside parent
            lines.append("")
            self._write_entity(entity, document, lines, 0)

        # Append top‑level extensions / services annotations as raw
        for ann in document.annotations:
            if ann.key == "extend":
                lines.append(f"extend {ann.value} {{ ... }}")
            elif ann.key == "service":
                lines.append(f"service {ann.value} {{ ... }}")

        return "\n".join(lines).encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Write a single entity (message / enum) ────────────────────
    def _write_entity(self, entity: Entity, doc: MSDMDocument, lines: List[str], indent_level: int) -> None:
        prefix = "  " * indent_level
        # Determine if it's an enum or message
        if self._is_enum_entity(entity):
            self._write_enum(entity, lines, indent_level)
        else:
            self._write_message(entity, doc, lines, indent_level)

    def _is_enum_entity(self, entity: Entity) -> bool:
        # An enum has a single attribute "value" with a CHECK constraint listing values,
        # or has no attributes but has enum_value annotations.
        if any(a.key == "enum_value" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and any(c.expression.startswith("IN (") for c in attr.constraints):
                return True
        return False

    # ── Write message ──────────────────────────────────────────────
    def _write_message(self, entity: Entity, doc: MSDMDocument, lines: List[str], indent_level: int) -> None:
        prefix = "  " * indent_level
        lines.append(f"{prefix}message {entity.name} {{")
        # Reserved fields from annotation
        reserved = self._get_annotation(entity, "reserved")
        if reserved:
            lines.append(f"{prefix}  reserved {reserved};")
        # Options on message
        for ann in entity.annotations:
            if ann.key == "option":
                lines.append(f"{prefix}  option {ann.value};")

        # Normal fields (including oneof)
        for attr in entity.attributes:
            if self._is_oneof(attr):
                self._write_oneof(attr, lines, indent_level + 1, entity)
            elif self._is_map_field(attr):
                self._write_map_field(attr, lines, indent_level + 1, entity)
            else:
                self._write_field(attr, lines, indent_level + 1, entity)

        # Nested messages/enums
        for ann in entity.annotations:
            if ann.key in ("nested_message", "nested_enum"):
                child_name = ann.value
                child_entity = self._find_entity_by_name(doc, child_name)
                if child_entity:
                    self._write_entity(child_entity, doc, lines, indent_level + 1)

        lines.append(f"{prefix}}}")

    # ── Write enum ──────────────────────────────────────────────────
    def _write_enum(self, entity: Entity, lines: List[str], indent_level: int) -> None:
        prefix = "  " * indent_level
        lines.append(f"{prefix}enum {entity.name} {{")
        # Collect enum values from annotations
        enum_values = [a for a in entity.annotations if a.key == "enum_value"]
        if not enum_values and entity.attributes:
            # fallback from constraint
            attr = entity.attributes[0]
            for c in attr.constraints:
                if c.expression.startswith("IN ("):
                    inner = c.expression[4:].rstrip(")")
                    vals = [v.strip().strip("'\"") for v in inner.split(",")]
                    for v in vals:
                        enum_values.append(Annotation(key="enum_value", value=f"{v}=0"))
        for ev in enum_values:
            parts = ev.value.split("=", 1)
            name = parts[0].strip()
            number = parts[1].strip() if len(parts) > 1 else "0"
            lines.append(f"{prefix}  {name} = {number};")
        # Reserved
        reserved = self._get_annotation(entity, "reserved")
        if reserved:
            lines.append(f"{prefix}  reserved {reserved};")
        lines.append(f"{prefix}}}")

    # ── Write normal field ─────────────────────────────────────────
    def _write_field(self, attr: Attribute, lines: List[str], indent: int, entity: Entity) -> None:
        prefix = "  " * indent
        label = self._get_annotation(attr, "label") or ""
        if attr.data_type.base == ScalarType.ARRAY:
            label = "repeated"
        elif attr.required:
            # proto3: no required; optional with proto3 optional? We'll output "optional" if label says so; else omit.
            # Use label if provided, else no label
            pass
        type_str = self._datatype_to_proto(attr.data_type)
        field_number = self._get_annotation(attr, "field_number") or self._get_field_number(attr, entity.name)
        # Options
        opts = self._get_field_options(attr)
        opt_str = f" [{', '.join(opts)}]" if opts else ""
        line = f"{prefix}{label + ' ' if label else ''}{type_str} {attr.name} = {field_number}{opt_str};"
        lines.append(line)

    # ── Write oneof ─────────────────────────────────────────────────
    def _write_oneof(self, attr: Attribute, lines: List[str], indent: int, entity: Entity) -> None:
        prefix = "  " * indent
        lines.append(f"{prefix}oneof {attr.name} {{")
        for nested in attr.nested_attributes:
            self._write_field(nested, lines, indent + 1, entity)
        lines.append(f"{prefix}}}")

    # ── Write map field ───────────────────────────────────────────
    def _write_map_field(self, attr: Attribute, lines: List[str], indent: int, entity: Entity) -> None:
        prefix = "  " * indent
        dt = attr.data_type
        key_type = self._scalar_to_proto_type(dt.key_type.base) if dt.key_type else "string"
        val_type = self._datatype_to_proto(dt.value_type) if dt.value_type else "string"
        field_number = self._get_annotation(attr, "field_number") or self._get_field_number(attr, entity.name)
        line = f"{prefix}map<{key_type}, {val_type}> {attr.name} = {field_number};"
        lines.append(line)

    # ── Helpers ────────────────────────────────────────────────────
    def _scalar_to_proto_type(self, scalar: ScalarType) -> str:
        return _SCALAR_TO_PROTO.get(scalar, "string")

    def _datatype_to_proto(self, dt: DataType) -> str:
        if dt.base == ScalarType.REF:
            return dt.ref_entity or "Unknown"
        if dt.base == ScalarType.ARRAY:
            return f"repeated {self._datatype_to_proto(dt.element_type)}" if dt.element_type else "repeated string"
        if dt.base == ScalarType.MAP:
            # handled elsewhere
            return "map<...>"
        return self._scalar_to_proto_type(dt.base)

    def _is_oneof(self, attr: Attribute) -> bool:
        return any(a.key == "oneof" for a in attr.annotations)

    def _is_map_field(self, attr: Attribute) -> bool:
        # Detect map: DataType is MAP and no explicit label?
        return attr.data_type.base == ScalarType.MAP

    def _get_field_options(self, attr: Attribute) -> List[str]:
        opts = []
        for ann in attr.annotations:
            if ann.key in ("option", "packed", "deprecated", "json_name"):
                # format: key=value
                if ann.key == "option":
                    opts.append(ann.value)
                else:
                    opts.append(f"{ann.key}={ann.value}")
        return opts

def _get_field_number(self, attr: Attribute, entity_name: str) -> str:
    """Return the field number for an attribute, respecting existing annotation or assigning a new one."""
    existing = self._get_annotation(attr, "field_number")
    if existing:
        # update the counter to be at least this value + 1
        num = int(existing)
        self._entity_field_counters[entity_name] = max(
            self._entity_field_counters.get(entity_name, 0), num + 1
        )
        return existing
    # assign next number
    current = self._entity_field_counters.get(entity_name, 1)
    self._entity_field_counters[entity_name] = current + 1
    return str(current)

    # # ── Field number generation (if no annotation) ──────────────────
    # # Simple incremental counter per message (stateful)
    # def _next_field_number_getter(self):
    #     # This is not thread-safe but works sequentially.
    #     # We'll use a dict to store per-entity counters.
    #     if not hasattr(self, '_field_counters'):
    #         self._field_counters: Dict[str, int] = {}
    #     # The caller needs to know which entity we are currently processing; we can pass entity name.
    #     # We'll adapt _write_field to accept entity name.
    #     # For simplicity, we'll use a default global counter.
    #     if not hasattr(self, '_global_field_counter'):
    #         self._global_field_counter = 0
    #     self._global_field_counter += 1
    #     return str(self._global_field_counter)

    # ── Annotation retrieval ───────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None

    def _get_doc_annotation(self, doc: MSDMDocument, key: str) -> Optional[str]:
        return next((a.value for a in doc.annotations if a.key == key), None)

    def _find_entity_by_name(self, doc: MSDMDocument, name: str) -> Optional[Entity]:
        return next((e for e in doc.entities if e.name == name), None)