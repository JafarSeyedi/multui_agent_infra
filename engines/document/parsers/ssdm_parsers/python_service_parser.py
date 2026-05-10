# engines/document/parsers/ssdm_parsers/python_service_parser.py
"""
Python Service Parser – parses a Python web service file (.py) built with
FastAPI (or Flask) and produces an SSDMDocument .

Every route becomes an ServiceOperation; Pydantic models become MSDM Entities.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import HttpMethod
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import ParameterLocation
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import Response
from ...models.ssdm_models import SSDMDocument
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser


# ── Python scalar → MSDM ScalarType ──────────────────────────────
PYTHON_SCALAR_MAP = {
    "str": ScalarType.STRING,
    "int": ScalarType.INT,
    "float": ScalarType.FLOAT,
    "bool": ScalarType.BOOLEAN,
    "bytes": ScalarType.BINARY,
    "date": ScalarType.DATE,
    "datetime": ScalarType.TIMESTAMP,
    "time": ScalarType.TIME,
    "timedelta": ScalarType.DURATION,
    "UUID": ScalarType.UUID,
    "Decimal": ScalarType.DECIMAL,
    "Any": ScalarType.ANY,
    "NoneType": ScalarType.ANY,
}

# Parameter location mapping
FASTAPI_PARAM_CLASSES = {
    "Query": ParameterLocation.QUERY,
    "Path": ParameterLocation.PATH,
    "Header": ParameterLocation.HEADER,
    "Cookie": ParameterLocation.COOKIE,
    "Body": ParameterLocation.BODY,
}


class PythonServiceParser(BaseSSDMParser):
    """Parser for Python web service files (.py)."""

    name = "python_service"
    supported_extensions = (".py",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        encoding = options.encoding or "utf-8"
        source = data.decode(encoding)
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")

        doc = SSDMDocument(
            title=Path(source_name).stem,
            document_id=source_name,  # temporary, will be overwritten by base parser
            media_type=MEDIA_TYPES["python_service"],
            version="1.0.0",
        )
        msdm = MSDMDocument(
            title="types",
            document_id="types",
            media_type=MEDIA_TYPES["python_model"],
        )

        # 1. Find the FastAPI/Flask app instance (look for `app = FastAPI()` or `app = Flask(__name__)`)
        app_var = self._find_app_instance(tree)

        # 2. Collect Pydantic models (classes inheriting from BaseModel) into MSDM
        self._collect_pydantic_models(tree, msdm)

        # 3. Parse route functions – also collect unresolved parameter type references
        param_refs: dict[Parameter, str] = {}
        self._parse_routes(tree, app_var, doc, msdm, param_refs)

        if msdm.entities:
            doc.type_definitions = msdm

        # 4. Second pass: resolve parameter type references to Entities
        self._resolve_parameter_types(param_refs, doc)

        return doc

    # ── Find app instance ────────────────────────────────────────
    def _find_app_instance(self, tree: ast.AST) -> str | None:
        """Return the variable name that holds the FastAPI/Flask app, e.g. 'app'."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    func = node.value.func
                    if self._get_name(func) in ("FastAPI", "Flask"):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                return target.id
        return None

    # ── Collect Pydantic models ──────────────────────────────────
    def _collect_pydantic_models(self, tree: ast.AST, msdm: MSDMDocument) -> None:
        """Find classes that inherit from BaseModel and add them as MSDM entities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [self._get_name(base) for base in node.bases]
                if any(b == "BaseModel" for b in bases):
                    entity = self._pydantic_class_to_entity(node)
                    msdm.entities.append(entity)

    def _pydantic_class_to_entity(self, node: ast.ClassDef) -> Entity:
        entity = Entity(name=node.name, description=ast.get_docstring(node))
        for stmt in node.body:
            if isinstance(stmt, ast.AnnAssign):
                if isinstance(stmt.target, ast.Name):
                    field_name = stmt.target.id
                    required = stmt.value is None  # no default → required
                    dt = self._annotation_to_datatype(stmt.annotation)
                    attr = Attribute(name=field_name, data_type=dt, required=required)
                    if stmt.value is not None and not self._is_field_call(stmt.value):
                        attr.default_value = ast.unparse(stmt.value)
                    entity.attributes.append(attr)
        return entity

    # ── Parse routes ─────────────────────────────────────────────
    def _parse_routes(
        self,
        tree: ast.AST,
        app_var: str | None,
        doc: SSDMDocument,
        msdm: MSDMDocument,
        param_refs: dict[Parameter, str],
    ) -> None:
        """Walk the AST and find decorated functions that are routes."""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if self._is_route_decorator(decorator, app_var):
                        # mypy cannot infer that decorator is always ast.Call here,
                        # but _is_route_decorator checks it. We add an assertion.
                        assert isinstance(decorator, ast.Call)
                        op = self._parse_route(node, decorator, msdm, param_refs)
                        doc.operations.append(op)
                        break  # one operation per route function

    def _is_route_decorator(self, decorator: ast.AST, app_var: str | None) -> bool:
        """Check if the decorator is `@app.get(...)`, `@app.post(...)`, etc."""
        if isinstance(decorator, ast.Call):
            func = decorator.func
            # Try `app.get` pattern
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                if app_var and func.value.id == app_var and func.attr in (
                    "get",
                    "post",
                    "put",
                    "delete",
                    "patch",
                    "head",
                    "options",
                    "trace",
                ):
                    return True
                # Also handle `app.route` for Flask
                if func.attr == "route":
                    return True
            # Try bare `app.get`? not possible without attribute.
        return False

    def _parse_route(
        self,
        func_def: ast.FunctionDef,
        decorator: ast.Call,
        msdm: MSDMDocument,
        param_refs: dict[Parameter, str],
    ) -> ServiceOperation:
        # Extract path and method from decorator
        path = "/"
        method = "get"
        if isinstance(decorator.func, ast.Attribute):
            method = decorator.func.attr.lower()
            if decorator.args:
                path = (
                    ast.literal_eval(decorator.args[0])
                    if isinstance(decorator.args[0], ast.Constant)
                    else str(ast.unparse(decorator.args[0]))
                )
        else:
            # route() case
            if decorator.args:
                path = (
                    ast.literal_eval(decorator.args[0])
                    if isinstance(decorator.args[0], ast.Constant)
                    else str(ast.unparse(decorator.args[0]))
                )
            # Look for methods kwarg
            for kw in decorator.keywords:
                if kw.arg == "methods":
                    methods = (
                        ast.literal_eval(kw.value)
                        if isinstance(kw.value, ast.Constant)
                        else ["GET"]
                    )
                    method = methods[0].lower() if methods else "get"

        # Convert method string to HttpMethod enum
        http_method = getattr(HttpMethod, method.upper(), None)

        op_name = f"{method.upper()} {path}"
        operation = ServiceOperation(
            name=op_name,
            http_method=http_method,
            path=path,
        )

        # Response model from decorator kwargs
        for kw in decorator.keywords:
            if kw.arg == "response_model":
                model_name = self._get_name(kw.value)
                if model_name:
                    resp_entity = Entity(name=model_name)
                    # We'll just reference it; the actual entity will be in type_definitions
                    resp = Response(status_code="200", content_entity=resp_entity)
                    operation.responses.append(resp)

        # Parse function parameters
        for arg in func_def.args.args:
            param = self._parse_func_arg(arg, param_refs)
            if param is not None:
                operation.parameters.append(param)

        # Determine request body from a parameter that is a Body or a Pydantic model not otherwise classified
        body_arg = None
        for arg in func_def.args.args:
            if self._is_body_argument(arg):
                body_arg = arg
                break
        if body_arg is None:
            # Fallback: first parameter not already assigned to path/query/header/cookie? Not reliable.
            pass
        if body_arg and body_arg.annotation:
            dt = self._annotation_to_datatype(body_arg.annotation)
            body_entity = self._datatype_to_entity(dt, f"{op_name}_Body")
            if body_entity:
                operation.request_body = RequestBody(content_entity=body_entity)

        # Remove body parameter from the parameter list (since it's handled as request body)
        operation.parameters = [
            p for p in operation.parameters if p.location != ParameterLocation.BODY
        ]

        return operation

    def _parse_func_arg(self, arg: ast.arg, param_refs: dict[Parameter, str]) -> Parameter | None:
        """Parse a function argument and return a Parameter, or None if not a parameter."""
        name = arg.arg
        annotation = arg.annotation
        if annotation is None:
            # Without annotation, assume query with Any type
            param = Parameter(
                name=name,
                location=ParameterLocation.QUERY,
                type_entity=None,
            )
            # No type reference to resolve
            return param

        # Check for Annotated[type, fastapi.param]
        if isinstance(annotation, ast.Subscript) and self._get_name(annotation.value) == "Annotated":
            # Extract base type and param metadata
            base_type_str = self._parse_annotated_type(annotation)
            param_meta = self._parse_annotated_metadata(annotation)
            location = param_meta.get("location", ParameterLocation.QUERY)
            # Ensure location is a ParameterLocation enum (the dict already holds enum values)
            if not isinstance(location, ParameterLocation):
                location = ParameterLocation.QUERY
            default = param_meta.get("default")
            required = default is None and location != ParameterLocation.PATH  # path is always required
            param = Parameter(
                name=name,
                location=location,
                required=required,
                type_entity=None,
            )
            # Store the base type string for later resolution
            if base_type_str:
                param_refs[param] = base_type_str
            return param

        # Otherwise, default to query parameter with the type
        dt = self._annotation_to_datatype(annotation)
        param = Parameter(
            name=name,
            location=ParameterLocation.QUERY,
            type_entity=None,
        )
        # Store a string representation of the type (e.g., "User", "List[int]")
        type_str = self._datatype_to_string(dt)
        param_refs[param] = type_str
        return param

    def _is_body_argument(self, arg: ast.arg) -> bool:
        """Check if the argument is annotated as a Body or a Pydantic model without other FastAPI markers."""
        if arg.annotation is None:
            return False
        if isinstance(arg.annotation, ast.Subscript) and self._get_name(arg.annotation.value) == "Annotated":
            metadata = self._parse_annotated_metadata(arg.annotation)
            return metadata.get("location") == ParameterLocation.BODY
        # Otherwise, if it's a Pydantic model, treat as body
        name = self._get_name(arg.annotation)
        return name is not None and not self._is_builtin_scalar(name)

    # ── Annotated extraction ────────────────────────────────────
    def _parse_annotated_type(self, node: ast.Subscript) -> str:
        """Return the base type string from Annotated[T, ...]."""
        if isinstance(node.slice, ast.Tuple):
            # Annotated[T, meta1, meta2]
            if node.slice.elts:
                return ast.unparse(node.slice.elts[0])
        # Python 3.9+ allows single expression without Tuple
        return ast.unparse(node.slice) if isinstance(node.slice, ast.AST) else "Any"

    def _parse_annotated_metadata(self, node: ast.Subscript) -> dict[str, Any]:
        """Extract a dict like {'location': ParameterLocation.QUERY, 'default': ...} from Annotated metadata."""
        meta: dict[str, Any] = {}
        if isinstance(node.slice, ast.Tuple):
            for elt in node.slice.elts[1:]:
                if isinstance(elt, ast.Call):
                    func_name = self._get_name(elt.func)
                    if func_name and func_name in FASTAPI_PARAM_CLASSES:
                        meta["location"] = FASTAPI_PARAM_CLASSES[func_name]
                    # Look for default keyword
                    for kw in elt.keywords:
                        if kw.arg == "default":
                            meta["default"] = (
                                ast.literal_eval(kw.value)
                                if isinstance(kw.value, ast.Constant)
                                else ast.unparse(kw.value)
                            )
        return meta

    # ── Type conversion helpers ──────────────────────────────────
    def _annotation_to_datatype(self, node: ast.AST) -> DataType:
        """Convert an AST annotation to MSDM DataType."""
        if isinstance(node, ast.Name):
            name = node.id
            if name in PYTHON_SCALAR_MAP:
                return DataType(base=PYTHON_SCALAR_MAP[name])
            # Could be a Pydantic model reference
            return DataType(base=ScalarType.REF, ref_entity_id=name)
        elif isinstance(node, ast.Subscript):
            # e.g., List[int], Optional[str], ...
            container = self._get_name(node.value)
            if container == "List":
                inner = self._annotation_to_datatype(
                    node.slice if not isinstance(node.slice, ast.Tuple) else node.slice.elts[0]
                )
                return DataType(base=ScalarType.ARRAY, element_type=inner)
            elif container == "Dict":
                if isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
                    key_dt = self._annotation_to_datatype(node.slice.elts[0])
                    val_dt = self._annotation_to_datatype(node.slice.elts[1])
                    return DataType(base=ScalarType.MAP, key_type=key_dt, value_type=val_dt)
            elif container == "Optional":
                inner = self._annotation_to_datatype(node.slice)
                return inner  # required handled elsewhere
        elif isinstance(node, ast.Constant) and node.value is None:
            return DataType(base=ScalarType.ANY)
        elif isinstance(node, ast.Attribute):
            full = ast.unparse(node)
            return DataType(base=ScalarType.REF, ref_entity_id=full)
        return DataType(base=ScalarType.ANY)

    def _datatype_to_entity(self, dt: DataType, name_hint: str) -> Entity | None:
        """Create a simple MSDM entity for a body type (if complex)."""
        if dt.base == ScalarType.REF and dt.ref_entity_id:
            return Entity(name=dt.ref_entity_id)
        if dt.base == ScalarType.ARRAY:
            inner = (
                self._datatype_to_entity(dt.element_type, name_hint + "_item")
                if dt.element_type
                else None
            )
            entity = Entity(name=name_hint)
            if inner:
                entity.attributes.append(
                    Attribute(
                        name="items",
                        data_type=dt.element_type or DataType(base=ScalarType.ANY),
                    )
                )
            return entity
        if dt.base == ScalarType.MAP:
            entity = Entity(name=name_hint)
            entity.attributes.append(Attribute(name="map", data_type=dt))
            return entity
        if dt.base == ScalarType.STRUCT:
            entity = Entity(name=name_hint)
            return entity
        return None

    @staticmethod
    def _datatype_to_string(dt: DataType) -> str:
        if dt.base == ScalarType.REF:
            return dt.ref_entity_id or "Any"
        return dt.base.value

    def _is_builtin_scalar(self, name: str) -> bool:
        return name in PYTHON_SCALAR_MAP

    # ── Resolution pass ─────────────────────────────────────────
    def _resolve_parameter_types(
        self, param_refs: dict[Parameter, str], doc: SSDMDocument
    ) -> None:
        """Second pass: resolve type reference strings to actual MSDM Entities."""
        if doc.type_definitions is None:
            return
        entity_by_name = {e.name: e for e in doc.type_definitions.entities}
        for param, type_str in param_refs.items():
            # The type_str may be something like "User" or "List[int]". For simplicity,
            # we extract the base name if it's a simple reference. For complex types,
            # we may need more advanced resolution; here we only handle simple names.
            # We also strip any subscript part (e.g., "List[int]" -> "List") if needed.
            base_name = type_str.split("[")[0]  # e.g., "List" from "List[int]"
            if base_name in entity_by_name:
                param.type_entity = entity_by_name[base_name]
            elif type_str in entity_by_name:
                param.type_entity = entity_by_name[type_str]
            # Otherwise leave as None

    # ── AST helpers ─────────────────────────────────────────────
    @staticmethod
    def _get_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{PythonServiceParser._get_name(node.value)}.{node.attr}" if node.value else node.attr
        if isinstance(node, ast.Call):
            return PythonServiceParser._get_name(node.func)
        return None

    @staticmethod
    def _is_field_call(node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            func = node.func
            name = PythonServiceParser._get_name(func)
            # Ensure name is not None before using 'in'
            return name is not None and ("Field" in name or "field" in name)
        return False