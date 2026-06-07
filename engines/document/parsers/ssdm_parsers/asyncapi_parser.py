# engines/document/parsers/ssdm_parsers/asyncapi_parser.py
"""
AsyncAPI 2.x / 3.x parser → SSDMDocument

All AsyncAPI‑specific data is stored in the document's `metadata` dictionary
under the key "asyncapi". Security schemes are mapped to `AuthConfig`.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Attribute, DataType, Entity, EntityKind, MSDMDocument, ScalarType, VersionStatus, Annotation
)
from ...models.ssdm_models import (
    ApiKeyLocation, AuthConfig, AuthMethod, ContactInfo, LicenseInfo,
    ServiceOperation, OperationType, Parameter, ParameterLocation, RequestBody,
    Response, SecurityRequirement, Server, SSDMDocument, OAuth2Flow
)
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser


class AsyncAPIParser(BaseSSDMParser):
    """
    Parses AsyncAPI 2.x (and partially 3.x) specifications into SSDMDocument.
    """

    name = "asyncapi"
    supported_extensions = (".yaml", ".yml", ".json")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
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
        doc = SSDMDocument(
            document_id=source_name,  # temporary, will be overwritten
            title=info.get("title", Path(source_name).stem),
            version=info.get("version", "1.0.0"),
            media_type=MEDIA_TYPES["asyncapi"],
            description=info.get("description", ""),
            contact=self._parse_contact(info.get("contact")),
            license=self._parse_license(info.get("license")),
            servers=self._parse_servers(servers),
            security_schemes=self._parse_security_schemes(components.get("securitySchemes", {})),
            operations=[],  # filled below
            type_definitions=None,  # will be set from components/schemas if present
        )

        # Keep the spec for $ref resolution
        self._doc_spec = spec

        # Parse schemas as MSDM entities
        schemas = components.get("schemas", {})
        entities: list[Entity] = []
        for name, schema in schemas.items():
            entity = self._schema_to_entity(schema, name)
            if entity:
                entities.append(entity)
        if entities:
            doc.type_definitions = MSDMDocument(
                title="asyncapi_schemas",
                document_id=f"{source_name}_schemas",
                media_type=MEDIA_TYPES["asyncapi"],
                entities=entities
            )

        # Store other reusable components in metadata
        doc.metadata["asyncapi"] = {
            "id": spec.get("id", ""),
            "defaultContentType": spec.get("defaultContentType", ""),
            "tags": spec.get("tags", []),
            "components": {
                key: components[key]
                for key in ("messages", "parameters", "correlationIds",
                            "operationTraits", "messageTraits", "serverBindings",
                            "channelBindings", "operationBindings", "messageBindings")
                if key in components
            }
        }

        # Parse channels -> Operations
        operations: list[ServiceOperation] = []
        for channel_name, channel_def in channels.items():
            ops = self._parse_channel(channel_name, channel_def)
            operations.extend(ops)

        doc.operations = operations

        # Store AsyncAPI version and server list in metadata
        doc.metadata["asyncapi"]["asyncapi_version"] = spec.get("asyncapi", "2.5.0")
        doc.metadata["asyncapi"]["servers"] = {
            k: v.get("url", "") for k, v in servers.items()
        }

        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    #  Helpers – contact, license, servers
    # ------------------------------------------------------------------
    def _parse_contact(self, raw: dict | None) -> ContactInfo | None:
        if not raw:
            return None
        return ContactInfo(
            name=raw.get("name"),
            url=raw.get("url"),
            email=raw.get("email"),
        )

    def _parse_license(self, raw: dict | None) -> LicenseInfo | None:
        if not raw:
            return None
        return LicenseInfo(
            name=raw.get("name", "Proprietary"),
            url=raw.get("url"),
        )

    def _parse_servers(self, servers: dict) -> list[Server]:
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
    #  Security schemes → AuthConfig
    # ------------------------------------------------------------------
    def _parse_security_schemes(self, schemes: dict) -> list[AuthConfig]:
        result: list[AuthConfig] = []
        for name, scheme in schemes.items():
            stype = scheme.get("type", "").lower()
            auth = AuthConfig(method=AuthMethod.NONE)

            if stype == "http":
                http_scheme = scheme.get("scheme", "").lower()
                if http_scheme == "basic":
                    auth.method = AuthMethod.HTTP_BASIC
                elif http_scheme == "bearer":
                    auth.method = AuthMethod.BEARER_TOKEN
            elif stype == "apiKey":
                auth.method = AuthMethod.API_KEY
                loc = scheme.get("in", "header")
                if loc == "header":
                    auth.location = ApiKeyLocation.HEADER
                elif loc == "query":
                    auth.location = ApiKeyLocation.QUERY
                elif loc == "cookie":
                    auth.location = ApiKeyLocation.COOKIE
                auth.param_name = scheme.get("name", "X-API-Key")
            elif stype == "oauth2":
                auth.method = AuthMethod.OAUTH2
                flows = scheme.get("flows", {})
                # Take the first flow (simplified)
                for flow_name, flow_def in flows.items():
                    flow_map = {
                        "implicit": "implicit",
                        "password": "password",
                        "clientCredentials": "clientCredentials",
                        "authorizationCode": "authorizationCode",
                    }
                    if flow_name in flow_map:
                        auth.oauth2_flow = getattr(OAuth2Flow, flow_name.upper(), None)
                        auth.oauth2_authorization_url = flow_def.get("authorizationUrl")
                        auth.oauth2_token_url = flow_def.get("tokenUrl")
                        auth.oauth2_scopes = list(flow_def.get("scopes", {}).keys())
                        break
            elif stype == "openIdConnect":
                auth.method = AuthMethod.OPENID_CONNECT
                auth.open_id_connect_url = scheme.get("openIdConnectUrl")
            elif stype == "mutualTLS":
                auth.method = AuthMethod.MUTUAL_TLS
            else:
                continue  # skip unsupported

            # Store description and any x-* as annotations
            if "description" in scheme:
                auth.annotations.append(Annotation(key="description", value=scheme["description"]))
            for key, val in scheme.items():
                if key.startswith("x-"):
                    auth.annotations.append(Annotation(key=key[2:], value=str(val)))

            result.append(auth)
        return result

    # ------------------------------------------------------------------
    #  Channel parsing
    # ------------------------------------------------------------------
    def _parse_channel(self, channel_name: str, channel_def: dict) -> list[ServiceOperation]:
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

    def _parse_operation(self, channel_name: str, kind: str, op_def: dict) -> ServiceOperation:
        op_type = OperationType.PUBLISH if kind == "publish" else OperationType.SUBSCRIBE
        operation_id = op_def.get("operationId", f"{kind}_{channel_name}")
        description = op_def.get("description") or op_def.get("summary", "")
        _tags = op_def.get("tags", [])

        # Parameters
        params = []
        raw_params = op_def.get("parameters", [])
        for p in raw_params:
            p = self._resolve_ref(p, "parameters")
            if not p:
                continue
            param = Parameter(
                name=p.get("name", ""),
                location=ParameterLocation.PATH,
                required=p.get("required", False),
                description=p.get("description", ""),
                type_entity=None,
            )
            if "schema" in p:
                param.annotations.append(Annotation(key="schema", value=str(p["schema"])))
            params.append(param)

        # Message payload
        message = op_def.get("message", {})
        request_body = None
        response = None

        if message:
            if "oneOf" in message:
                messages = message["oneOf"]
                message = messages[0] if messages else {}
            message = self._resolve_ref(message, "messages")
            if message:
                payload = message.get("payload", {})
                if isinstance(payload, dict):
                    entity = self._schema_to_entity(payload, f"{operation_id}_payload")
                    if entity:
                        request_body = RequestBody(
                            description=message.get("description", ""),
                            required=True,
                            content_entity=entity,
                            is_binary=False,
                        )
                response = Response(status_code="200", description="Asynchronous message")

        # Security requirements – convert to SecurityRequirement objects
        security_reqs: list[SecurityRequirement] = []
        raw_security = op_def.get("security", [])
        for sec in raw_security:
            if isinstance(sec, dict):
                for name, scopes in sec.items():
                    security_reqs.append(SecurityRequirement(name=name, scopes=scopes))

        version_status = VersionStatus.DEPRECATED if op_def.get("deprecated") else None

        return ServiceOperation(
            name=operation_id,
            type=op_type,
            description=description,
            http_method=None,
            path=channel_name,
            parameters=params,
            request_body=request_body,
            responses=[response] if response else [],
            security_requirements=security_reqs,
            version_status=version_status,
        )
 
    # ------------------------------------------------------------------
    #  Schema to MSDM Entity
    # ------------------------------------------------------------------
    def _schema_to_entity(self, schema: dict, name: str) -> Entity | None:
        """Convert an AsyncAPI schema (JSON Schema compatible) to an Entity."""
        schema = self._resolve_ref(schema, "schemas")
        if not schema:
            return None

        type_ = schema.get("type")
        if type_ == "object" or "properties" in schema:
            attrs = []
            required_set = set(schema.get("required", []))
            for prop_name, prop_schema in schema.get("properties", {}).items():
                data_type = self._schema_to_datatype(prop_schema)
                attr = Attribute(
                    name=prop_name,
                    data_type=data_type,
                    required=prop_name in required_set,
                    description=prop_schema.get("description", ""),
                )
                attrs.append(attr)
            return Entity(name=name, kind=EntityKind.OBJECT, attributes=attrs, description=schema.get("description"))
        elif type_ == "array":
            items = schema.get("items", {})
            item_dt = self._schema_to_datatype(items)
            return Entity(
                name=name,
                kind=EntityKind.OBJECT,
                attributes=[Attribute(name="items", data_type=DataType(base=ScalarType.ARRAY, element_type=item_dt))],
                description=schema.get("description"),
            )
        else:
            # Primitives
            scalar_dt = self._schema_to_datatype(schema)
            return Entity(
                name=name,
                kind=EntityKind.OBJECT,
                attributes=[Attribute(name="value", data_type=scalar_dt)],
                description=schema.get("description"),
            )

    def _schema_to_datatype(self, schema: dict) -> DataType:
        """Convert an AsyncAPI schema to an MSDM DataType."""
        if not schema:
            return DataType(base=ScalarType.STRING)
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return DataType(base=ScalarType.REF, ref_entity_id=ref_name)
        type_ = schema.get("type", "string")
        if type_ == "integer":
            return DataType(base=ScalarType.INT)
        if type_ == "number":
            return DataType(base=ScalarType.FLOAT)
        if type_ == "boolean":
            return DataType(base=ScalarType.BOOLEAN)
        if type_ == "array":
            items = schema.get("items", {})
            item_dt = self._schema_to_datatype(items)
            return DataType(base=ScalarType.ARRAY, element_type=item_dt)
        if type_ == "object":
            # We treat as a reference to an object – but we don't have the entity name yet.
            # For simplicity, return ANY.
            return DataType(base=ScalarType.ANY)
        return DataType(base=ScalarType.STRING)

    # ------------------------------------------------------------------
    #  Simple $ref resolver (only #/components/...)
    # ------------------------------------------------------------------
    def _resolve_ref(self, obj, component_type: str) -> dict:
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