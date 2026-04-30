# engines/document/writers/ssdm_writers/asyncapi_writer.py
"""
AsyncAPI Writer – serialises an SSDM_DOCUMENT into an AsyncAPI 2.x JSON document.

All data is obtained from typed SSDM fields, with AsyncAPI‑specific information
stored in the document’s `asyncapi_info` attribute.  No annotations are used.

Mapping rules (SSDM → AsyncAPI):
- document.title / document.version          → info.title / info.version
- document.description                        → info.description
- document.contact                            → info.contact
- document.license                            → info.license
- document.asyncapi_info.servers              → servers (name → url)
- document.asyncapi_info.channels (list of Operation) → channels
  - operation.channel                         → channel name
  - operation.type (publish/subscribe)        → channel operation (publish/subscribe)
  - operation.message_entity (MSDM Entity)    → message payload (JSON Schema)
- document.security_schemes                   → components.securitySchemes
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, List, Dict, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    OperationType,
    SecurityScheme,
)
from ...models.msdm_models import Entity, MSDMDocument
from ...models.base import BaseDocument


class AsyncAPIWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to AsyncAPI JSON."""

    name = "asyncapi"
    supported_extensions = (".asyncapi.json", ".asyncapi.yaml")  # we only write JSON for simplicity

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        spec: Dict[str, any] = {
            "asyncapi": "2.5.0",
            "info": self._build_info(document),
            "servers": self._build_servers(document),
            "channels": self._build_channels(document),
        }

        # Components (security schemes)
        components = {}
        if document.security_schemes:
            components["securitySchemes"] = self._build_security_schemes(document.security_schemes)
        # If there are type definitions (MSDM), we could output components.schemas,
        # but the SSDM model does not store them in asyncapi_info; we skip for now.

        if components:
            spec["components"] = components

        json_str = json.dumps(spec, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build info ──────────────────────────────────────────────────
    def _build_info(self, doc: SSDM_DOCUMENT) -> dict:
        info = {
            "title": doc.title or "Untitled",
            "version": doc.version or "1.0.0",
        }
        if doc.description:
            info["description"] = doc.description
        if doc.contact:
            contact = {}
            if doc.contact.name:
                contact["name"] = doc.contact.name
            if doc.contact.url:
                contact["url"] = doc.contact.url
            if doc.contact.email:
                contact["email"] = doc.contact.email
            if contact:
                info["contact"] = contact
        if doc.license:
            info["license"] = {
                "name": doc.license.name,
                "url": doc.license.url,
            }
        return info

    # ── Build servers ──────────────────────────────────────────────
    def _build_servers(self, doc: SSDM_DOCUMENT) -> dict:
        # Use asyncapi_info.servers if present (a dict of name → url)
        if doc.asyncapi_info and doc.asyncapi_info.servers:
            servers = {}
            for name, url in doc.asyncapi_info.servers.items():
                servers[name] = {"url": url, "protocol": "http"}  # default
            return servers
        # Fallback to document.servers
        servers = {}
        for server in doc.servers:
            name = server.description or server.url
            servers[name] = {"url": server.url, "protocol": "http"}
        return servers

    # ── Build channels ─────────────────────────────────────────────
    def _build_channels(self, doc: SSDM_DOCUMENT) -> dict:
        channels = {}
        operations_source: List[Operation] = []
        if doc.asyncapi_info and doc.asyncapi_info.channels:
            operations_source = doc.asyncapi_info.channels
        else:
            # Fallback: use document.operations if no asyncapi_info
            operations_source = doc.operations

        for op in operations_source:
            channel_name = op.channel or op.path or op.name
            if not channel_name:
                continue
            channel_entry = channels.setdefault(channel_name, {})
            # Determine if publish or subscribe
            op_type = op.type
            if op_type in (OperationType.PUBLISH, OperationType.SUBSCRIBE):
                # In AsyncAPI, operation ID is "publish" or "subscribe"
                asyncapi_op = "publish" if op_type == OperationType.PUBLISH else "subscribe"
            else:
                # Default to publish for other types? Or skip.
                asyncapi_op = "publish"

            operation_object = {}
            if op.description:
                operation_object["description"] = op.description
            # Message
            if op.message_entity:
                operation_object["message"] = {
                    "payload": self._entity_to_json_schema(op.message_entity)
                }
            else:
                # Default message
                operation_object["message"] = {"payload": {"type": "object"}}

            channel_entry[asyncapi_op] = operation_object

        return channels

    # ── Build security schemes ────────────────────────────────────
    def _build_security_schemes(self, schemes: List[SecurityScheme]) -> dict:
        result = {}
        for scheme in schemes:
            entry = {
                "type": scheme.type.value,
            }
            if scheme.description:
                entry["description"] = scheme.description
            if scheme.api_key_location:
                entry["in"] = scheme.api_key_location.value
                entry["name"] = scheme.api_key_param_name or "X-API-Key"
            if scheme.open_id_connect_url:
                entry["openIdConnectUrl"] = scheme.open_id_connect_url
            result[scheme.name] = entry
        return result

    # ── MSDM Entity → JSON Schema (simplified) ────────────────────
    @staticmethod
    def _entity_to_json_schema(entity: Entity) -> dict:
        schema = {
            "type": "object",
            "properties": {}
        }
        for attr in entity.attributes:
            prop = AsyncAPIWriter._attribute_to_json_schema(attr)
            schema["properties"][attr.name] = prop
        return schema

    @staticmethod
    def _attribute_to_json_schema(attr) -> dict:
        from ...models.msdm_models import ScalarType, DataType
        dt = attr.data_type
        base = dt.base
        type_map = {
            ScalarType.STRING: "string",
            ScalarType.INT: "integer",
            ScalarType.LONG: "integer",
            ScalarType.FLOAT: "number",
            ScalarType.DOUBLE: "number",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.DATE: "string",
            ScalarType.TIMESTAMP: "string",
            ScalarType.ANY: "object",
        }
        prop = {"type": type_map.get(base, "string")}
        if base == ScalarType.ARRAY and dt.element_type:
            prop["type"] = "array"
            prop["items"] = AsyncAPIWriter._attribute_to_json_schema(
                type("temp", (), {"data_type": dt.element_type})()
            )
        return prop