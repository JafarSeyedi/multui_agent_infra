# engines/document/writers/ssdm_writers/openapi_writer.py
"""
OpenAPI (Swagger) Writer – serialises an SSDMDocument into an OpenAPI 3.0 JSON
specification.

Uses only typed SSDM fields; all metadata, operations, parameters, request bodies,
responses, and security schemes are faithfully reproduced.

Mapping logic:
- AuthConfig (security scheme) → OpenAPI Security Scheme Object
- ServiceOperation.security_requirements (list of dict) → OpenAPI `security` array
- ServiceOperation.version_status == DEPRECATED → deprecated: true
- Parameter.type_entity (Entity) → JSON Schema
- RequestBody/Response.content_entity → JSON Schema
- All x-* extensions are ignored (non‑standard)
"""
from __future__ import annotations

import json
from typing import Any

from ...models.msdm_models import Attribute
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.msdm_models import VersionStatus
from ...models.ssdm_models import ApiKeyLocation
from ...models.ssdm_models import AuthConfig
from ...models.ssdm_models import AuthMethod
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import Response
from ...models.ssdm_models import Server
from ...models.ssdm_models import SSDMDocument
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions


class OpenAPIWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument to OpenAPI 3.0 JSON."""

    name = "openapi"
    supported_extensions = (".openapi.json",)

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, document: SSDMDocument) -> bytes:
        spec: dict[str, Any] = {
            "openapi": "3.0.3",
            "info": self._build_info(document),
            "paths": self._build_paths(document),
        }

        if document.servers:
            spec["servers"] = self._build_servers(document.servers)

        components: dict[str, Any] = {}
        if document.security_schemes:
            components["securitySchemes"] = self._build_security_schemes(document.security_schemes)
        if document.type_definitions:
            components["schemas"] = self._build_schemas(document.type_definitions)
        if components:
            spec["components"] = components

        json_str = json.dumps(spec, indent=2, ensure_ascii=False)
        return json_str.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Info block ──────────────────────────────────────────────────
    def _build_info(self, doc: SSDMDocument) -> dict[str, Any]:
        info: dict[str, Any] = {
            "title": doc.title or "Untitled",
            "version": doc.version or "1.0.0",
        }
        if doc.description:
            info["description"] = doc.description
        if doc.contact:
            contact_dict: dict[str, str] = {}
            if doc.contact.name:
                contact_dict["name"] = doc.contact.name
            if doc.contact.url:
                contact_dict["url"] = doc.contact.url
            if doc.contact.email:
                contact_dict["email"] = doc.contact.email
            if contact_dict:
                info["contact"] = contact_dict
        if doc.license:
            info["license"] = {"name": doc.license.name}
            if doc.license.url:
                info["license"]["url"] = doc.license.url
        return info

    # ── Servers ────────────────────────────────────────────────────
    def _build_servers(self, servers: list[Server]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for srv in servers:
            entry: dict[str, Any] = {"url": srv.url}
            if srv.description:
                entry["description"] = srv.description
            if srv.variables:
                entry["variables"] = {
                    var: {"default": val} for var, val in srv.variables.items()
                }
            result.append(entry)
        return result

    # ── Paths ──────────────────────────────────────────────────────
    def _build_paths(self, doc: SSDMDocument) -> dict[str, dict[str, Any]]:
        paths: dict[str, dict[str, Any]] = {}
        for op in doc.operations:
            path: str = op.path or "/"
            method: str = (op.http_method.value if op.http_method else "get").lower()
            path_entry: dict[str, Any] = paths.setdefault(path, {})
            path_entry[method] = self._build_operation(op)
        return paths

    def _build_operation(self, op: ServiceOperation) -> dict[str, Any]:
        oper: dict[str, Any] = {
            "operationId": op.name,
        }
        if op.description:
            oper["description"] = op.description

        # Parameters
        if op.parameters:
            oper["parameters"] = [self._build_parameter(p) for p in op.parameters]

        # Request body
        if op.request_body:
            oper["requestBody"] = self._build_request_body(op.request_body)

        # Responses
        oper["responses"] = {}
        for resp in op.responses:
            oper["responses"][resp.status_code] = self._build_response(resp)
        if not oper["responses"]:
            oper["responses"]["200"] = {"description": "OK"}

        # Security requirements
        if op.security_requirements:
            oper["security"] = list(op.security_requirements)

        # Deprecated flag from version_status (correct field name)
        if op.version_status == VersionStatus.DEPRECATED:
            oper["deprecated"] = True

        return oper

    # ── Parameter ──────────────────────────────────────────────────
    def _build_parameter(self, param: Parameter) -> dict[str, Any]:
        p: dict[str, Any] = {
            "name": param.name,
            "in": param.location.value,
            "required": param.required,
        }
        if param.description:
            p["description"] = param.description

        # Build schema from type_entity or fallback
        if param.type_entity:
            p["schema"] = self._entity_to_json_schema(param.type_entity)
        else:
            p["schema"] = {"type": "string"}

        return p

    # ── Request Body ──────────────────────────────────────────────
    def _build_request_body(self, body: RequestBody) -> dict[str, Any]:
        rb: dict[str, Any] = {
            "content": {},
            "required": body.required,
        }
        if body.description:
            rb["description"] = body.description

        # Determine media types
        if body.content_entity:
            media_type: str = "application/json"
            rb["content"][media_type] = {
                "schema": self._entity_to_json_schema(body.content_entity)
            }
        elif body.content_type_entities:
            for mime, entity in body.content_type_entities.items():
                rb["content"][mime] = {
                    "schema": self._entity_to_json_schema(entity)
                }
        else:
            rb["content"]["application/json"] = {"schema": {"type": "object"}}

        return rb

    # ── Response ──────────────────────────────────────────────────
    def _build_response(self, resp: Response) -> dict[str, Any]:
        r: dict[str, Any] = {
            "description": resp.description or ""
        }
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

        # Headers (simplified)
        if resp.headers:
            r["headers"] = {}
            for h in resp.headers:
                header_schema: dict[str, Any] = {"schema": {"type": "string"}}
                if h.description:
                    header_schema["description"] = h.description
                r["headers"][h.name] = header_schema

        return r

    # ── Security Schemes (AuthConfig → OpenAPI) ────────────────────
    def _build_security_schemes(self, schemes: list[AuthConfig]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for s in schemes:
            entry: dict[str, Any] = {}
            # Map AuthMethod to OpenAPI type
            if s.method == AuthMethod.HTTP_BASIC:
                entry = {"type": "http", "scheme": "basic"}
            elif s.method == AuthMethod.BEARER_TOKEN:
                entry = {"type": "http", "scheme": "bearer"}
            elif s.method == AuthMethod.API_KEY:
                entry = {"type": "apiKey"}
                if s.location == ApiKeyLocation.HEADER:
                    entry["in"] = "header"
                elif s.location == ApiKeyLocation.QUERY:
                    entry["in"] = "query"
                elif s.location == ApiKeyLocation.COOKIE:
                    entry["in"] = "cookie"
                entry["name"] = s.param_name or "X-API-Key"
            elif s.method == AuthMethod.OAUTH2:
                entry = {"type": "oauth2"}
                if s.oauth2_flow:
                    flow_name = s.oauth2_flow.value
                    entry["flows"] = {
                        flow_name: {
                            "authorizationUrl": s.oauth2_authorization_url,
                            "tokenUrl": s.oauth2_token_url,
                            "scopes": {scope: scope for scope in s.oauth2_scopes}
                        }
                    }
            elif s.method == AuthMethod.OPENID_CONNECT:
                entry = {"type": "openIdConnect", "openIdConnectUrl": s.open_id_connect_url}
            elif s.method == AuthMethod.MUTUAL_TLS:
                entry = {"type": "mutualTLS"}
            else:
                continue

            if s.annotations:
                for ann in s.annotations:
                    if ann.key == "description":
                        entry["description"] = ann.value
                        break

            result[f"security_{len(result)+1}"] = entry
        return result

    # ── Schemas from MSDM ─────────────────────────────────────────
    def _build_schemas(self, msdm: MSDMDocument) -> dict[str, Any]:
        schemas: dict[str, Any] = {}
        for entity in msdm.entities:
            schemas[entity.name] = self._entity_to_json_schema(entity)
        return schemas

    def _entity_to_json_schema(self, entity: Entity) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {},
        }
        required: list[str] = []
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

    def _attribute_to_json_schema(self, attr: Attribute) -> dict[str, Any]:
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            if dt.element_type:
                # Create a dummy attribute for the item type
                item_attr = Attribute(name="item", data_type=dt.element_type)
                items_schema = self._attribute_to_json_schema(item_attr)
            else:
                items_schema = {"type": "string"}
            return {"type": "array", "items": items_schema}
        if base == ScalarType.MAP:
            if dt.value_type:
                val_attr = Attribute(name="value", data_type=dt.value_type)
                additional = self._attribute_to_json_schema(val_attr)
            else:
                additional = {"type": "string"}
            return {"type": "object", "additionalProperties": additional}
        if base == ScalarType.REF:
            ref_name = dt.ref_entity_id or (dt.ref_entity.name if dt.ref_entity else None)
            if ref_name:
                return {"$ref": f"#/components/schemas/{ref_name}"}
            return {"type": "object"}
        if base == ScalarType.STRUCT:
            return {"type": "object"}
        # scalar
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