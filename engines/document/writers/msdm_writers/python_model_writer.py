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
from typing import Optional, Dict, Any, List, Set, Union
from enum import Enum

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

# ── Python type mappings ─────────────────────────────────────────
_SCALAR_TO_PYTHON: Dict[ScalarType, str] = {
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

# Additional imports required for certain types
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
    """Python class style."""
    PYDANTIC    = "pydantic"
    DATACLASS   = "dataclass"
    PLAIN       = "plain"          # annotations only, no decorator


class PythonModelWriter(BaseMSDMWriter):
    """Writer for Python data model files (.py)."""
    name = "python_model"
    supported_extensions = (".py",)

    def __init__(
        self,
        options: Optional[WriteOptions] = None,
        target_mode: WriteTarget = WriteTarget.DESIGN_FILE,
        soft_delete_strategy: SoftDeleteStrategy = SoftDeleteStrategy.NONE,
        target_style: TargetStyle = TargetStyle.PYDANTIC,
    ):
        super().__init__(options, target_mode, soft_delete_strategy)
        self.target_style = target_style

    # ── Public API ─────────────────────────────────────────────────
    async def _write_design(self, document: MSDMDocument) -> bytes:
        self._imports: Set[str] = set()
        lines: List[str] = []

        # File header
        if document.namespace:
            lines.append(f"# {document.namespace}")
        lines.append("")

        # Collect all needed imports
        for entity in document.entities:
            self._collect_imports(entity)
        # Add base import based on style
        if self.target_style == TargetStyle.PYDANTIC:
            lines.append("from pydantic import BaseModel, Field")
        elif self.target_style == TargetStyle.DATACLASS:
            lines.append("from dataclasses import dataclass, field")
        # Add third-party imports sorted
        third_party = sorted(imp for imp in self._imports if not imp.startswith("from"))
        from_imports = sorted(imp for imp in self._imports if imp.startswith("from"))
        lines.extend(third_party)
        lines.extend(from_imports)
        lines.append("")

        # Write entities
        for entity in document.entities:
            if self._is_enum_entity(entity):
                lines.append(self._build_enum(entity))
            else:
                lines.append(self._build_model(entity, document))
            lines.append("")

        source = "\n".join(lines)
        return source.encode(self.options.encoding or "utf-8")

    async def get_supported_media_types(self) -> list[str]:
        return ["text/x-python"]

    async def get_supported_extensions(self) -> list[str]:
        return self.supported_extensions

    # ── Entity classification ────────────────────────────────────
    def _is_enum_entity(self, entity: Entity) -> bool:
        """Check if the entity represents an enum."""
        if any(a.key == "enum_member" for a in entity.annotations):
            return True
        if len(entity.attributes) == 1:
            attr = entity.attributes[0]
            if attr.name == "value" and any(c.expression.startswith("IN (") for c in attr.constraints):
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

        # Collect enum members from annotations or constraint
        members = []
        for ann in entity.annotations:
            if ann.key == "enum_member":
                # Value may be "VALUE=number"
                parts = ann.value.split("=", 1)
                member_name = parts[0].strip()
                member_value = parts[1].strip() if len(parts) > 1 else member_name
                members.append((member_name, member_value))
        if not members and entity.attributes:
            attr = entity.attributes[0]
            for c in attr.constraints:
                if c.expression.startswith("IN ("):
                    inner = c.expression[4:].rstrip(")")
                    vals = [v.strip().strip("'\"") for v in inner.split(",")]
                    for i, v in enumerate(vals):
                        members.append((v, str(i)))
        for member_name, member_value in members:
            lines.append(f"    {member_name} = {self._format_enum_value(member_value)}")
        return "\n".join(lines) + "\n"

    def _format_enum_value(self, val: str) -> str:
        """Return an appropriate Python literal for enum value."""
        if val.isdigit():
            return val
        if val.replace('.', '', 1).isdigit() and val.count('.') < 2:
            return val
        # Assume string if not numeric
        return f'"{val}"'

    # ── Build model (Pydantic / dataclass) ───────────────────────
    def _build_model(self, entity: Entity, doc: MSDMDocument) -> str:
        name = entity.name
        desc = entity.description
        lines = []
        if desc:
            lines.append(f'"""{desc}"""')

        # Decorator
        if self.target_style == TargetStyle.PYDANTIC:
            # Pydantic: class definition
            base_classes = ["BaseModel"]
            # Check for additional bases from implements
            for impl in entity.implements:
                base_classes.append(impl)
            bases = ", ".join(base_classes)
            lines.append(f"class {name}({bases}):")
        elif self.target_style == TargetStyle.DATACLASS:
            # Dataclass decorator plus class
            attrs = ""
            # Extract dataclass arguments from annotations
            for ann in entity.annotations:
                if ann.key.startswith("dataclass_"):
                    key = ann.key[10:]  # e.g., "frozen"
                    attrs += f", {key}={ann.value}"
            lines.append(f"@dataclass{attrs}")
            extends = entity.extends if entity.extends else ""
            lines.append(f"class {name}({extends}):" if extends else f"class {name}:")
        else:  # plain
            extends = entity.extends if entity.extends else ""
            lines.append(f"class {name}({extends}):" if extends else f"class {name}:")

        # Fields
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
        # Type annotation
        py_type = self._datatype_to_python(attr.data_type, attr.required)
        if not attr.required:
            py_type = f"Optional[{py_type}]" if py_type != "Any" else py_type
            self._imports.add("from typing import Optional")
        # Default value
        default = ""
        if attr.default_value is not None:
            default_val = self._format_default(attr.default_value, attr.data_type)
            if self.target_style == TargetStyle.PYDANTIC:
                # Use Field(default=...)
                default = f" = Field(default={default_val}"
                extra = self._field_constraints_and_options(attr)
                if extra:
                    default += f", {extra}"
                default += ")"
            elif self.target_style == TargetStyle.DATACLASS:
                # use field(default=...)
                self._imports.add("from dataclasses import field")
                extra = self._field_constraints_and_options(attr)
                if extra:
                    default = f" = field(default={default_val}, {extra})"
                else:
                    default = f" = field(default={default_val})"
            else:
                default = f" = {default_val}"
        else:
            if attr.required:
                default = ""
            else:
                default = " = None"

        name = attr.name
        if self._is_python_keyword(name):
            name = f"{name}_"

        return f"{name}: {py_type}{default}"

    def _datatype_to_python(self, dt: DataType, required: bool = True) -> str:
        """Convert a DataType to a Python type string."""
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
        if base == ScalarType.REF:
            ref_name = dt.ref_entity or "object"
            return ref_name
        if base == ScalarType.STRUCT:
            # If there are nested attributes, we should have a nested class reference.
            # The parser may have stored the entity name; we use ref_entity or "object"
            return dt.ref_entity or "Any"
        if base in _SCALAR_TO_PYTHON:
            py = _SCALAR_TO_PYTHON[base]
            if py in _IMPORT_MAP:
                self._imports.add(_IMPORT_MAP[py])
            return py
        return "Any"

    # ── Pydantic Field options from constraints ────────────────────
    def _field_constraints_and_options(self, attr: Attribute) -> str:
        """Generate additional keyword arguments for Field() or field()."""
        opts = []
        # Constraints from model
        for c in attr.constraints:
            if c.type == ConstraintType.CHECK:
                if c.expression.startswith("IN ("):
                    # enum values – usually not passed as Field options; skip
                    pass
                elif c.expression.startswith("= "):
                    # exact value? default handled differently
                    pass
                else:
                    # Could be a generic expression, we ignore
                    pass
            elif c.type == ConstraintType.DEFAULT:
                pass  # already handled
        # Annotations from parser (e.g., min_length, max_length, pattern, ge, le, etc.)
        for ann in attr.annotations:
            key = ann.key
            val = ann.value
            if key in ("min_length", "max_length", "ge", "le", "gt", "lt", "multipleOf",
                       "regex", "pattern", "minItems", "maxItems", "uniqueItems",
                       "minProperties", "maxProperties"):
                if key in ("min_length",):
                    opts.append(f"min_length={val}")
                elif key == "max_length":
                    opts.append(f"max_length={val}")
                elif key in ("ge", "le", "gt", "lt"):
                    opts.append(f"{key}={val}")
                elif key in ("regex", "pattern"):
                    opts.append(f"pattern={val}")
                elif key == "minItems":
                    opts.append(f"min_items={val}")
                elif key == "maxItems":
                    opts.append(f"max_items={val}")
                elif key == "uniqueItems":
                    opts.append(f"unique_items={val}")
            elif key == "alias":
                opts.append(f"alias=\"{val}\"")
            elif key == "title":
                opts.append(f"title=\"{val}\"")
            elif key == "description":
                opts.append(f"description=\"{val}\"")
            elif key == "format":
                opts.append(f"format=\"{val}\"")
            elif key == "example":
                opts.append(f"example={val}")
            elif key == "default_factory":
                opts.append(f"default_factory={val}")
        return ", ".join(opts)

    # ── Default value formatting ──────────────────────────────────
    def _format_default(self, default_str: str, dt: DataType) -> str:
        """Convert a default value string to a Python literal."""
        default_str = default_str.strip()
        base = dt.base
        # Try to infer Python literal from string
        if base in (ScalarType.STRING, ScalarType.ANY, ScalarType.JSON, ScalarType.XML):
            if not (default_str.startswith('"') or default_str.startswith("'")):
                return f'"{default_str}"'
            return default_str
        if base in (ScalarType.INT, ScalarType.LONG):
            return default_str if default_str.isdigit() else f"int({default_str})"
        if base in (ScalarType.FLOAT, ScalarType.DOUBLE, ScalarType.DECIMAL):
            try:
                float(default_str)
                return default_str
            except ValueError:
                return f"float({repr(default_str)})"
        if base == ScalarType.BOOLEAN:
            return default_str.lower() if default_str.lower() in ("true", "false") else f"bool({default_str})"
        if base == ScalarType.UUID:
            return f'uuid.UUID("{default_str}")'
        if base == ScalarType.REF:
            return default_str  # assume it's a class name or variable
        return default_str

    # ── Soft‑delete detection ─────────────────────────────────────
    def _is_soft_deleted(self, attr: Attribute) -> bool:
        return any(a.key == "deleted" for a in attr.annotations)

    # ── Import collection ──────────────────────────────────────────
    def _collect_imports(self, entity: Entity) -> None:
        # For each attribute, resolve types and add imports if needed
        for attr in entity.attributes:
            self._datatype_to_python(attr.data_type, attr.required)
        # If Pydantic, ensure BaseModel is available? Already done at top.
        # If any field uses Field/field, handled implicitly.
        # Decorators are handled elsewhere.
        # Inherited classes from extends/implements may need imports; we can't track automatically.
        pass

    # ── Python keyword check ──────────────────────────────────────
    @staticmethod
    def _is_python_keyword(name: str) -> bool:
        import keyword
        return keyword.iskeyword(name)