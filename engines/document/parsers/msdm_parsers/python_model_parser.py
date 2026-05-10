# engines/document/parsers/msdm_parsers/python_model_parser.py
"""
Python Model Parser – extracts MSDM entities from Python source code
containing Pydantic v1/v2 models, standard dataclasses, and enums.

Uses the built‑in `ast` module for reliable, execution‑free analysis.
All type annotations, constraints, default values, and metadata are captured.
Non‑mappable details are stored as structured annotations for lossless round‑trip.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import Constraint
from ...models.msdm_models import ConstraintType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityKind
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType, Namespace
from ..base import ParseOptions
from .base_msdm_parser import BaseMSDMParser

# ── Mapping of Python type names to ScalarType ──────────────────
PYTHON_SCALAR_MAP = {
    "str":       ScalarType.STRING,
    "int":       ScalarType.INT,
    "float":     ScalarType.FLOAT,
    "bool":      ScalarType.BOOLEAN,
    "bytes":     ScalarType.BINARY,
    "datetime":  ScalarType.TIMESTAMP,
    "date":      ScalarType.DATE,
    "time":      ScalarType.TIME,
    "Decimal":   ScalarType.DECIMAL,
    "UUID":      ScalarType.UUID,
    "NoneType":  ScalarType.ANY,
}


class PythonModelParser(BaseMSDMParser):
    """Parser for Python data model files (.py)."""
    name = "python_model"
    supported_extensions = (".py",)

    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        encoding = options.encoding or "utf-8"
        source = data.decode(encoding)

        doc = MSDMDocument(
            document_id=Path(source_name).stem,
            title=Path(source_name).stem,
            media_type=MEDIA_TYPES.get("python_model", MEDIA_TYPES["txt"])
        )
        doc.namespace = Namespace(uri=Path(source_name).stem)

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}") from e

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class(node, doc)

        self.resolve_references(doc)
        return doc

    # ── Class processing ────────────────────────────────────────
    def _process_class(self, cls_node: ast.ClassDef, doc: MSDMDocument) -> None:
        base_names = self._get_base_names(cls_node)
        decorator_ids = self._get_decorator_names(cls_node)
        is_pydantic = any("BaseModel" in b or "pydantic.BaseModel" in b for b in base_names)
        is_dataclass = "dataclass" in decorator_ids
        is_enum = "Enum" in base_names or "enum.Enum" in base_names or "IntEnum" in base_names

        if is_enum:
            self._process_enum(cls_node, doc)
            return
        if not (is_dataclass or is_pydantic):
            return

        entity = Entity(
            name=cls_node.name,
            kind=EntityKind.OBJECT,
            description=ast.get_docstring(cls_node),
        )

        for base in base_names:
            if base.endswith("BaseModel"):
                continue
            if not entity.extends:
                entity.extends_ref_id = base
            else:
                entity.implements_ref_ids.append(base)

        for dec in decorator_ids:
            if dec != "dataclass":
                entity.annotations.append(Annotation(key="decorator", value=dec))

        for decorator in cls_node.decorator_list:
            if isinstance(decorator, ast.Call) and self._get_name(decorator.func) == "dataclass":
                self._store_dataclass_args(decorator, entity)

        self._extract_fields(cls_node, entity, is_pydantic)
        doc.entities.append(entity)

    # ── Enum handling ───────────────────────────────────────────
    def _process_enum(self, cls_node: ast.ClassDef, doc: MSDMDocument) -> None:
        entity = Entity(
            name=cls_node.name,
            kind=EntityKind.OBJECT,
            description=ast.get_docstring(cls_node),
        )
        members = []
        for stmt in cls_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Name):
                        members.append(target.id)
        if members:
            attr = Attribute(
                name="value",
                data_type=DataType(base=ScalarType.STRING),
                required=True,
            )
            quoted = ", ".join(repr(m) for m in members)
            attr.constraints.append(Constraint(type=ConstraintType.CHECK, expression=f"IN ({quoted})"))
            entity.attributes.append(attr)
            # Also store each member as annotation for round‑trip
            for m in members:
                entity.annotations.append(Annotation(key="enum_member", value=m))
        doc.entities.append(entity)

    # ── Field extraction (Pydantic/dataclasses) ──────────────────
    def _extract_fields(self, cls_node: ast.ClassDef, entity: Entity, is_pydantic: bool) -> None:
        for stmt in cls_node.body:
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                field_name = stmt.target.id
                annotation = stmt.annotation
                default = stmt.value

                dt, annotation_str = self._annotation_to_datatype(annotation)
                attr = Attribute(name=field_name, data_type=dt, required=default is None)
                if annotation_str:
                    attr.annotations.append(Annotation(key="python_type", value=annotation_str))

                if default is not None:
                    if self._is_field_call(default):
                        self._process_field_call(cast(ast.Call, default), attr)
                    else:
                        default_val = ast.unparse(default)
                        attr.default_value = default_val
                        attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))

                entity.attributes.append(attr)

        for stmt in cls_node.body:
            if isinstance(stmt, ast.FunctionDef):
                for decorator in stmt.decorator_list:
                    dec_name = self._get_name(decorator.func) if isinstance(decorator, ast.Call) else self._get_name(decorator)
                    if dec_name and "validator" in dec_name.lower():
                        entity.annotations.append(Annotation(key="validator", value=stmt.name))

    # ── Type annotation to DataType ─────────────────────────────
    def _annotation_to_datatype(self, node: ast.AST) -> tuple[DataType, str]:
        source = ast.unparse(node)
        dt = self._ast_to_datatype(node)
        return dt, source

    def _ast_to_datatype(self, node: ast.AST) -> DataType:
        if isinstance(node, ast.Name):
            return self._name_to_datatype(node.id)
        elif isinstance(node, ast.Constant) and node.value is None:
            return DataType(base=ScalarType.ANY)
        elif isinstance(node, ast.Subscript):
            container = self._get_name(node.value)
            if container in ("List", "Sequence", "Set", "FrozenSet"):
                elem = self._slice_to_datatype(node.slice)
                return DataType(base=ScalarType.ARRAY, element_type=elem)
            elif container == "Dict":
                if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                    key_dt = self._ast_to_datatype(node.slice.elts[0])
                    val_dt = self._ast_to_datatype(node.slice.elts[1])
                else:
                    key_dt = DataType(base=ScalarType.STRING)
                    val_dt = self._ast_to_datatype(node.slice)
                return DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)
            elif container == "Optional":
                return self._ast_to_datatype(node.slice)
            elif container in ("Union", "Literal"):
                return DataType(base=ScalarType.ANY)
            else:
                return DataType(base=ScalarType.ANY)
        elif isinstance(node, ast.Attribute):
            full = ast.unparse(node)
            return DataType(base=ScalarType.REF, ref_entity_id=full)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return DataType(base=ScalarType.ANY)
        else:
            return DataType(base=ScalarType.ANY)

    def _slice_to_datatype(self, slice_node: ast.AST) -> DataType:
        # Handle old ast.Index nodes (Python <3.9) and newer subscript slices
        if hasattr(slice_node, 'value'):  # ast.Index
            return self._ast_to_datatype(slice_node.value)
        else:
            return self._ast_to_datatype(slice_node)

    def _name_to_datatype(self, name: str) -> DataType:
        if name in PYTHON_SCALAR_MAP:
            return DataType(base=PYTHON_SCALAR_MAP[name])
        return DataType(base=ScalarType.REF, ref_entity_id=name)

    # ── Field() processing ──────────────────────────────────────
    def _is_field_call(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            func = node.func
            name = self._get_name(func)
            return name in ("Field", "dataclasses.field", "field")
        return False

    def _process_field_call(self, call: ast.Call, attr: Attribute) -> None:
        for kw in call.keywords:
            if kw.arg is None:
                continue
            key = kw.arg
            val = kw.value
            if key == "default":
                default_val = ast.unparse(val)
                attr.default_value = default_val
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
            elif key == "default_factory":
                default_val = ast.unparse(val)
                attr.default_value = default_val
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT, expression=default_val))
            elif key == "description" and isinstance(val, ast.Constant):
                attr.description = str(val.value)
            elif key in ("min_length", "minLength", "max_length", "maxLength",
                         "ge", "gt", "le", "lt", "regex", "pattern",
                         "alias", "title", "uniqueItems"):
                if isinstance(val, ast.Constant):
                    mapped_key = "min_length" if key in ("min_length", "minLength") else \
                                 "max_length" if key in ("max_length", "maxLength") else \
                                 "pattern" if key in ("regex", "pattern") else key
                    attr.annotations.append(Annotation(key=mapped_key, value=str(val.value)))
            else:
                attr.annotations.append(Annotation(key=f"field_{key}", value=ast.unparse(val)))

    # ── AST helpers ──────────────────────────────────────────────
    @staticmethod
    def _get_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{ast.unparse(node.value)}.{node.attr}"
        if isinstance(node, ast.Call):
            return PythonModelParser._get_name(node.func)
        return None

    def _get_base_names(self, cls_node: ast.ClassDef) -> list[str]:
        bases = []
        for base in cls_node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
            elif isinstance(base, ast.Call):
                fname = self._get_name(base.func)
                if fname:
                    bases.append(fname)
        return bases

    def _get_decorator_names(self, cls_node: ast.ClassDef) -> list[str]:
        decs = []
        for d in cls_node.decorator_list:
            if isinstance(d, ast.Name):
                decs.append(d.id)
            elif isinstance(d, ast.Attribute):
                decs.append(ast.unparse(d))
            elif isinstance(d, ast.Call):
                name = self._get_name(d.func)
                if name:
                    decs.append(name)
        return decs

    def _store_dataclass_args(self, decorator: ast.Call, entity: Entity) -> None:
        for kw in decorator.keywords:
            if kw.arg:
                entity.annotations.append(Annotation(key=f"dataclass_{kw.arg}", value=ast.unparse(kw.value)))