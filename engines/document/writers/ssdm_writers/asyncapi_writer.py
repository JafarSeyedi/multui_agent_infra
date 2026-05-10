# engines/document/writers/ssdm_writers/asyncapi_writer.py
"""
AsyncAPI Writer – serialises an SSDMDocument into an AsyncAPI 2.x JSON document.

All data is obtained from typed SSDM fields. AsyncAPI‑specific information
(such as server names and a dedicated channel list) is stored in the document’s
`metadata` dictionary under the key "asyncapi".

Mapping rules (SSDM → AsyncAPI):
- document.title / document.version          → info.title / info.version
- document.description                        → info.description
- document.contact                            → info.contact
- document.license                            → info.license
- document.metadata["asyncapi"]["servers"]    → servers (name → url)
- document.metadata["asyncapi"]["channels"]   → list of ServiceOperation objects (or direct)
- document.operations (if no asyncapi.channels) → channels (fallback)
- operation.channel                           → channel name
- operation.type (publish/subscribe)          → channel operation (publish/subscribe)
- operation.message_entity (MSDM Entity)      → message payload (JSON Schema)
- document.security_schemes                   → components.securitySchemes
"""
from __future__ import annotations

import json
from typing import Any

from ...models.msdm_models import Entity, ScalarType
from ...models.ssdm_models import ApiKeyLocation, AuthConfig, AuthMethod, ServiceOperation, OperationType
from ...models.ssdm_models import SSDMDocument
from .base_ssdm_writer import BaseSSDMWriter
from .base_ssdm_writer import SSDMWriteOptions


class AsyncAPIWriter(BaseSSDMWriter):
    """Serialises an SSDMDocument to AsyncAPI JSON."""

    name = "asyncapi"
    supported_extensions = (".asyncapi.json", ".asyncapi.yaml")  # we only write JSON for simplicity

    def __init__(self, options: SSDMWriteOptions | None = None):
        super().__init__(options)

    async def _write_design(self, document: SSDMDocument) -> bytes:
        spec: dict[str, Any] = {
            "asyncapi": "2.5.0",
            "info": self._build_info(document),
            "servers": self._build_servers(document),
            "channels": self._build_channels(document),
        }

        # Components (security schemes)
        components: dict[str, Any] = {}
        if document.security_schemes:
            components["securitySchemes"] = self._build_security_schemes(document.security_schemes)

        if components:
            spec["components"] = components

        json_str = json.dumps(spec, indent=2, ensure_ascii=False)
        return json_str.encode(getattr(self.options, "encoding", "utf-8") or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build info ──────────────────────────────────────────────────
    def _build_info(self, doc: SSDMDocument) -> dict[str, Any]:
        info: dict[str, Any] = {
            "title": doc.title or "Untitled",
            "version": doc.version or "1.0.0",
        }
        if doc.description:
            info["description"] = doc.description
        if doc.contact:
            contact: dict[str, str] = {}
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
    def _build_servers(self, doc: SSDMDocument) -> dict[str, Any]:
        # Use metadata["asyncapi"]["servers"] if present
        asyncapi_data = doc.metadata.get("asyncapi", {})
        servers_dict = asyncapi_data.get("servers", {})
        if servers_dict:
            servers: dict[str, Any] = {}
            for name, url in servers_dict.items():
                servers[name] = {"url": url, "protocol": "http"}  # default protocol
            return servers
        # Fallback to document.servers (but those are generic Server objects)
        servers = {}
        for server in doc.servers:
            name = server.description or server.url
            servers[name] = {"url": server.url, "protocol": "http"}
        return servers

    # ── Build channels ─────────────────────────────────────────────
    def _build_channels(self, doc: SSDMDocument) -> dict[str, Any]:
        channels: dict[str, Any] = {}
        # Try to get explicit channel list from metadata
        asyncapi_data = doc.metadata.get("asyncapi", {})
        operations_source = asyncapi_data.get("channels")
        if operations_source is None:
            operations_source = doc.operations

        for op in operations_source:
            channel_name = getattr(op, "channel", None) or op.path or op.name
            if not channel_name:
                continue
            channel_entry = channels.setdefault(channel_name, {})
            # Determine if publish or subscribe
            op_type = op.type
            if op_type in (OperationType.PUBLISH, OperationType.SUBSCRIBE):
                asyncapi_op = "publish" if op_type == OperationType.PUBLISH else "subscribe"
            else:
                # Default to publish for request‑response etc.
                asyncapi_op = "publish"

            operation_object: dict[str, Any] = {}
            if op.description:
                operation_object["description"] = op.description
            # Message
            if getattr(op, "message_entity", None):
                operation_object["message"] = {
                    "payload": self._entity_to_json_schema(op.message_entity)
                }
            else:
                operation_object["message"] = {"payload": {"type": "object"}}

            channel_entry[asyncapi_op] = operation_object

        return channels

    # ── Build security schemes (AuthConfig → AsyncAPI) ────────────
    def _build_security_schemes(self, schemes: list[AuthConfig]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for i, scheme in enumerate(schemes, start=1):
            entry: dict[str, Any] = {}
            # Map AuthMethod to AsyncAPI scheme type
            if scheme.method == AuthMethod.HTTP_BASIC:
                entry = {"type": "http", "scheme": "basic"}
            elif scheme.method == AuthMethod.BEARER_TOKEN:
                entry = {"type": "http", "scheme": "bearer"}
            elif scheme.method == AuthMethod.API_KEY:
                entry = {"type": "apiKey"}
                if scheme.location == ApiKeyLocation.HEADER:
                    entry["in"] = "header"
                elif scheme.location == ApiKeyLocation.QUERY:
                    entry["in"] = "query"
                elif scheme.location == ApiKeyLocation.COOKIE:
                    entry["in"] = "cookie"
                entry["name"] = scheme.param_name or "X-API-Key"
            elif scheme.method == AuthMethod.OAUTH2:
                entry = {"type": "oauth2"}
                # Simplified – we don't convert flows here
                pass
            elif scheme.method == AuthMethod.OPENID_CONNECT:
                entry = {"type": "openIdConnect", "openIdConnectUrl": scheme.open_id_connect_url}
            else:
                continue

            if scheme.annotations:
                for ann in scheme.annotations:
                    if ann.key == "description":
                        entry["description"] = ann.value
                        break

            result[f"security_{i}"] = entry
        return result

    # ── MSDM Entity → JSON Schema (simplified) ────────────────────
    @staticmethod
    def _entity_to_json_schema(entity: Entity) -> dict[str, Any]:
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {}
        }
        for attr in entity.attributes:
            prop = AsyncAPIWriter._attribute_to_json_schema(attr)
            schema["properties"][attr.name] = prop
        if entity.description:
            schema["description"] = entity.description
        return schema

    @staticmethod
    def _attribute_to_json_schema(attr: Any) -> dict[str, Any]:
        # attr is an Attribute object
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
        prop: dict[str, Any] = {"type": type_map.get(base, "string")}
        if base == ScalarType.ARRAY and dt.element_type:
            prop["type"] = "array"
            # Create a temporary attribute for the element type
            from ...models.msdm_models import Attribute
            temp_attr = Attribute(name="item", data_type=dt.element_type)
            prop["items"] = AsyncAPIWriter._attribute_to_json_schema(temp_attr)
        return prop