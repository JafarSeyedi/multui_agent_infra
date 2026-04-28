# engines/document/writers/msdm_writers/thrift_idl_writer.py
"""
Apache Thrift IDL Writer – converts an MSDMDocument into a .thrift file.
Handles namespaces, includes, typedefs, enums, structs, unions, exceptions,
constants, and services.  Field options (required/optional, field id, default)
and file‑level directives are faithfully reproduced using annotations.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Set, Tuple

from .base_msdm_writer import BaseMSDMWriter, WriteTarget, SoftDeleteStrategy
from engines.document.writers.base import WriteOptions
from engines.document.models.msdm_models import (
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

# ── ScalarType → Thrift type ───────────────────────────────────────
_SCALAR_TO_THRIFT = {
    ScalarType.BOOLEAN:  "bool",
    ScalarType.INT:      "i32",
    ScalarType.LONG:     "i64",
    ScalarType.FLOAT:    "double",
    ScalarType.DOUBLE:   "double",
    ScalarType.STRING:   "string",
    ScalarType.BINARY:   "binary",
    ScalarType.DATE:     "string",          # no native date
    ScalarType.TIME:     "string",
    ScalarType.TIMESTAMP:"string",
    ScalarType.DURATION: "string",
    ScalarType.UUID:     "string",
    ScalarType.DECIMAL:  "string",
    ScalarType.ANY:      "string",
}


class ThriftIDLWriter(BaseMSDMWriter):
    """Writer for Apache Thrift IDL (.thrift)."""
    name = "thrift_idl"
    supported_extensions = (".thrift",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines: List[str] = []

        # 1. File‑level directives
        for ann in document.annotations:
            if ann.key in ("include", "cpp_include"):
                lines.append(f'{ann.key} "{ann.value}"')
            elif ann.key.startswith("namespace_"):
                # namespace_lang -> namespace lang ...
                lang = ann.key[10:]  # e.g., "java", "py"
                lines.append(f"namespace {lang} {ann.value}")
            elif ann.key == "php_namespace":
                lines.append(f"php_namespace {ann.value}")
        lines.append("")

        # 2. Typedefs (entities that are just aliases)
        for entity in document.entities:
            if self._is_typedef(entity):
                lines.append(self._build_typedef(entity))
        lines.append("")

        # 3. Enums
        for entity in document.entities:
            if self._is_enum(entity):
                lines.append(self._build_enum(entity))
                lines.append("")

        # 4. Structures, unions, exceptions
        for entity in document.entities:
            if self._is_struct_like(entity):
                lines.append(self._build_struct(entity))
                lines.append("")

        # 5. Constants
        for ann in document.annotations:
            if ann.key == "const":
                lines.append(f"const {ann.value};")
        lines.append("")

        # 6. Services (raw verbatim from annotation for round‑trip)
        for ann in document.annotations:
            if ann.key == "service":
                lines.append(ann.value)
                lines.append("")

        thrift = "\n".join(lines).strip() + "\n"
        return thrift.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity classification ──────────────────────────────────────
    def _is_typedef(self, entity: Entity) -> bool:
        # A typedef is an entity with exactly one attribute named "value"
        return len(entity.attributes) == 1 and entity.attributes[0].name == "value"

    def _is_enum(self, entity: Entity) -> bool:
        # Enum if has enum_member annotations or a single "value" with CHECK constraint listing values
        if any(a.key == "enum_member" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and any(c.expression.startswith("IN (") for c in attr.constraints):
                return True
        return False

    def _is_struct_like(self, entity: Entity) -> bool:
        # Struct, union, exception – not typedef, not enum
        if self._is_typedef(entity) or self._is_enum(entity):
            return False
        # Exclude other special kinds like VIEW, etc.
        return entity.kind in (EntityKind.OBJECT, EntityKind.DOCUMENT,
                               EntityKind.TABLE, EntityKind.COLUMN_FAMILY,
                               EntityKind.GRAPH_NODE, EntityKind.GRAPH_EDGE)

    def _thrift_keyword(self, entity: Entity) -> str:
        """Return struct, union, or exception based on annotations."""
        if any(a.key == "thrift_union" and a.value == "true" for a in entity.annotations):
            return "union"
        if any(a.key == "thrift_exception" and a.value == "true" for a in entity.annotations):
            return "exception"
        return "struct"

    # ── Typedef ─────────────────────────────────────────────────────
    def _build_typedef(self, entity: Entity) -> str:
        attr = entity.attributes[0]
        type_str = self._datatype_to_thrift(attr.data_type)
        return f"typedef {type_str} {entity.name}"

    # ── Enum ────────────────────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        name = entity.name
        lines = [f"enum {name} {{"]
        # Collect values
        members: List[Tuple[str, Optional[str]]] = []  # (name, optional numeric string)
        for ann in entity.annotations:
            if ann.key == "enum_member":
                # may be "VALUE=0"
                parts = ann.value.split("=", 1)
                mem_name = parts[0].strip()
                mem_val = parts[1].strip() if len(parts) > 1 else None
                members.append((mem_name, mem_val))
        if not members and entity.attributes:
            attr = entity.attributes[0]
            for c in attr.constraints:
                if c.expression.startswith("IN ("):
                    inner = c.expression[4:].rstrip(")")
                    vals = [v.strip().strip("'\"") for v in inner.split(",")]
                    for i, v in enumerate(vals):
                        members.append((v, str(i)))
                    break
        for mem_name, mem_val in members:
            if mem_val:
                lines.append(f"  {mem_name} = {mem_val}")
            else:
                lines.append(f"  {mem_name}")
        lines.append("}")
        return "\n".join(lines)

    # ── Struct / Union / Exception ──────────────────────────────────
    def _build_struct(self, entity: Entity) -> str:
        kw = self._thrift_keyword(entity)
        lines = [f"{kw} {entity.name} {{"]
        for attr in entity.attributes:
            lines.append(f"  {self._field_to_thrift(attr)}")
        lines.append("}")
        return "\n".join(lines)

    def _field_to_thrift(self, attr: Attribute) -> str:
        # field id (if present)
        field_id = self._get_annotation(attr, "field_id")
        label = self._get_annotation(attr, "label") or ""

        # In Thrift, required/optional can be inferred from attr.required
        if not label:
            if attr.required:
                label = "required"
            else:
                label = "optional"

        type_str = self._datatype_to_thrift(attr.data_type)
        name = attr.name
        # Default value
        default = ""
        if attr.default_value is not None:
            default = f" = {self._format_default(attr.default_value, attr.data_type)}"

        # Combine
        parts = []
        if field_id:
            parts.append(f"{field_id}:")
        if label:
            parts.append(label)
        parts.append(type_str)
        parts.append(name)
        if default:
            parts.append(default)
        return " ".join(parts) + ","

    # ── DataType → Thrift type ──────────────────────────────────────
    def _datatype_to_thrift(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_thrift(dt.element_type) if dt.element_type else "string"
            return f"list<{inner}>"
        if base == ScalarType.MAP:
            key = self._datatype_to_thrift(dt.key_type) if dt.key_type else "string"
            val = self._datatype_to_thrift(dt.value_type) if dt.value_type else "string"
            return f"map<{key}, {val}>"
        if base == ScalarType.REF:
            return dt.ref_entity or "string"
        if base == ScalarType.STRUCT:
            # If there's a ref_entity, use it; otherwise fallback
            return dt.ref_entity or "string"
        if base in _SCALAR_TO_THRIFT:
            return _SCALAR_TO_THRIFT[base]
        return "string"

    # ── Default formatting ──────────────────────────────────────────
    def _format_default(self, default_str: str, dt: DataType) -> str:
        """Format a default value for Thrift IDL."""
        default_str = default_str.strip()
        base = dt.base
        if base == ScalarType.STRING:
            if not (default_str.startswith('"') or default_str.startswith("'")):
                return f'"{default_str}"'
            return default_str
        if base == ScalarType.BOOLEAN:
            return default_str.lower()
        # numbers
        if base in (ScalarType.INT, ScalarType.LONG, ScalarType.FLOAT,
                     ScalarType.DOUBLE, ScalarType.DECIMAL):
            return default_str
        # other
        return default_str

    # ── Annotation helper ─────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None