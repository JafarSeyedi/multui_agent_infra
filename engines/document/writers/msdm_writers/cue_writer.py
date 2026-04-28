# engines/document/writers/msdm_writers/cue_writer.py
"""
CUE Writer – converts an MSDMDocument into a CUE (data constraint language) file.
Produces definitions, fields, nested structs, constraints, defaults, and annotations.
Soft‑delete is not applicable (CUE is a design language).
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Union

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

# ── ScalarType → CUE type string ──────────────────────────────────
SCALAR_TO_CUE = {
    ScalarType.STRING:    "string",
    ScalarType.INT:       "int",
    ScalarType.LONG:      "int",        # CUE does not distinguish long
    ScalarType.FLOAT:     "number",
    ScalarType.DOUBLE:    "number",
    ScalarType.BOOLEAN:   "bool",
    ScalarType.DATE:      "string",     # or use #Date constraint
    ScalarType.TIME:      "string",
    ScalarType.TIMESTAMP: "string",
    ScalarType.DURATION:  "string",
    ScalarType.UUID:      "string",
    ScalarType.BINARY:    "bytes",
    ScalarType.DECIMAL:   "number",
    ScalarType.ANY:       "_",
}


class CUEWriter(BaseMSDMWriter):
    """Writer for CUE data language files (.cue)."""
    name = "cue"
    supported_extensions = (".cue",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        lines = []
        if document.namespace:
            lines.append(f"package {document.namespace}")
            lines.append("")

        # Write each entity as a definition
        for entity in document.entities:
            lines.append(self._entity_to_cue(entity, document))
            lines.append("")

        cue_text = "\n".join(lines)
        return cue_text.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity → definition ────────────────────────────────────────
    def _entity_to_cue(self, entity: Entity, doc: MSDMDocument) -> str:
        # Definition header: #Name: {
        header = f"#{entity.name}: {{"
        if entity.description:
            header = f"// {entity.description}\n{header}"

        lines = [header]
        for attr in entity.attributes:
            lines.append(self._attribute_to_cue(attr, doc, indent="    "))

        # Constraints at entity level? Add as closing fields if needed.
        lines.append("}")

        # Extends? In CUE we would use embedding, e.g., #Child: #Parent & { ... }
        # We'll represent extends as an embedding line: #Child: #Parent & {
        if entity.extends:
            # Re‑write the first line to include embedding
            base_def = f"#{entity.extends}"
            lines[0] = f"#{entity.name}: {base_def} & {{"
        return "\n".join(lines)

    # ── Attribute → field ──────────────────────────────────────────
    def _attribute_to_cue(self, attr: Attribute, doc: MSDMDocument, indent: str = "") -> str:
        name = self._cue_field_name(attr.name)
        # Type
        type_str = self._datatype_to_cue(attr.data_type, attr.nested_attributes)

        # Optionality
        if not attr.required:
            name += "?"
        # Default
        default = ""
        if attr.default_value is not None:
            default = f" | *{self._format_default(attr.default_value, attr.data_type)}"
        # Constraints
        constraints = self._format_constraints(attr.constraints)
        # Annotations (CUE attributes)
        attr_annotations = self._format_annotations(attr.annotations)

        field = f"{indent}{name}: {type_str}{default}{constraints}{attr_annotations}"
        return field

    # ── DataType to CUE type string ────────────────────────────────
    def _datatype_to_cue(self, dt: DataType, nested_attrs: List[Attribute]) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            elem_str = self._datatype_to_cue(dt.element_type, []) if dt.element_type else "_"
            return f"[...{elem_str}]"
        elif base == ScalarType.MAP:
            # CUE does not have a native map; we can express as { [string]: value } or use a struct with dynamic key.
            # We'll produce: { [string]: valueType }
            key_str = self._datatype_to_cue(dt.key_type, []) if dt.key_type else "string"
            val_str = self._datatype_to_cue(dt.value_type, []) if dt.value_type else "_"
            return f"{{ [{key_str}]: {val_str} }}"
        elif base == ScalarType.STRUCT:
            if nested_attrs:
                # Inline struct
                inner = "{\n"
                for na in nested_attrs:
                    inner += "        " + self._attribute_to_cue(na, None, indent="    ").lstrip() + "\n"
                inner += "    }"
                return inner
            return "{}"
        elif base == ScalarType.REF:
            ref = dt.ref_entity or "_"
            return f"#{ref}"
        elif base in SCALAR_TO_CUE:
            return SCALAR_TO_CUE[base]
        else:
            return "_"

    # ── Constraint formatting ──────────────────────────────────────
    def _format_constraints(self, constraints: List[Constraint]) -> str:
        parts = []
        for c in constraints:
            if c.type == ConstraintType.CHECK:
                expr = c.expression or ""
                if expr.startswith("IN ("):
                    # enum constraint → CUE enum via | *"val" | *"val2"? Not beautifully.
                    # We'll represent as a disjunction of allowed values.
                    inner = expr[4:].rstrip(")")
                    values = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
                    # CUE: string & ( "val1" | "val2" )
                    quoted = " | ".join(f'"{v}"' for v in values)
                    parts.append(f" & ({quoted})")
                elif expr.startswith("≥") or expr.startswith(">") or expr.startswith("<") or expr.startswith("="):
                    # comparison: > 0
                    parts.append(f" & {expr}")
                else:
                    parts.append(f" & {expr}")   # generic expression
            elif c.type == ConstraintType.NOT_NULL:
                # already reflected by required flag
                pass
            elif c.type == ConstraintType.UNIQUE:
                parts.append(f" // UNIQUE")
            elif c.type == ConstraintType.PRIMARY_KEY:
                parts.append(f" // PK({c.expression})")
            elif c.type == ConstraintType.FOREIGN_KEY:
                parts.append(f" // FK → {c.referenced_entity}.{c.referenced_attributes}")
            elif c.type == ConstraintType.DEFAULT:
                # default already handled through | *value
                pass
        return "".join(parts)

    # ── Annotations ────────────────────────────────────────────────
    def _format_annotations(self, annotations: List[Annotation]) -> str:
        parts = []
        for ann in annotations:
            key = ann.key
            val = ann.value
            # CUE attributes: @key(value)
            parts.append(f" @{key}({val})")
        return "".join(parts)

    # ── Default value formatting ───────────────────────────────────
    def _format_default(self, default_str: str, dt: DataType) -> str:
        # Try to interpret the string as a literal
        if dt.base in (ScalarType.INT, ScalarType.LONG, ScalarType.FLOAT, ScalarType.DOUBLE,
                        ScalarType.DECIMAL):
            # Return as number string
            return default_str
        elif dt.base == ScalarType.STRING:
            # Ensure quoted
            if not (default_str.startswith('"') and default_str.endswith('"')):
                return f'"{default_str}"'
            return default_str
        elif dt.base == ScalarType.BOOLEAN:
            return default_str.lower()
        elif dt.base == ScalarType.REF:
            return f"#{default_str}"
        else:
            return default_str

    # ── Field name escaping ────────────────────────────────────────
    @staticmethod
    def _cue_field_name(name: str) -> str:
        """Escape a CUE field name if it contains special characters."""
        if any(ch in name for ch in ' -{}[]()@:?|&*#'):
            return f'"{name}"'
        return name