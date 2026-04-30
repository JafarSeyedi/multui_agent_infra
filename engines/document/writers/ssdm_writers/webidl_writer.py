# engines/document/writers/ssdm_writers/webidl_writer.py
"""
Web IDL Writer – serialises an SSDM_DOCUMENT into a Web IDL text file (.webidl).

Maps operations to WebIDL interface methods with parameters and return types.
MSDM type entities are converted to WebIDL dictionaries or interfaces where possible.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
)
from ...models.base import BaseDocument


# MSDM scalar → WebIDL type mapping
SCALAR_TO_WEBIDL = {
    ScalarType.STRING:    "DOMString",
    ScalarType.INT:       "long",
    ScalarType.LONG:      "long long",
    ScalarType.FLOAT:     "float",
    ScalarType.DOUBLE:    "double",
    ScalarType.BOOLEAN:   "boolean",
    ScalarType.BINARY:    "ArrayBuffer",
    ScalarType.DATE:      "Date",
    ScalarType.TIMESTAMP: "Date",
    ScalarType.ANY:       "any",
    ScalarType.UUID:      "DOMString",
    ScalarType.DECIMAL:   "double",
    ScalarType.TIME:      "DOMString",
    ScalarType.DURATION:  "DOMString",
}


class WebIDLWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to a Web IDL file."""

    name = "webidl"
    supported_extensions = (".webidl",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        lines: List[str] = []
        interface_name = self._safe_name(document.title) if document.title else "Service"

        # Write dictionaries from MSDM entities first
        if document.type_definitions:
            for entity in document.type_definitions.entities:
                self._write_dictionary(lines, entity)

        lines.append(f"[Exposed=Window]")
        lines.append(f"interface {interface_name} {{")

        for op in document.operations:
            self._write_operation(lines, op)

        lines.append("};")
        return "\n".join(lines).encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Dictionary from MSDM Entity ──────────────────────────────
    def _write_dictionary(self, lines: List[str], entity: Entity) -> None:
        dict_name = entity.name
        lines.append(f"dictionary {dict_name} {{")
        for attr in entity.attributes:
            required = "required " if attr.required else ""
            wtype = self._datatype_to_webidl(attr.data_type)
            lines.append(f"  {required}{wtype} {attr.name};")
        lines.append("};")
        lines.append("")

    # ── Operation → WebIDL method ──────────────────────────────────
    def _write_operation(self, lines: List[str], op: Operation) -> None:
        ret_type = "void"
        # Determine return type from the first 200 response
        for resp in op.responses:
            if resp.status_code in ("200", "201") and resp.content_entity:
                ret_type = self._safe_name(resp.content_entity.name)
                break

        method_name = self._safe_name(op.name)
        # Gather parameters (only body and query – WebIDL doesn't have path/header directly)
        params = []
        for param in op.parameters:
            ptype = self._param_type_to_webidl(param)
            params.append(f"{ptype} {param.name}")
        if op.request_body and op.request_body.content_entity:
            body_type = self._safe_name(op.request_body.content_entity.name)
            params.append(f"{body_type} body")

        params_str = ", ".join(params)
        lines.append(f"  {ret_type} {method_name}({params_str});")

    def _param_type_to_webidl(self, param: Parameter) -> str:
        if param.type_entity:
            return param.type_entity.name
        if param.type_string:
            return param.type_string
        return "DOMString"

    def _datatype_to_webidl(self, dt: DataType) -> str:
        base = dt.base
        if base == ScalarType.ARRAY:
            inner = self._datatype_to_webidl(dt.element_type) if dt.element_type else "any"
            return f"sequence<{inner}>"
        if base == ScalarType.MAP:
            return "record<DOMString, any>"  # simplified
        if base == ScalarType.REF and dt.ref_entity:
            return dt.ref_entity
        if base == ScalarType.STRUCT:
            return dt.ref_entity if dt.ref_entity else "object"
        return SCALAR_TO_WEBIDL.get(base, "DOMString")

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in (name or "unnamed")).strip("_")