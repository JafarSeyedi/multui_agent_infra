# engines/document/writers/ssdm_writers/mcp_writer.py
"""
MCP (Model Context Protocol) Writer – serialises an SSDM_DOCUMENT into an
MCP server manifest JSON.

Mapping rules (SSDM → MCP):
- SSDM_DOCUMENT.title          → name
- SSDM_DOCUMENT.description    → description
- Each Operation               → a tool entry
  - operation.name             → tool name
  - operation.description      → tool description
  - operation.parameters       → inputSchema (JSON Schema from MSDM or type_string)
  - operation.request_body     → inputSchema (if body schema present)
  - operation.responses        → outputSchema (optional, from response body)
- MSDM type definitions are inlined into the JSON Schema for tools.
"""

from __future__ import annotations
import json
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
    Entity,
    Attribute,
    DataType,
    ScalarType,
)
from ...models.base import BaseDocument


class MCPWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to an MCP server manifest JSON."""

    name = "mcp"
    supported_extensions = (".mcp.json",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        manifest: Dict[str, Any] = {
            "name": document.title or "untitled",
            "version": document.version or "1.0.0",
            "tools": [],
        }
        if document.description:
            manifest["description"] = document.description

        for op in document.operations:
            tool = {
                "name": op.name,
                "description": op.description or "",
                "inputSchema": self._build_input_schema(op),
            }
            # Optional output schema
            output_schema = self._build_output_schema(op)
            if output_schema:
                tool["outputSchema"] = output_schema

            manifest["tools"].append(tool)

        json_str = json.dumps(manifest, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build input schema for a tool ──────────────────────────────
    def _build_input_schema(self, op: Operation) -> dict:
        """
        Construct a JSON Schema from parameters and request body.
        """
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
        }
        required = []

        # Parameters
        for param in op.parameters:
            prop_schema = self._parameter_to_json_schema(param)
            schema["properties"][param.name] = prop_schema
            if param.required:
                required.append(param.name)

        # Request body
        if op.request_body and op.request_body.content_entity:
            body_schema = self._entity_to_json_schema(op.request_body.content_entity)
            schema["properties"]["body"] = body_schema
            if op.request_body.required:
                required.append("body")
        elif op.request_body:
            schema["properties"]["body"] = {"type": "object"}

        if required:
            schema["required"] = required
        return schema

    def _build_output_schema(self, op: Operation) -> Optional[dict]:
        """
        If any response defines a content entity, use the first one as output schema.
        """
        for resp in op.responses:
            if resp.content_entity:
                return self._entity_to_json_schema(resp.content_entity)
        return None

    # ── Parameter → JSON Schema property ────────────────────────────
    def _parameter_to_json_schema(self, param: Parameter) -> dict:
        if param.type_entity:
            return self._entity_to_json_schema(param.type_entity)
        if param.type_string:
            return {"type": param.type_string}
        return {"type": "string"}

    # ── MSDM Entity → JSON Schema object ───────────────────────────
    def _entity_to_json_schema(self, entity: Entity) -> dict:
        schema: Dict[str, Any] = {
            "type": "object",
            "properties": {},
        }
        required = []
        for attr in entity.attributes:
            prop = self._attribute_to_json_schema(attr)
            schema["properties"][attr.name] = prop
            if attr.required:
                required.append(attr.name)
        if required:
            schema["required"] = required
        return schema

    def _attribute_to_json_schema(self, attr: Attribute) -> dict:
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            items = self._attribute_to_json_schema(
                self._make_temp_attribute(dt.element_type)
            ) if dt.element_type else {"type": "string"}
            return {"type": "array", "items": items}
        if base == ScalarType.MAP:
            val = self._attribute_to_json_schema(
                self._make_temp_attribute(dt.value_type)
            ) if dt.value_type else {"type": "string"}
            return {"type": "object", "additionalProperties": val}
        if base == ScalarType.REF and dt.ref_entity:
            return {"$ref": f"#/definitions/{dt.ref_entity}"}
        if base == ScalarType.STRUCT:
            return {"type": "object"}
        return {"type": self._scalar_to_json_type(base)}

    @staticmethod
    def _scalar_to_json_type(base: ScalarType) -> str:
        mapping = {
            ScalarType.STRING: "string",
            ScalarType.INT: "integer",
            ScalarType.LONG: "integer",
            ScalarType.FLOAT: "number",
            ScalarType.DOUBLE: "number",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.DATE: "string",
            ScalarType.TIME: "string",
            ScalarType.TIMESTAMP: "string",
            ScalarType.DURATION: "string",
            ScalarType.UUID: "string",
            ScalarType.BINARY: "string",
            ScalarType.DECIMAL: "number",
            ScalarType.ANY: "object",
        }
        return mapping.get(base, "string")

    @staticmethod
    def _make_temp_attribute(dt: Optional[DataType]) -> Attribute:
        """Create a temporary attribute with the given DataType for recursive calls."""
        return Attribute(name="temp", data_type=dt or DataType(base=ScalarType.STRING))