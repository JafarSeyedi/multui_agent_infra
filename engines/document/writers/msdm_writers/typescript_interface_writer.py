# engines/document/writers/msdm_writers/typescript_interface_writer.py
"""
TypeScript Interface Writer – converts an MSDMDocument into TypeScript (.ts)
declarations (interfaces, type aliases, enums, classes).
Preserves modifiers (readonly, public, private, static), optionality, defaults,
and TypeScript‑specific annotations for lossless round‑trip.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Set

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

# ── ScalarType → TypeScript type ──────────────────────────────────
_SCALAR_TO_TS: Dict[ScalarType, str] = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "number",
    ScalarType.LONG:      "number",
    ScalarType.FLOAT:     "number",
    ScalarType.DOUBLE:    "number",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.DATE:      "Date",
    ScalarType.TIME:      "string",
    ScalarType.TIMESTAMP: "Date",
    ScalarType.DURATION:  "string",
    ScalarType.UUID:      "string",
    ScalarType.BINARY:    "Uint8Array",
    ScalarType.DECIMAL:   "number",
    ScalarType.ANY:       "any",
}


class TypeScriptInterfaceWriter(BaseMSDMWriter):
    """Writer for TypeScript interface/type files (.ts)."""
    name = "typescript_interface"
    supported_extensions = (".ts",)

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
        for entity in document.entities:
            block = self._entity_to_declaration(entity)
            if block:
                lines.append(block)
                lines.append("")
        source = "\n".join(lines).strip() + "\n"
        return source.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/typescript"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity dispatch ───────────────────────────────────────────
    def _entity_to_declaration(self, entity: Entity) -> str:
        # Enum detection
        if self._is_enum(entity):
            return self._build_enum(entity)

        # Type alias detection (the parser stored annotation "type_alias")
        type_alias_body = self._get_annotation(entity, "type_alias")
        if type_alias_body:
            # This entity is a type alias; its attributes contain only a "value" pseudo-attribute
            # with the alias expression. We'll output the original type expression for round‑trip,
            # or reconstruct from attribute.
            if entity.attributes and entity.attributes[0].name == "value":
                alias_expr = type_alias_body
            else:
                alias_expr = type_alias_body
            export = self._get_annotation(entity, "exported") == "true"
            return f"{'export ' if export else ''}type {entity.name} = {alias_expr};"

        # Interface / class detection
        ts_type = self._get_annotation(entity, "ts_type") or "interface"
        if ts_type == "class":
            return self._build_class(entity)
        else:
            return self._build_interface(entity)

    def _is_enum(self, entity: Entity) -> bool:
        """Check if entity represents an enum (has member annotations or appropriate constraint)."""
        if any(a.key == "enum_member" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and any(c.expression.startswith("IN (") for c in attr.constraints):
                return True
        return False

    # ── Enum ──────────────────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        name = entity.name
        export = self._get_annotation(entity, "exported") == "true"
        lines = [f"{'export ' if export else ''}enum {name} {{"]

        members: List[Tuple[str, Optional[str]]] = []
        for ann in entity.annotations:
            if ann.key == "enum_member":
                # Value is "MEMBER=VALUE"
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
                    for v in vals:
                        members.append((v, None))
                    break

        for mem_name, mem_val in members:
            if mem_val is not None:
                lines.append(f"  {mem_name} = {mem_val},")
            else:
                lines.append(f"  {mem_name},")
        lines.append("}")
        return "\n".join(lines)

    # ── Interface ─────────────────────────────────────────────────
    def _build_interface(self, entity: Entity) -> str:
        name = entity.name
        export = self._get_annotation(entity, "exported") == "true"
        extends = entity.implements  # interfaces are stored here by parser
        ext_str = f" extends {', '.join(extends)}" if extends else ""
        lines = [f"{'export ' if export else ''}interface {name}{ext_str} {{"]

        for attr in entity.attributes:
            if self._is_soft_deleted(attr):
                continue
            if self._is_method(attr):
                lines.append(f"  {self._method_to_ts(attr)};")
            else:
                lines.append(f"  {self._field_to_ts(attr)};")
        lines.append("}")
        return "\n".join(lines)

    # ── Class ─────────────────────────────────────────────────────
    def _build_class(self, entity: Entity) -> str:
        name = entity.name
        export = self._get_annotation(entity, "exported") == "true"
        extends = entity.extends or ""
        implements = entity.implements
        ext_str = ""
        if extends:
            ext_str += f" extends {extends}"
        if implements:
            ext_str += f" implements {', '.join(implements)}"
        lines = [f"{'export ' if export else ''}class {name}{ext_str} {{"]

        # Only public fields with type annotations are output (as per parser)
        for attr in entity.attributes:
            if self._is_soft_deleted(attr):
                continue
            if self._is_method(attr):
                # Methods in class – output as function signature (no body)
                lines.append(f"  {self._method_to_ts(attr, is_class_method=True)};")
            else:
                visibility = self._get_annotation(attr, "visibility")
                if visibility in ("private", "protected"):
                    mod = visibility
                else:
                    mod = "public"
                if self._get_annotation(attr, "static") == "true":
                    mod = f"static {mod}" if mod else "static"
                if self._get_annotation(attr, "readonly") == "true":
                    mod = f"readonly {mod}" if mod else "readonly"
                default = ""
                if attr.default_value is not None:
                    default = f" = {self._format_default(attr.default_value, attr.data_type)}"
                ts_type = self._datatype_to_ts(attr.data_type)
                optional = "?" if not attr.required else ""
                lines.append(f"  {mod} {attr.name}{optional}: {ts_type}{default};")
        lines.append("}")
        return "\n".join(lines)

    # ── Field → property signature ─────────────────────────────────
    def _field_to_ts(self, attr: Attribute) -> str:
        modifiers = []
        for ann in attr.annotations:
            if ann.key == "modifier":
                modifiers.append(ann.value)
        modifiers_str = " ".join(modifiers) + " " if modifiers else ""

        optional = "?" if not attr.required else ""
        ts_type = self._datatype_to_ts(attr.data_type)
        name = attr.name
        return f"{modifiers_str}{name}{optional}: {ts_type}"

    # ── Method → method signature ──────────────────────────────────
    def _method_to_ts(self, attr: Attribute, is_class_method: bool = False) -> str:
        # Recover method name and parameters from pseudo-name stored by parser
        op_name = attr.name
        params_str = ""
        # The parser stored the method name with parameters in the attribute name: methodName(param1:type1, param2:type2)
        # and the original operation name in annotation "operation_name" for class methods.
        if self._get_annotation(attr, "operation_name"):
            op_name = self._get_annotation(attr, "operation_name")
        # Extract params from attribute name
        m = __import__("re").match(r"(\w+)\(([^)]*)\)", attr.name)
        if m:
            op_name = m.group(1)
            params_str = m.group(2) if m.group(2) else ""

        ret_type = self._datatype_to_ts(attr.data_type)

        modifiers = []
        for ann in attr.annotations:
            if ann.key == "visibility":
                modifiers.append(ann.value)
            elif ann.key == "modifier" and ann.value in ("static", "abstract"):
                modifiers.append(ann.value)
        modifiers_str = " ".join(modifiers) + " " if modifiers else ""

        return f"{modifiers_str}{op_name}({params_str}): {ret_type}"

    # ── DataType → TypeScript type string ─────────────────────────
    def _datatype_to_ts(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_ts(dt.element_type) if dt.element_type else "any"
            return f"Array<{inner}>"
        if base == ScalarType.MAP:
            key = self._datatype_to_ts(dt.key_type) if dt.key_type else "string"
            val = self._datatype_to_ts(dt.value_type) if dt.value_type else "any"
            return f"Record<{key}, {val}>"
        if base == ScalarType.REF:
            return dt.ref_entity or "any"
        if base == ScalarType.STRUCT:
            # If there's a ref_entity, use it; else fallback to object
            return dt.ref_entity or "object"
        if base in _SCALAR_TO_TS:
            return _SCALAR_TO_TS[base]
        return "any"

    # ── Default formatting ────────────────────────────────────────
    def _format_default(self, default_str: str, dt: DataType) -> str:
        """Format a default value as a TypeScript literal."""
        default_str = default_str.strip()
        base = dt.base
        if base == ScalarType.STRING:
            if not (default_str.startswith('"') or default_str.startswith("'") or default_str.startswith("`")):
                return f'"{default_str}"'
            return default_str
        if base == ScalarType.BOOLEAN:
            return default_str.lower()
        if base in (ScalarType.INT, ScalarType.LONG, ScalarType.FLOAT,
                     ScalarType.DOUBLE, ScalarType.DECIMAL):
            return default_str
        # arrays, objects, etc.
        return default_str

    # ── Helpers ────────────────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> Optional[str]:
        if isinstance(obj, Entity):
            return next((a.value for a in obj.annotations if a.key == key), None)
        if isinstance(obj, Attribute):
            return next((a.value for a in obj.annotations if a.key == key), None)
        return None

    def _is_method(self, attr: Attribute) -> bool:
        return any(a.key == "method" and a.value == "true" for a in attr.annotations)

    def _is_soft_deleted(self, attr: Attribute) -> bool:
        return any(a.key == "deleted" for a in attr.annotations)