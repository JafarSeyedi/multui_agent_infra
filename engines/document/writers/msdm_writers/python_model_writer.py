# engines/document/writers/msdm_writers/python_model_writer.py
"""
Python Model Writer – converts an MSDMDocument into Python source code
using Pydantic v2 (default), standard dataclasses, or plain typed classes.
Preserves field options, constraints, enums, and round‑trip annotations.

Supports:
- Pydantic BaseModel / dataclasses.dataclass
- Enum classes
- Field constraints (min_length, max_length, ge, le, pattern, etc.)
- Default values and default_factory
- Optional fields via typing.Optional
- Nested models and references
- Custom decorators and annotations captured by the parser
"""
from __future__ import annotations

import keyword
from enum import Enum

from ...models.msdm_models import Attribute
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ..base import WriteOptions
from .base_msdm_writer import BaseMSDMWriter
from .base_msdm_writer import SoftDeleteStrategy
from .base_msdm_writer import WriteTarget

# ── Python type mappings ─────────────────────────────────────────
_SCALAR_TO_PYTHON: dict[ScalarType, str] = {
    ScalarType.STRING:    "str",
    ScalarType.INT:       "int",
    ScalarType.LONG:      "int",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "float",
    ScalarType.BOOLEAN:   "bool",
    ScalarType.DATE:      "datetime.date",
    ScalarType.TIME:      "datetime.time",
    ScalarType.TIMESTAMP: "datetime.datetime",
    ScalarType.DURATION:  "datetime.timedelta",
    ScalarType.UUID:      "uuid.UUID",
    ScalarType.BINARY:    "bytes",
    ScalarType.DECIMAL:   "decimal.Decimal",
    ScalarType.ANY:       "typing.Any",
}

_IMPORT_MAP = {
    "datetime.date":     "import datetime",
    "datetime.time":     "import datetime",
    "datetime.datetime": "import datetime",
    "datetime.timedelta": "import datetime",
    "uuid.UUID":         "import uuid",
    "decimal.Decimal":   "import decimal",
    "typing.Any":        "from typing import Any",
    "typing.Optional":   "from typing import Optional",
    "typing.List":       "from typing import List",
    "typing.Dict":       "from typing import Dict",
    "typing.Union":      "from typing import Union",
}


class TargetStyle(str, Enum):
    PYDANTIC    = "pydantic"
    DATACLASS   = "dataclass"
    PLAIN       = "plain"


class PythonModelWriter(BaseMSDMWriter):
    name = "python_model"
    supported_extensions = (".py",)

    def __init__(
        self,
        options: WriteOptions | None = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
        target_style: TargetStyle = TargetStyle.PYDANTIC,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self.target_style = target_style
        self._imports: set[str] = set()

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        self._imports.clear()
        lines: list[str] = []

        if document.namespace:
            lines.append(f"# {document.namespace}")
        lines.append("")

        for entity in document.entities:
            self._collect_imports(entity)

        if self.target_style == TargetStyle.PYDANTIC:
            lines.append("from pydantic import BaseModel, Field")
        elif self.target_style == TargetStyle.DATACLASS:
            lines.append("from dataclasses import dataclass, field")

        third_party = sorted(imp for imp in self._imports if not imp.startswith("from"))
        from_imports = sorted(imp for imp in self._imports if imp.startswith("from"))
        lines.extend(third_party)
        lines.extend(from_imports)
        lines.append("")

        for entity in document.entities:
            if self._is_enum_entity(entity):
                lines.append(self._build_enum(entity))
            else:
                lines.append(self._build_model(entity, document))
            lines.append("")

        source = "\n".join(lines)
        return source.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/x-python"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Entity classification ────────────────────────────────────
    def _is_enum_entity(self, entity: Entity) -> bool:
        if any(a.key == "enum_member" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and  any(c.expression is not None and c.expression.startswith("IN (") for c in attr.constraints):
                return True
        return False

    # ── Build Enum class ─────────────────────────────────────────
    def _build_enum(self, entity: Entity) -> str:
        name = entity.name
        desc = entity.description
        lines = []
        if desc:
            lines.append(f"# {desc}")
        lines.append(f"class {name}(enum.Enum):")
        self._imports.add("import enum")

        members = []
        for ann in entity.annotations:
            if ann.key == "enum_member" and ann.value is not None:
                parts = ann.value.split("=", 1)
                member_name = parts[0].strip()
                member_value = parts[1].strip() if len(parts) > 1 else member_name
                members.append((member_name, member_value))
        if not members and entity.attributes:
            attr = entity.attributes[0]
            for c in attr.constraints:
                if c.expression is not None and c.expression.startswith("IN ("):
                    inner = c.expression[4:].rstrip(")")
                    vals = [v.strip().strip("'\"") for v in inner.split(",")]
                    for i, v in enumerate(vals):
                        members.append((v, str(i)))
        for member_name, member_value in members:
            lines.append(f"    {member_name} = {self._format_enum_value(member_value)}")
        return "\n".join(lines) + "\n"

    def _format_enum_value(self, val: str) -> str:
        if val.isdigit():
            return val
        if val.replace('.', '', 1).isdigit() and val.count('.') < 2:
            return val
        return f'"{val}"'

    # ── Build model (Pydantic / dataclass) ───────────────────────
    def _build_model(self, entity: Entity, doc: MSDMDocument) -> str:
        name = entity.name
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')

        if self.target_style == TargetStyle.PYDANTIC:
            base_classes = ["BaseModel"]
            for impl in entity.implements:
                base_classes.append(impl.name)
            bases = ", ".join(base_classes)
            lines.append(f"class {name}({bases}):")
        elif self.target_style == TargetStyle.DATACLASS:
            attrs = ""
            for ann in entity.annotations:
                if ann.key.startswith("dataclass_") and ann.value is not None:
                    key = ann.key[10:]
                    attrs += f", {key}={ann.value}"
            lines.append(f"@dataclass{attrs}")
            extends = entity.extends.name if entity.extends else ""
            lines.append(f"class {name}({extends}):" if extends else f"class {name}:")
        else:
            extends = entity.extends.name if entity.extends else ""
            lines.append(f"class {name}({extends}):" if extends else f"class {name}:")

        for attr in entity.attributes:
            if self._is_soft_deleted(attr):
                lines.append(f"    # {attr.name}: deleted")
                continue
            lines.append(f"    {self._field_to_python(attr)}")

        if not entity.attributes:
            lines.append("    pass")
        return "\n".join(lines) + "\n"

    # ── Field conversion ─────────────────────────────────────────
    def _field_to_python(self, attr: Attribute) -> str:
        py_type = self._datatype_to_python(attr.data_type, attr.required)
        if not attr.required:
            py_type = f"Optional[{py_type}]" if py_type != "Any" else py_type
            self._imports.add("from typing import Optional")

        default = ""
        if attr.default_value is not None:
            default_val = self._format_default(attr.default_value, attr.data_type)
            if self.target_style == TargetStyle.PYDANTIC:
                extra = self._field_constraints_and_options(attr)
                if extra:
                    default = f" = Field(default={default_val}, {extra})"
                else:
                    default = f" = Field(default={default_val})"
            elif self.target_style == TargetStyle.DATACLASS:
                self._imports.add("from dataclasses import field")
                extra = self._field_constraints_and_options(attr)
                if extra:
                    default = f" = field(default={default_val}, {extra})"
                else:
                    default = f" = field(default={default_val})"
            else:
                default = f" = {default_val}"
        else:
            default = "" if attr.required else " = None"

        name = attr.name
        if keyword.iskeyword(name):
            name = f"{name}_"

        return f"{name}: {py_type}{default}"

    def _datatype_to_python(self, dt: DataType, required: bool = True) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_python(dt.element_type, required=False) if dt.element_type else "Any"
            self._imports.add("from typing import List")
            return f"List[{inner}]"
        if base == ScalarType.MAP:
            key = self._datatype_to_python(dt.key_type, required=False) if dt.key_type else "str"
            val = self._datatype_to_python(dt.value_type, required=False) if dt.value_type else "Any"
            self._imports.add("from typing import Dict")
            return f"Dict[{key}, {val}]"
        if base == ScalarType.REF and dt.ref_entity:
            ref_name = dt.ref_entity.name or "object"
            return ref_name
        if base == ScalarType.STRUCT and dt.ref_entity:
            return dt.ref_entity.name or "Any"
        if base in _SCALAR_TO_PYTHON:
            py = _SCALAR_TO_PYTHON[base]
            if py in _IMPORT_MAP:
                self._imports.add(_IMPORT_MAP[py])
            return py
        return "Any"

    # ── Pydantic Field options from constraints ────────────────────
    def _field_constraints_and_options(self, attr: Attribute) -> str:
        opts = []
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK and c.expression is not None and c.expression.startswith("IN ("):
                pass
            elif c.type == ConstraintType.DEFAULT:
                pass
        for ann in attr.annotations:
            if ann.value is None:
                continue
            key = ann.key
            val = ann.value
            if key in ("min_length", "max_length", "ge", "le", "gt", "lt", "multipleOf",
                       "regex", "pattern", "minItems", "maxItems", "uniqueItems",
                       "minProperties", "maxProperties"):
                if key in ("regex", "pattern"):
                    opts.append(f"pattern={val}")
                else:
                    opts.append(f"{key}={val}")
            elif key == "alias":
                opts.append(f'alias="{val}"')
            elif key == "title":
                opts.append(f'title="{val}"')
            elif key == "description":
                opts.append(f'description="{val}"')
            elif key == "format":
                opts.append(f'format="{val}"')
            elif key == "example":
                opts.append(f"example={val}")
            elif key == "default_factory":
                opts.append(f"default_factory={val}")
        return ", ".join(opts)

    # ── Default value formatting ──────────────────────────────────
    def _format_default(self, default_str: str | None, dt: DataType) -> str:
        if default_str is None:
            return "None"
        raw = default_str.strip()
        base = dt.base
        if base in (ScalarType.STRING, ScalarType.ANY, ScalarType.JSON, ScalarType.XML):
            if not (raw.startswith('"') or raw.startswith("'")):
                return f'"{raw}"'
            return raw
        if base in (ScalarType.INT, ScalarType.LONG):
            return raw if raw.isdigit() else f"int({raw})"
        if base in (ScalarType.FLOAT, ScalarType.DOUBLE, ScalarType.DECIMAL):
            try:
                float(raw)
                return raw
            except ValueError:
                return f"float({repr(raw)})"
        if base == ScalarType.BOOLEAN:
            return raw.lower() if raw.lower() in ("true", "false") else f"bool({raw})"
        if base == ScalarType.UUID:
            return f'uuid.UUID("{raw}")'
        if base == ScalarType.REF:
            return raw
        return raw
    
    # ── Soft‑delete detection ─────────────────────────────────────
    def _is_soft_deleted(self, attr: Attribute) -> bool:
        return any(a.key == "deleted" for a in attr.annotations)

    # ── Import collection ──────────────────────────────────────────
    def _collect_imports(self, entity: Entity) -> None:
        for attr in entity.attributes:
            self._datatype_to_python(attr.data_type, attr.required)
        for attr in entity.attributes:
            self._collect_ref_imports(attr.data_type)

    def _collect_ref_imports(self, dt: DataType) -> None:
        if dt.element_type:
            self._collect_ref_imports(dt.element_type)
        if dt.key_type:
            self._collect_ref_imports(dt.key_type)
        if dt.value_type:
            self._collect_ref_imports(dt.value_type)