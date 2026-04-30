# engines/document/writers/ssdm_writers/openapi_writer.py
"""
OpenAPI (Swagger) Writer – serialises an SSDM_DOCUMENT into an OpenAPI 3.0 JSON
specification.

Uses only typed SSDM fields; all metadata, operations, parameters, request bodies,
responses, and security schemes are faithfully reproduced.
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


class OpenAPIWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to OpenAPI 3.0 JSON."""

    name = "openapi"
    supported_extensions = (".openapi.json",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        spec: Dict[str, Any] = {
            "openapi": "3.0.3",
            "info": self._build_info(document),
            "paths": self._build_paths(document),
        }

        if document.servers:
            spec["servers"] = self._build_servers(document.servers)

        components: Dict[str, Any] = {}
        if document.security_schemes:
            components["securitySchemes"] = self._build_security_schemes(document.security_schemes)
        if document.type_definitions:
            components["schemas"] = self._build_schemas(document.type_definitions)
        if components:
            spec["components"] = components

        json_str = json.dumps(spec, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Info block ──────────────────────────────────────────────────
    def _build_info(self, doc: SSDM_DOCUMENT) -> dict:
        info = {
            "title": doc.title or "Untitled",
            "version": doc.version or "1.0.0",
        }
        if doc.description:
            info["description"] = doc.description
        if doc.contact:
            info["contact"] = {}
            if doc.contact.name:
                info["contact"]["name"] = doc.contact.name
            if doc.contact.url:
                info["contact"]["url"] = doc.contact.url
            if doc.contact.email:
                info["contact"]["email"] = doc.contact.email
        if doc.license:
            info["license"] = {"name": doc.license.name}
            if doc.license.url:
                info["license"]["url"] = doc.license.url
        return info

    # ── Servers ────────────────────────────────────────────────────
    def _build_servers(self, servers: List[Server]) -> list:
        result = []
        for srv in servers:
            entry = {"url": srv.url}
            if srv.description:
                entry["description"] = srv.description
            if srv.variables:
                entry["variables"] = {
                    var: {"default": val} for var, val in srv.variables.items()
                }
            result.append(entry)
        return result

    # ── Paths ──────────────────────────────────────────────────────
    def _build_paths(self, doc: SSDM_DOCUMENT) -> dict:
        paths: Dict[str, dict] = {}
        for op in doc.operations:
            path = op.path or "/"
            method = (op.http_method.value if op.http_method else "get").lower()
            path_entry = paths.setdefault(path, {})
            path_entry[method] = self._build_operation(op)
        return paths

    def _build_operation(self, op: Operation) -> dict:
        oper: Dict[str, Any] = {
            "operationId": op.name,
        }
        if op.description:
            oper["description"] = op.description

        # Parameters
        if op.parameters:
            oper["parameters"] = []
            for param in op.parameters:
                oper["parameters"].append(self._build_parameter(param))

        # Request body
        if op.request_body:
            oper["requestBody"] = self._build_request_body(op.request_body)

        # Responses
        oper["responses"] = {}
        for resp in op.responses:
            oper["responses"][resp.status_code] = self._build_response(resp)
        if not oper["responses"]:
            oper["responses"]["200"] = {"description": "OK"}

        # Tags
        if op.tags:
            oper["tags"] = op.tags

        # Security
        if op.security:
            oper["security"] = [{s: []} for s in op.security]

        oper["deprecated"] = op.deprecated
        return oper

    # ── Parameter ──────────────────────────────────────────────────
    def _build_parameter(self, param: Parameter) -> dict:
        p = {
            "name": param.name,
            "in": param.location.value,
            "required": param.required,
        }
        if param.description:
            p["description"] = param.description
        if param.type_entity:
            p["schema"] = self._entity_to_json_schema(param.type_entity)
        elif param.type_string:
            p["schema"] = {"type": param.type_string}
        else:
            p["schema"] = {"type": "string"}
        return p

    # ── Request Body ──────────────────────────────────────────────
    def _build_request_body(self, body: RequestBody) -> dict:
        rb: Dict[str, Any] = {
            "content": {}
        }
        if body.description:
            rb["description"] = body.description
        rb["required"] = body.required

        # Determine media type – default JSON
        media_type = "application/json"
        if body.content_entity:
            schema = self._entity_to_json_schema(body.content_entity)
        elif body.content_type_entities:
            for mime, entity in body.content_type_entities.items():
                schema = self._entity_to_json_schema(entity)
                rb["content"][mime] = {"schema": schema}
            return rb
        else:
            schema = {"type": "object"}

        rb["content"][media_type] = {"schema": schema}
        return rb

    # ── Response ──────────────────────────────────────────────────
    def _build_response(self, resp: Response) -> dict:
        r: Dict[str, Any] = {}
        if resp.description:
            r["description"] = resp.description
        else:
            r["description"] = ""

        if resp.content_entity:
            r["content"] = {
                "application/json": {
                    "schema": self._entity_to_json_schema(resp.content_entity)
                }
            }
        elif resp.content_type_entities:
            r["content"] = {}
            for mime, entity in resp.content_type_entities.items():
                r["content"][mime] = {
                    "schema": self._entity_to_json_schema(entity)
                }

        if resp.headers:
            r["headers"] = {}
            for h in resp.headers:
                r["headers"][h.name] = {
                    "schema": {"type": h.type_string or "string"}
                }
        return r

    # ── Security Schemes ──────────────────────────────────────────
    def _build_security_schemes(self, schemes: List[SecurityScheme]) -> dict:
        result = {}
        for s in schemes:
            entry = {"type": s.type.value}
            if s.description:
                entry["description"] = s.description
            if s.type.value == "apiKey":
                entry["in"] = s.api_key_location.value if s.api_key_location else "header"
                entry["name"] = s.api_key_param_name or "X-API-Key"
            if s.open_id_connect_url:
                entry["openIdConnectUrl"] = s.open_id_connect_url
            result[s.name] = entry
        return result

    # ── Schemas from MSDM ─────────────────────────────────────────
    def _build_schemas(self, msdm: MSDMDocument) -> dict:
        schemas = {}
        for entity in msdm.entities:
            schemas[entity.name] = self._entity_to_json_schema(entity)
        return schemas

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
        if entity.description:
            schema["description"] = entity.description
        return schema

    def _attribute_to_json_schema(self, attr: Attribute) -> dict:
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            items = (
                self._attribute_to_json_schema(
                    Attribute(name="items", data_type=dt.element_type)
                )
                if dt.element_type
                else {"type": "string"}
            )
            return {"type": "array", "items": items}
        if base == ScalarType.MAP:
            val = (
                self._attribute_to_json_schema(
                    Attribute(name="val", data_type=dt.value_type)
                )
                if dt.value_type
                else {"type": "string"}
            )
            return {"type": "object", "additionalProperties": val}
        if base == ScalarType.REF and dt.ref_entity:
            return {"$ref": f"#/components/schemas/{dt.ref_entity}"}
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