# engines/document/writers/msdm_writers/typescript_interface_writer.py
"""
TypeScript Interface Writer – converts an MSDMDocument into TypeScript (.ts)
declarations (interfaces, type aliases, enums, classes).
Preserves modifiers (readonly, public, private, static), optionality, defaults,
and TypeScript‑specific annotations for lossless round‑trip.
"""
from __future__ import annotations

import re

from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget

# ── ScalarType → TypeScript type ──────────────────────────────────
_SCALAR_TO_TS: dict[ScalarType, str] = {
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
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines: list[str] = []
        for entity in document.entities:
            block = self._entity_to_declaration(entity)
            if block:
                lines.append(block)
                lines.append("")
        source = "\n".join(lines).strip() + "\n"
        return source.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/typescript"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Entity dispatch ───────────────────────────────────────────
    def _entity_to_declaration(self, entity: Entity) -> str:
        if self._is_enum(entity):
            return self._build_enum(entity)

        type_alias_body = self._get_annotation(entity, "type_alias")
        if type_alias_body:
            if entity.attributes and entity.attributes[0].name == "value":
                alias_expr = type_alias_body
            else:
                alias_expr = type_alias_body
            export = self._get_annotation(entity, "exported") == "true"
            return f"{'export ' if export else ''}type {entity.name} = {alias_expr};"

        ts_type = self._get_annotation(entity, "ts_type") or "interface"
        if ts_type == "class":
            return self._build_class(entity)
        else:
            return self._build_interface(entity)

    def _is_enum(self, entity: Entity) -> bool:
        if any(a.key == "enum_member" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and any(c.expression and c.expression.startswith("IN (") for c in attr.constraints):
                return True
        return False

    # ── Enum ──────────────────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        name = entity.name
        export = self._get_annotation(entity, "exported") == "true"
        lines = [f"{'export ' if export else ''}enum {name} {{"]

        members: list[tuple[str, str | None]] = []
        for ann in entity.annotations:
            if ann.key == "enum_member" and ann.value is not None:
                parts = ann.value.split("=", 1)
                mem_name = parts[0].strip()
                mem_val = parts[1].strip() if len(parts) > 1 else None
                members.append((mem_name, mem_val))
        if not members and entity.attributes:
            attr = entity.attributes[0]
            for c in attr.constraints:
                if c.expression and c.expression.startswith("IN ("):
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
        extends = entity.implements
        ext_str = f" extends {', '.join([imp.name for imp in extends])}" if extends else ""
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
        extends = entity.extends or None
        implements = entity.implements
        ext_str = ""
        if extends:
            ext_str += f" extends {extends.name}"
        if implements:
            ext_str += f" implements {', '.join([imp.name for imp in implements])}"
        lines = [f"{'export ' if export else ''}class {name}{ext_str} {{"]

        for attr in entity.attributes:
            if self._is_soft_deleted(attr):
                continue
            if self._is_method(attr):
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
            if ann.key == "modifier" and ann.value is not None:
                modifiers.append(ann.value)
        modifiers_str = " ".join(modifiers) + " " if modifiers else ""

        optional = "?" if not attr.required else ""
        ts_type = self._datatype_to_ts(attr.data_type)
        name = attr.name
        return f"{modifiers_str}{name}{optional}: {ts_type}"

    # ── Method → method signature ──────────────────────────────────
    def _method_to_ts(self, attr: Attribute, is_class_method: bool = False) -> str:
        # Retrieve stored operation name
        op_name = self._get_annotation(attr, "operation_name")
        params_str = ""

        # If we have a stored operation name, use it; otherwise try to extract from attribute name
        if not op_name:
            m = re.match(r"(\w+)\(([^)]*)\)", attr.name)
            if m:
                op_name = m.group(1)
                params_str = m.group(2) if m.group(2) else ""
            else:
                op_name = attr.name

        # If we still have no name, fallback to a default
        if not op_name:
            op_name = "method"

        ret_type = self._datatype_to_ts(attr.data_type)

        modifiers = []
        for ann in attr.annotations:
            if ann.key == "visibility" and ann.value is not None:
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
            if dt.ref_entity:
                return dt.ref_entity.name or "any"
            return "any"
        if base == ScalarType.STRUCT:
            if dt.ref_entity:
                return dt.ref_entity.name or "object"
            return "object"
        return _SCALAR_TO_TS.get(base, "any")

    # ── Default formatting ────────────────────────────────────────
    def _format_default(self, default_str: str, dt: DataType) -> str:
        if default_str is None:
            return ""
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
        return default_str

    # ── Helpers ────────────────────────────────────────────────────
    def _get_annotation(self, obj, key: str) -> str | None:
        if isinstance(obj, Entity):
            for a in obj.annotations:
                if a.key == key:
                    return a.value
        elif isinstance(obj, Attribute):
            for a in obj.annotations:
                if a.key == key:
                    return a.value
        return None

    def _is_method(self, attr: Attribute) -> bool:
        return any(a.key == "method" and a.value == "true" for a in attr.annotations)

    def _is_soft_deleted(self, attr: Attribute) -> bool:
        return any(a.key == "deleted" for a in attr.annotations)