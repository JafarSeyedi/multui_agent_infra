# engines/document/writers/ssdm_writers/python_service_writer.py
"""
Python Service Writer – serialises an SSDMDocument  into a Python web service
file using the FastAPI framework.

All type information is derived from the typed SSDM and MSDM models without
annotations.  Each operation becomes a FastAPI route; MSDM entities become
Pydantic models.
"""
from __future__ import annotations

from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import ScalarType
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import ParameterLocation
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import SSDMDocument 
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions


# Mapping from MSDM scalar to Python type
SCALAR_TO_PYTHON: dict[ScalarType, str] = {
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
    ScalarType.ANY:       "Any",
}


class PythonServiceWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument  to a Python FastAPI service file."""

    name = "python_service"
    supported_extensions = (".py",)

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)
        self._imports: set[str] = set()
        self._generated_models: set[str] = set()

    async def _write_design(self, document: SSDMDocument ) -> bytes:
        lines: list[str] = []
        self._imports = {"from fastapi import FastAPI, Query, Path, Header, Cookie, Body, HTTPException"}
        self._generated_models.clear()

        # Build Pydantic models from MSDM type definitions
        if document.type_definitions:
            for entity in document.type_definitions.entities:
                self._write_pydantic_model(lines, entity)

        # Write app creation
        lines.append("")
        lines.append("app = FastAPI()")
        lines.append("")

        # Write routes for each operation
        for op in document.operations:
            self._write_route(lines, op)

        # Prepend imports
        import_block = "\n".join(sorted(self._imports))
        source = import_block + "\n\n" + "\n".join(lines)
        return source.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/x-python"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Pydantic model generator ────────────────────────────────────
    def _write_pydantic_model(self, lines: list[str], entity: Entity) -> None:
        model_name = self._safe_python_name(entity.name)
        if model_name in self._generated_models:
            return
        self._generated_models.add(model_name)

        lines.append(f"class {model_name}(BaseModel):")
        if entity.description:
            lines.append(f'    """{entity.description}"""')
        for attr in entity.attributes:
            py_type = self._datatype_to_python(attr.data_type, attr.required)
            default = ""
            if not attr.required:
                default = " = None"
            elif attr.default_value is not None:
                default = f" = {attr.default_value}"
            lines.append(f"    {attr.name}: {py_type}{default}")
        lines.append("")
        self._imports.add("from pydantic import BaseModel")

    # ── Route writer ────────────────────────────────────────────────
    def _write_route(self, lines: list[str], op: ServiceOperation) -> None:
        method = op.http_method.value.lower() if op.http_method else "get"
        path = op.path or "/"
        func_name = self._safe_python_name(op.name)

        # Build parameter list
        params: list[str] = []
        # Path/Query/Header/Cookie parameters
        for param in op.parameters:
            param_str = self._build_param_declaration(param)
            if param_str:
                params.append(param_str)

        # Request body
        body_param = None
        if op.request_body:
            body_param = self._build_body_declaration(op.request_body)

        # Combine parameters into function signature
        signature = ", ".join(params)
        if body_param:
            if signature:
                signature += ", "
            signature += body_param

        # Decorator
        lines.append(f"@app.{method}(\"{path}\")")
        lines.append(f"async def {func_name}({signature}):")
        if op.description:
            lines.append(f'    """{op.description}"""')

        # Default response
        response_type = "None"
        if op.responses:
            for resp in op.responses:
                if resp.status_code == "200" or resp.status_code == "201":
                    if resp.content_entity:
                        response_type = self._safe_python_name(resp.content_entity.name)
                        break
        # We could add response_model param, but we'll just show a placeholder
        lines.append(f"    # TODO: implement logic, return {response_type}")
        lines.append("    raise HTTPException(status_code=501, detail=\"Not implemented\")")
        lines.append("")

    # ── Parameter declaration ──────────────────────────────────────
    def _build_param_declaration(self, param: Parameter) -> str | None:
        py_type = self._param_type_to_python(param)
        if not py_type:
            return None
        loc = param.location
        if loc == ParameterLocation.PATH:
            default = "..." if param.required else "None"
            return f"{param.name}: {py_type} = Path(default={default}, description=\"{param.description or ''}\")"
        elif loc == ParameterLocation.QUERY:
            default = "..." if param.required else "None"
            return f"{param.name}: {py_type} = Query(default={default}, description=\"{param.description or ''}\")"
        elif loc == ParameterLocation.HEADER:
            default = "..." if param.required else "None"
            return f"{param.name}: {py_type} = Header(default={default}, description=\"{param.description or ''}\")"
        elif loc == ParameterLocation.COOKIE:
            default = "..." if param.required else "None"
            return f"{param.name}: {py_type} = Cookie(default={default}, description=\"{param.description or ''}\")"
        elif loc == ParameterLocation.BODY:
            return None  # body handled separately
        return None

    def _param_type_to_python(self, param: Parameter) -> str | None:
        if param.type_entity:
            return self._safe_python_name(param.type_entity.name)
        if param.type_entity:
            return param.type_entity.name
        return "str"

    # ── Request body declaration ───────────────────────────────────
    def _build_body_declaration(self, body: RequestBody) -> str | None:
        model_name = "Any"
        if body.content_entity:
            model_name = self._safe_python_name(body.content_entity.name)
        default = "..." if body.required else "None"
        return f"body: {model_name} = Body(default={default})"

    # ── DataType → Python type string ──────────────────────────────
    def _datatype_to_python(self, dt: DataType, required: bool) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_python(dt.element_type, True) if dt.element_type else "Any"
            self._imports.add("from typing import List")
            type_str = f"List[{inner}]"
        elif base == ScalarType.MAP:
            key = self._datatype_to_python(dt.key_type, True) if dt.key_type else "str"
            val = self._datatype_to_python(dt.value_type, True) if dt.value_type else "Any"
            self._imports.add("from typing import Dict")
            type_str = f"Dict[{key}, {val}]"
        elif base == ScalarType.REF and dt.ref_entity:
            type_str = self._safe_python_name(dt.ref_entity.name or "object")
        elif base == ScalarType.STRUCT:
            type_str = self._safe_python_name(dt.ref_entity.name or "object") if dt.ref_entity else "Dict[str, Any]"
        elif base in SCALAR_TO_PYTHON:
            py = SCALAR_TO_PYTHON[base]
            type_str = py
            # Add necessary imports for special types
            if py == "datetime.date":
                self._imports.add("import datetime")
            elif py == "datetime.time":
                self._imports.add("import datetime")
            elif py == "datetime.datetime":
                self._imports.add("import datetime")
            elif py == "datetime.timedelta":
                self._imports.add("import datetime")
            elif py == "uuid.UUID":
                self._imports.add("import uuid")
            elif py == "decimal.Decimal":
                self._imports.add("import decimal")
            elif py == "Any":
                self._imports.add("from typing import Any")
        else:
            type_str = "Any"
            self._imports.add("from typing import Any")

        # Optionality is handled by default value in function signature, not type itself
        # For Pydantic fields, we already handled required.
        return type_str

    @staticmethod
    def _safe_python_name(name: str) -> str:
        """Convert a string to a valid Python identifier."""
        return "".join(c if c.isalnum() else "_" for c in (name or "unnamed")).strip("_")
