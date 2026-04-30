"""
asyncapi_parser.py – AsyncAPI 2.x / 3.x parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    AsyncAPIInfo,
    ContactInfo,
    LicenseInfo,
    Server,
    SecurityScheme,
    OAuth2FlowInfo,
    Operation,
    RequestBody,
    Response,
    Parameter,
    ParameterLocation,
    OperationType,
    SecurityType,
    OAuth2Flow,
    ApiKeyLocation,
)
from ...models.msdm_models import MSDMDocument, Entity, Attribute


class AsyncAPIParser(BaseSSDMParser):
    """
    Parses AsyncAPI 2.x (and partially 3.x) specifications into SSDM_DOCUMENT.
    """

    name = "asyncapi"
    supported_extensions = (".yaml", ".yml", ".json")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        fmt = Path(source_name).suffix.lower()
        if fmt == ".json":
            spec = json.loads(text)
        else:
            spec = yaml.safe_load(text)

        if not isinstance(spec, dict):
            raise ValueError("AsyncAPI spec must be a JSON/YAML object")

        # Key sections
        info = spec.get("info", {})
        servers = spec.get("servers", {})
        channels = spec.get("channels", {})
        components = spec.get("components", {})

        # Build SSDM document
        doc = SSDM_DOCUMENT(
            document_id="",  # will be filled by caller
            title=info.get("title", Path(source_name).stem),
            version=info.get("version", "1.0.0"),
            description=info.get("description", ""),
            contact=self._parse_contact(info.get("contact")),
            license=self._parse_license(info.get("license")),
            servers=self._parse_servers(servers),
            security_schemes=self._parse_security_schemes(
                components.get("securitySchemes", {})
            ),
            operations=[],  # filled below
            type_definitions=None,  # will be set from components/schemas if present
            asyncapi_info=None,    # will be set below
        )

        # Resolve internal $refs (simple in‑document resolver)
        self._doc_spec = spec

        # Parse schemas as MSDM entities
        schemas = components.get("schemas", {})
        entities = []
        for name, schema in schemas.items():
            entity = self._schema_to_entity(schema, name)
            if entity:
                entities.append(entity)
        if entities:
            doc.type_definitions = MSDMDocument(entities=entities)

        # Save other reusable components (messages, parameters, etc.) as metadata for now
        doc.metadata["asyncapi:components"] = {
            key: components[key]
            for key in ("messages", "securitySchemes", "parameters", "correlationIds",
                        "operationTraits", "messageTraits", "serverBindings",
                        "channelBindings", "operationBindings", "messageBindings")
            if key in components
        }

        # Parse channels -> Operations
        operations = []
        for channel_name, channel_def in channels.items():
            ops = self._parse_channel(channel_name, channel_def)
            operations.extend(ops)

        doc.operations = operations

        # AsyncAPIInfo object
        doc.asyncapi_info = AsyncAPIInfo(
            asyncapi_version=spec.get("asyncapi", "2.5.0"),
            servers={k: v.get("url", "") for k, v in servers.items()},
            channels=operations,  # we can reuse the same list
        )

        doc.metadata["asyncapi:id"] = spec.get("id", "")
        doc.metadata["asyncapi:defaultContentType"] = spec.get("defaultContentType", "")
        doc.metadata["asyncapi:tags"] = spec.get("tags", [])

        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    #  Helpers – contact, license, servers
    # ------------------------------------------------------------------
    def _parse_contact(self, raw: Optional[dict]) -> Optional[ContactInfo]:
        if not raw:
            return None
        return ContactInfo(
            name=raw.get("name"),
            url=raw.get("url"),
            email=raw.get("email"),
        )

    def _parse_license(self, raw: Optional[dict]) -> Optional[LicenseInfo]:
        if not raw:
            return None
        return LicenseInfo(
            name=raw.get("name", "Proprietary"),
            url=raw.get("url"),
        )

    def _parse_servers(self, servers: dict) -> List[Server]:
        result = []
        for name, srv in servers.items():
            result.append(
                Server(
                    url=srv.get("url", ""),
                    description=srv.get("description", ""),
                    variables={k: v.get("default", "") for k, v in srv.get("variables", {}).items()},
                )
            )
        return result

    # ------------------------------------------------------------------
    #  Security schemes
    # ------------------------------------------------------------------
    def _parse_security_schemes(self, schemes: dict) -> List[SecurityScheme]:
        result = []
        for name, scheme in schemes.items():
            stype = scheme.get("type", "").lower()
            if stype == "oauth2":
                stype_enum = SecurityType.OAUTH2
            elif stype == "apikey":
                stype_enum = SecurityType.API_KEY
            elif stype in ("http", "httpApiKey"):
                http_scheme = scheme.get("scheme", "").lower()
                if http_scheme == "bearer":
                    stype_enum = SecurityType.HTTP_BEARER
                else:
                    stype_enum = SecurityType.HTTP_BASIC
            elif stype == "openidconnect":
                stype_enum = SecurityType.OPENID_CONNECT
            elif stype == "mutualtls":
                stype_enum = SecurityType.MUTUAL_TLS
            else:
                stype_enum = SecurityType.API_KEY  # fallback

            api_key_location = None
            api_key_param = None
            oauth2_flows = []

            if stype_enum == SecurityType.API_KEY:
                loc = scheme.get("in", "header")
                api_key_location = ApiKeyLocation.HEADER if loc == "header" else ApiKeyLocation.QUERY
                api_key_param = scheme.get("name", "X-API-Key")
            elif stype_enum == SecurityType.OAUTH2:
                flows = scheme.get("flows", {})
                for flow_name, flow_def in flows.items():
                    flow_map = {
                        "implicit": OAuth2Flow.IMPLICIT,
                        "password": OAuth2Flow.PASSWORD,
                        "clientCredentials": OAuth2Flow.CLIENT_CREDENTIALS,
                        "authorizationCode": OAuth2Flow.AUTHORIZATION_CODE,
                    }
                    flow_enum = flow_map.get(flow_name)
                    if flow_enum:
                        oauth2_flows.append(
                            OAuth2FlowInfo(
                                flow=flow_enum,
                                authorization_url=flow_def.get("authorizationUrl"),
                                token_url=flow_def.get("tokenUrl"),
                                refresh_url=flow_def.get("refreshUrl"),
                                scopes=flow_def.get("scopes", {}),
                            )
                        )

            result.append(
                SecurityScheme(
                    name=name,
                    type=stype_enum,
                    description=scheme.get("description"),
                    api_key_location=api_key_location,
                    api_key_param_name=api_key_param,
                    oauth2_flows=oauth2_flows,
                    open_id_connect_url=scheme.get("openIdConnectUrl"),
                )
            )
        return result

    # ------------------------------------------------------------------
    #  Channel parsing
    # ------------------------------------------------------------------
    def _parse_channel(self, channel_name: str, channel_def: dict) -> List[Operation]:
        operations = []
        # Publish operation: server sends to client (consumer)
        if "publish" in channel_def:
            op = self._parse_operation(channel_name, "publish", channel_def["publish"])
            operations.append(op)
        # Subscribe operation: client sends to server (producer)
        if "subscribe" in channel_def:
            op = self._parse_operation(channel_name, "subscribe", channel_def["subscribe"])
            operations.append(op)
        return operations

    def _parse_operation(self, channel_name: str, kind: str, op_def: dict) -> Operation:
        # Determine OperationType
        if kind == "publish":
            op_type = OperationType.PUBLISH
        else:
            op_type = OperationType.SUBSCRIBE

        operation_id = op_def.get("operationId", f"{kind}_{channel_name}")
        description = op_def.get("description") or op_def.get("summary", "")
        tags = op_def.get("tags", [])

        # Parameters – channel parameters are in channel definition itself,
        # but operation can also have parameters. We'll gather from channel parameters.
        # We'll extract channel parameters from the channel name? Not yet; we assume
        # parameters are part of the operation definition.
        params = []
        raw_params = op_def.get("parameters", [])
        for p in raw_params:
            params.append(
                Parameter(
                    name=p.get("name", ""),
                    location=ParameterLocation.PATH,  # channel parameters are path-like
                    required=p.get("required", False),
                    description=p.get("description", ""),
                    type_string=self._schema_type_string(p.get("schema", {})),
                )
            )

        # Message – there can be one or multiple messages (oneOf)
        message = op_def.get("message", {})
        if not message:
            # Could be absent; no body
            request_body = None
            response = None
        else:
            # Handle oneOf for multiple messages
            if "oneOf" in message:
                # For simplicity, take the first message (or create a composition entity)
                messages = message["oneOf"]
                message = messages[0] if messages else {}
            # Resolve $ref if present
            message = self._resolve_ref(message, "messages")

            # Extract payload
            payload = message.get("payload", {})
            if isinstance(payload, dict):
                entity = self._schema_to_entity(payload, f"{operation_id}_payload")
            else:
                entity = None  # could be a reference string, skip

            request_body = RequestBody(
                description=message.get("description", ""),
                required=True,  # messages are serialised as body
                content_entity=entity,
                is_binary=False,
            )
            # In AsyncAPI, there is no explicit response; we can leave response empty
            response = Response(status_code="200", description="Asynchronous message")

        return Operation(
            name=operation_id,
            type=op_type,
            description=description,
            http_method=None,
            path=channel_name,
            parameters=params,
            request_body=request_body,
            responses=[response] if response else [],
            security=[],  # security at operation level? AsyncAPI supports security. We skip.
            tags=tags,
            deprecated=op_def.get("deprecated", False),
        )

    # ------------------------------------------------------------------
    #  Schema to MSDM Entity (similar to OpenAPI parser)
    # ------------------------------------------------------------------
    def _schema_to_entity(self, schema: dict, name: str) -> Optional[Entity]:
        """Convert an AsyncAPI schema (JSON Schema compatible) to an Entity."""
        schema = self._resolve_ref(schema, "schemas")
        if not schema:
            return None

        type_ = schema.get("type")
        if type_ == "object" or "properties" in schema:
            attrs = []
            required_set = set(schema.get("required", []))
            for prop_name, prop_schema in schema.get("properties", {}).items():
                attr_type = self._schema_type_string(prop_schema)
                attr = Attribute(
                    name=prop_name,
                    type=attr_type,
                    required=prop_name in required_set,
                    description=prop_schema.get("description", ""),
                )
                attrs.append(attr)
            return Entity(name=name, attributes=attrs, description=schema.get("description"))
        elif type_ == "array":
            items = schema.get("items", {})
            inner = self._schema_type_string(items)
            return Entity(
                name=name,
                attributes=[Attribute(name="items", type=f"array<{inner}>")]
            )
        else:
            # Primitives
            return Entity(
                name=name,
                attributes=[Attribute(name="value", type=self._schema_type_string(schema))]
            )

    def _schema_type_string(self, schema: dict) -> str:
        """Return a string representation of the schema type."""
        if not schema:
            return "string"
        if "$ref" in schema:
            return schema["$ref"].split("/")[-1]
        type_ = schema.get("type", "string")
        if type_ == "integer":
            return "int"
        if type_ == "number":
            return "float"
        if type_ == "boolean":
            return "boolean"
        if type_ == "array":
            items = schema.get("items", {})
            if items:
                return f"array<{self._schema_type_string(items)}>"
            return "array"
        return type_

    # ------------------------------------------------------------------
    #  Simple $ref resolver (only #/components/...)
    # ------------------------------------------------------------------
    def _resolve_ref(self, obj, component_type: str):
        """Resolve $ref inside the same document."""
        if not isinstance(obj, dict):
            return obj
        ref = obj.get("$ref")
        if not ref:
            return obj
        if not ref.startswith("#/"):
            # external refs not resolved
            return {}
        path = ref[2:].split("/")
        if path[0] == "components" and len(path) >= 3 and path[1] == component_type:
            name = "/".join(path[2:])
            return self._doc_spec.get("components", {}).get(component_type, {}).get(name, {})
        return {}