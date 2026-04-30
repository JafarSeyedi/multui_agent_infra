# engines/document/writers/ssdm_writers/raml_writer.py
"""
RAML 1.0 Writer – serialises an SSDM_DOCUMENT into a RAML 1.0 YAML file.

All data is obtained from typed SSDM fields; no annotations are used.
MSDM type definitions are converted to RAML types.
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
    SecurityScheme,
    Server,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
)
from ...models.base import BaseDocument

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required for RAML writer. Install with: pip install pyyaml")


class RAMLWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to a RAML 1.0 YAML file."""

    name = "raml"
    supported_extensions = (".raml",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        raml: Dict[str, Any] = {
            "#%RAML 1.0": "",
            "title": document.title or "Untitled API",
        }
        if document.version:
            raml["version"] = document.version
        if document.description:
            raml["description"] = document.description

        # Base URI from servers
        if document.servers:
            raml["baseUri"] = document.servers[0].url
            if len(document.servers) > 1:
                bases = {s.description or s.url: s.url for s in document.servers}
                raml["baseUriParameters"] = {"baseUri": {"enum": list(bases.values())}}

        # Media type
        raml["mediaType"] = "application/json"

        # Security schemes
        if document.security_schemes:
            raml["securitySchemes"] = self._build_security_schemes(document.security_schemes)

        # Types from MSDM
        if document.type_definitions:
            raml["types"] = self._build_types(document.type_definitions)

        # Resources from operations
        resources = self._build_resources(document.operations)
        for path, resource in resources.items():
            # Insert into RAML using dot notation (we'll build nested dict structure)
            self._set_nested_resource(raml, path, resource)

        yaml_str = yaml.dump(raml, default_flow_style=False, allow_unicode=True, sort_keys=False)
        return yaml_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/raml+yaml"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build resources tree ──────────────────────────────────────
    def _build_resources(self, operations: List[Operation]) -> Dict[str, Any]:
        """Group operations by path into a nested resource structure."""
        resources: Dict[str, Any] = {}
        # First pass: collect methods per path
        path_methods: Dict[str, Dict[str, Any]] = {}
        for op in operations:
            path = op.path or "/"
            path = path.rstrip("/") if path != "/" else "/"
            method = op.http_method.value.lower() if op.http_method else "get"
            if path not in path_methods:
                path_methods[path] = {}
            path_methods[path][method] = self._build_method(op)
        # Second pass: build nested resource tree
        # For simplicity, we'll store each path separately and then merge later via _set_nested_resource.
        # We'll just return a dict of path -> methods.
        # RAML expects nested resources with leading "/".
        # We'll convert each path into a nested dict structure.
        for path, methods in path_methods.items():
            resource_node = methods
            # Add resource-level description? Not directly from operations.
            resources[path] = resource_node
        return resources

    def _set_nested_resource(self, root: Dict[str, Any], path: str, resource: Dict[str, Any]) -> None:
        """Insert a resource into the RAML root dict by splitting the path."""
        if path == "/":
            # root level
            root.update(resource)
            return
        # Split and create nested '/' segments
        segments = [seg for seg in path.strip("/").split("/") if seg]
        current = root
        for seg in segments:
            if seg.startswith("{") and seg.endswith("}"):
                param_name = seg[1:-1]
                current = current.setdefault(f"/{seg}", {})
            else:
                current = current.setdefault(f"/{seg}", {})
        current.update(resource)

    # ── Build a single HTTP method ──────────────────────────────────
    def _build_method(self, op: Operation) -> dict:
        method_def: Dict[str, Any] = {}
        if op.description:
            method_def["description"] = op.description

        # Query parameters
        query_params = [p for p in op.parameters if p.location == ParameterLocation.QUERY]
        if query_params:
            method_def["queryParameters"] = {}
            for param in query_params:
                method_def["queryParameters"][param.name] = self._build_parameter(param)

        # Headers
        headers_params = [p for p in op.parameters if p.location == ParameterLocation.HEADER]
        if headers_params:
            method_def["headers"] = {}
            for param in headers_params:
                method_def["headers"][param.name] = self._build_parameter(param)

        # Body
        if op.request_body:
            method_def["body"] = self._build_body(op.request_body)

        # Responses
        if op.responses:
            method_def["responses"] = {}
            for resp in op.responses:
                method_def["responses"][resp.status_code] = self._build_response(resp)

        # Security
        if op.security:
            method_def["securedBy"] = [s for s in op.security]

        return method_def

    # ── Parameter definition ───────────────────────────────────────
    def _build_parameter(self, param: Parameter) -> dict:
        p: Dict[str, Any] = {}
        if param.description:
            p["description"] = param.description
        if param.required:
            p["required"] = True
        if param.type_entity:
            p["type"] = param.type_entity.name
        elif param.type_string:
            p["type"] = param.type_string
        else:
            p["type"] = "string"
        return p

    # ── Request body ──────────────────────────────────────────────
    def _build_body(self, body: RequestBody) -> dict:
        b: Dict[str, Any] = {}
        if body.description:
            b["description"] = body.description
        # Map content types
        if body.content_type_entities:
            b["properties"] = {}
            for mime, entity in body.content_type_entities.items():
                b["properties"][mime] = {
                    "type": entity.name
                }
        elif body.content_entity:
            b["application/json"] = {
                "type": body.content_entity.name
            }
        return b

    # ── Response ──────────────────────────────────────────────────
    def _build_response(self, resp: Response) -> dict:
        r: Dict[str, Any] = {}
        if resp.description:
            r["description"] = resp.description
        if resp.content_entity:
            r["body"] = {
                "application/json": {
                    "type": resp.content_entity.name
                }
            }
        elif resp.content_type_entities:
            r["body"] = {}
            for mime, entity in resp.content_type_entities.items():
                r["body"][mime] = {"type": entity.name}
        return r

    # ── Security schemes ──────────────────────────────────────────
    def _build_security_schemes(self, schemes: List[SecurityScheme]) -> dict:
        result = {}
        for s in schemes:
            entry = {"type": s.type.value}
            if s.description:
                entry["description"] = s.description
            if s.type.value == "apiKey":
                entry["describedBy"] = {
                    "headers": {
                        s.api_key_param_name or "X-API-Key": {
                            "type": "string"
                        }
                    }
                }
            result[s.name] = entry
        return result

    # ── Types from MSDM ────────────────────────────────────────────
    def _build_types(self, msdm: MSDMDocument) -> dict:
        types = {}
        for entity in msdm.entities:
            type_def: Dict[str, Any] = {"type": "object"}
            if entity.description:
                type_def["description"] = entity.description
            props = {}
            for attr in entity.attributes:
                props[attr.name] = self._attribute_to_raml_type(attr)
            if props:
                type_def["properties"] = props
            types[entity.name] = type_def
        return types

    def _attribute_to_raml_type(self, attr: Attribute) -> dict:
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            items = self._attribute_to_raml_type(
                Attribute(name="items", data_type=dt.element_type) if dt.element_type else Attribute(name="items", data_type=DataType(base=ScalarType.STRING))
            )
            return {"type": "array", "items": items}
        if base == ScalarType.MAP:
            # RAML doesn't have map, use object with additional properties?
            val = self._attribute_to_raml_type(Attribute(name="val", data_type=dt.value_type) if dt.value_type else Attribute(name="val", data_type=DataType(base=ScalarType.STRING)))
            return {"type": "object", "properties": {}}
        if base == ScalarType.REF:
            return {"type": dt.ref_entity or "string"}
        if base == ScalarType.STRUCT:
            return {"type": "object"}
        return {"type": self._scalar_to_raml_type(base)}

    @staticmethod
    def _scalar_to_raml_type(base: ScalarType) -> str:
        mapping = {
            ScalarType.STRING: "string",
            ScalarType.INT: "integer",
            ScalarType.LONG: "integer",
            ScalarType.FLOAT: "number",
            ScalarType.DOUBLE: "number",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.DATE: "date-only",
            ScalarType.TIME: "time-only",
            ScalarType.TIMESTAMP: "datetime-only",
            ScalarType.DURATION: "string",
            ScalarType.UUID: "string",
            ScalarType.BINARY: "file",
            ScalarType.DECIMAL: "number",
            ScalarType.ANY: "any",
        }
        return mapping.get(base, "string")