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
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Set, Union, Tuple

from .base_msdm_parser import BaseMSDMParser
from ..base import ParseOptions
from ...models.msdm_models import (
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

        doc = MSDMDocument()
        doc.namespace = Path(source_name).stem

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}") from e

        # Top‑level classes only
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                self._process_class(node, doc)

        return doc

    # ── Class processing ────────────────────────────────────────
    def _process_class(self, cls_node: ast.ClassDef, doc: MSDMDocument) -> None:
        # Determine the “kind” of data model
        base_names = self._get_base_names(cls_node)
        decorator_ids = self._get_decorator_names(cls_node)
        is_pydantic = any("BaseModel" in b or "pydantic.BaseModel" in b for b in base_names)
        is_dataclass = "dataclass" in decorator_ids
        is_enum = "Enum" in base_names or "enum.Enum" in base_names or "IntEnum" in base_names

        if is_enum:
            self._process_enum(cls_node, doc)
            return
        if not (is_dataclass or is_pydantic):
            # Optional: also accept classes with `__annotations__` but no decorator?
            # We'll skip for safety.
            return

        entity = Entity(
            name=cls_node.name,
            kind=EntityKind.OBJECT,
            description=ast.get_docstring(cls_node),
        )

        # Base classes (other than BaseModel) stored as extends / implements
        for base in base_names:
            if base.endswith("BaseModel"):
                continue
            if not entity.extends:
                entity.extends = base
            else:
                entity.implements.append(base)

        # Store decorator info
        for dec in decorator_ids:
            if dec != "dataclass":
                entity.annotations.append(Annotation(key="decorator", value=dec))

        # If it's a dataclass, we can extract the `@dataclass` parameters (like `frozen`, `order`)
        # from the decorator expression – stored as annotation.
        for decorator in cls_node.decorator_list:
            if isinstance(decorator, ast.Call) and self._get_name(decorator.func) == "dataclass":
                self._store_dataclass_args(decorator, entity)

        # Extract fields
        self._extract_fields(cls_node, entity, is_pydantic)

        doc.entities.append(entity)

    # ── Enum handling ───────────────────────────────────────────
    def _process_enum(self, cls_node: ast.ClassDef, doc: MSDMDocument) -> None:
        entity = Entity(
            name=cls_node.name,
            kind=EntityKind.OBJECT,
            description=ast.get_docstring(cls_node),
        )
        # Collect enum members: simple assignments to names (no type annotation needed)
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
        doc.entities.append(entity)

    # ── Field extraction (Pydantic/dataclasses) ──────────────────
    def _extract_fields(self, cls_node: ast.ClassDef, entity: Entity, is_pydantic: bool) -> None:
        # Collect annotations (from AnnAssign and from class‑level __annotations__?)
        # In ast, class body can have AnnAssign (var: type [= value]).
        # For Pydantic, fields may also be defined via class variables `name: type = Field(...)`.
        # We'll iterate over class body and pick AnnAssign nodes.
        for stmt in cls_node.body:
            if isinstance(stmt, ast.AnnAssign):
                # stmt.target should be a Name node for simple fields
                if isinstance(stmt.target, ast.Name):
                    field_name = stmt.target.id
                    annotation = stmt.annotation
                    default = stmt.value  # may be Field() or simple default

                    # Build DataType from annotation
                    dt, annotation_str = self._annotation_to_datatype(annotation)
                    attr = Attribute(name=field_name, data_type=dt, required=default is None)

                    # Store original annotation string for round‑trip
                    if annotation_str:
                        attr.annotations.append(Annotation(key="python_type", value=annotation_str))

                    # Process default value / Field() metadata
                    if default is not None:
                        if self._is_field_call(default):
                            self._process_field_call(default, attr)
                        else:
                            # Simple default literal
                            attr.default_value = ast.unparse(default)
                            attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                                               expression=attr.default_value))

                    entity.attributes.append(attr)

        # For Pydantic, also look for validators (decorated methods) – store as annotations
        for stmt in cls_node.body:
            if isinstance(stmt, ast.FunctionDef):
                for decorator in stmt.decorator_list:
                    dec_name = self._get_name(decorator.func) if isinstance(decorator, ast.Call) else self._get_name(decorator)
                    if dec_name and "validator" in dec_name.lower():
                        entity.annotations.append(Annotation(key="validator", value=stmt.name))

    # ── Type annotation to DataType ─────────────────────────────
    def _annotation_to_datatype(self, node: ast.AST) -> Tuple[DataType, str]:
        """Convert an AST annotation to a DataType and its source text."""
        source = ast.unparse(node)
        dt = self._ast_to_datatype(node)
        return dt, source

    def _ast_to_datatype(self, node: ast.AST) -> DataType:
        if isinstance(node, ast.Name):
            # Simple type like `str`, `int`, `MyModel`
            return self._name_to_datatype(node.id)
        elif isinstance(node, ast.Constant) and node.value is None:
            # `None` -> used in Optional[None]? rare
            return DataType(base=ScalarType.ANY)
        elif isinstance(node, ast.Subscript):
            # Generic type: List[int], Optional[str], Union[A, B], etc.
            # node.value is the container (e.g., `List`), node.slice is the index
            container = self._get_name(node.value)
            if container in ("List", "Sequence", "Set", "FrozenSet"):
                elem = self._slice_to_datatype(node.slice)
                return DataType(base=ScalarType.ARRAY, element_type=elem)
            elif container == "Dict":
                # Dict[K, V] – slice is a tuple if two arguments, else single
                if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                    key_dt = self._ast_to_datatype(node.slice.elts[0])
                    val_dt = self._ast_to_datatype(node.slice.elts[1])
                else:
                    key_dt = DataType(base=ScalarType.STRING)   # default
                    val_dt = self._ast_to_datatype(node.slice)
                return DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)
            elif container == "Optional":
                # Optional[X] is equivalent to Union[X, None]
                inner = self._ast_to_datatype(node.slice)
                # We'll mark required=False via outer context; no change to DataType
                return inner
            elif container == "Union":
                # Union[A, B] – we flatten to ANY for now, but store as annotation
                return DataType(base=ScalarType.ANY)
            elif container == "Literal":
                # Literal values – treat as string enum? We'll store as annotation
                return DataType(base=ScalarType.STRING)
            else:
                # Unknown generic – fallback
                return DataType(base=ScalarType.ANY)
        elif isinstance(node, ast.Attribute):
            # e.g., datetime.datetime, pydantic.BaseModel
            full = ast.unparse(node)
            return DataType(base=ScalarType.REF, ref_entity=full)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            # Union[A, B] written as A | B (Python 3.10+)
            return DataType(base=ScalarType.ANY)   # treat as ANY
        else:
            # Fallback
            return DataType(base=ScalarType.ANY)

    def _slice_to_datatype(self, slice_node: ast.AST) -> DataType:
        """Convert the slice part of a subscript (e.g., the `int` in `List[int]`)."""
        if isinstance(slice_node, ast.Index):  # Python <3.9
            return self._ast_to_datatype(slice_node.value)
        else:
            return self._ast_to_datatype(slice_node)

    def _name_to_datatype(self, name: str) -> DataType:
        if name in PYTHON_SCALAR_MAP:
            return DataType(base=PYTHON_SCALAR_MAP[name])
        # Assume reference to another class
        return DataType(base=ScalarType.REF, ref_entity=name)

    # ── Field() processing ──────────────────────────────────────
    def _is_field_call(self, node: ast.AST) -> bool:
        """Check if node is a call to `Field` or `dataclasses.field`."""
        if isinstance(node, ast.Call):
            func = node.func
            name = self._get_name(func)
            return name in ("Field", "dataclasses.field", "field")
        return False

    def _process_field_call(self, call: ast.Call, attr: Attribute) -> None:
        """Extract metadata from `Field(...)` or `field(...)`."""
        # Iterate keyword arguments
        for kw in call.keywords:
            key = kw.arg
            val = kw.value
            if key is None:
                continue
            if key == "default":
                attr.default_value = ast.unparse(val)
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                                   expression=attr.default_value))
            elif key == "default_factory":
                attr.default_value = ast.unparse(val)
                attr.constraints.append(Constraint(type=ConstraintType.DEFAULT,
                                                   expression=attr.default_value))
            elif key == "description":
                if isinstance(val, ast.Constant):
                    attr.description = str(val.value)
            elif key == "min_length" or key == "minLength":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="min_length", value=str(val.value)))
            elif key == "max_length" or key == "maxLength":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="max_length", value=str(val.value)))
            elif key == "ge" or key == "gt" or key == "le" or key == "lt":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key=key, value=str(val.value)))
            elif key == "regex" or key == "pattern":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="pattern", value=str(val.value)))
            elif key == "alias":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="alias", value=str(val.value)))
            elif key == "title":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="title", value=str(val.value)))
            elif key == "uniqueItems":
                if isinstance(val, ast.Constant):
                    attr.annotations.append(Annotation(key="uniqueItems", value=str(val.value)))
            else:
                # Store unknown keyword as annotation for round‑trip
                attr.annotations.append(Annotation(key=f"field_{key}", value=ast.unparse(val)))

    # ── AST helpers ──────────────────────────────────────────────
    @staticmethod
    def _get_name(node: ast.AST) -> Optional[str]:
        """Get the string name of an AST node, e.g., 'ClassName', 'module.attr'."""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{ast.unparse(node.value)}.{node.attr}"
        if isinstance(node, ast.Call):
            return PythonModelParser._get_name(node.func)
        return None

    def _get_base_names(self, cls_node: ast.ClassDef) -> List[str]:
        """Return list of base class names (e.g., ['BaseModel', 'MyMixin'])."""
        bases = []
        for base in cls_node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
            elif isinstance(base, ast.Call):
                # e.g., `BaseModel(...)`, we take the callable name
                fname = self._get_name(base.func)
                if fname:
                    bases.append(fname)
        return bases

    def _get_decorator_names(self, cls_node: ast.ClassDef) -> List[str]:
        """Return list of decorator names (e.g., 'dataclass', 'pydantic.dataclasses.dataclass')."""
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
        """Store the arguments of @dataclass(...) as annotations on the entity."""
        for kw in decorator.keywords:
            if kw.arg:
                entity.annotations.append(Annotation(key=f"dataclass_{kw.arg}", value=ast.unparse(kw.value)))