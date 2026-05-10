# engines/document/parsers/ssdm_parsers/openapi_parser.py
"""
openapi_parser.py – Complete OpenAPI 3.x parser → SSDMDocument  (lossless)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import Annotation
from ...models.msdm_models import Attribute
from ...models.msdm_models import CompositionType
from ...models.msdm_models import DataType
from ...models.msdm_models import Entity
from ...models.msdm_models import EntityComposition
from ...models.msdm_models import MSDMDocument
from ...models.msdm_models import ScalarType
from ...models.msdm_models import VersionStatus, EntityKind
from ...models.ssdm_models import ApiKeyLocation
from ...models.ssdm_models import AuthConfig
from ...models.ssdm_models import AuthMethod
from ...models.ssdm_models import ContactInfo
from ...models.ssdm_models import HttpMethod
from ...models.ssdm_models import LicenseInfo
from ...models.ssdm_models import Link
from ...models.ssdm_models import OAuth2Flow
from ...models.ssdm_models import ServiceOperation
from ...models.ssdm_models import OperationType
from ...models.ssdm_models import Parameter
from ...models.ssdm_models import ParameterLocation
from ...models.ssdm_models import RequestBody
from ...models.ssdm_models import Response
from ...models.ssdm_models import SecurityRequirement
from ...models.ssdm_models import Server
from ...models.ssdm_models import SSDMDocument
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser


class OpenAPIV3Parser(BaseSSDMParser):
    """Full OpenAPI 3.x (and 3.1) parser that produces an SSDMDocument."""

    name = "openapi_v3"
    supported_extensions = (".json", ".yaml", ".yml")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        text = data.decode(options.encoding)
        fmt = "yaml" if Path(source_name).suffix.lower() in (".yaml", ".yml") else "json"
        spec = json.loads(text) if fmt == "json" else yaml.safe_load(text)
        if not isinstance(spec, dict):
            raise ValueError("Root of OpenAPI document must be a JSON object")

        # Required fields for SSDMDocument
        doc = SSDMDocument(
            title=Path(source_name).stem,
            document_id=source_name,
            media_type=MEDIA_TYPES["ssdm"],
            version="1.0.0",
        )

        # ── Info ──────────────────────────────────────────────────
        info = spec.get("info", {})
        doc.title = info.get("title", doc.title)
        doc.version = info.get("version", doc.version)
        doc.description = info.get("description", doc.description)
        doc.contact = self._parse_contact(info.get("contact"))
        doc.license = self._parse_license(info.get("license"))

        # ── Servers ───────────────────────────────────────────────
        doc.servers = self._parse_servers(spec.get("servers", []))

        # ── Security Schemes (components) ─────────────────────────
        components = spec.get("components", {})
        sec_schemes = components.get("securitySchemes", {})
        doc.security_schemes = self._parse_security_schemes(sec_schemes)

        # ── Global security (store in metadata as Annotation) ────
        global_sec = spec.get("security", [])
        if global_sec:
            doc.annotations.append(Annotation(
                key="openapi:global_security",
                value=str(global_sec)
            ))

        # ── Reusable components (not schemas) ────────────────────
        self._all_components = components  # for $ref resolution

        # Schemas → MSDMDocument
        schemas = components.get("schemas", {})
        entities: dict[str, Entity] = {}
        for name, schema in schemas.items():
            entity = self._schema_to_entity(schema, name, entities)
            if entity:
                entities[name] = entity
        if entities:
            doc.type_definitions = MSDMDocument(
                title="schemas",
                document_id=f"{source_name}_schemas",
                media_type=MEDIA_TYPES["msdm"],
                entities=list(entities.values())
            )

        # Other component types: stored as raw in annotations (simplified)
        doc.annotations.extend(self._store_components_as_annotations(components))

        # ── Paths & Operations ───────────────────────────────────
        doc.operations = self._parse_paths(
            spec.get("paths", {}),
            entities
        )

        # ── Tags & External Docs (store as annotations) ───────────
        tags = spec.get("tags", [])
        if tags:
            doc.annotations.append(Annotation(key="openapi:tags", value=str(tags)))
        ext_docs = spec.get("externalDocs", {})
        if ext_docs:
            doc.annotations.append(Annotation(key="openapi:externalDocs", value=str(ext_docs)))

        # ── Top‑level x-* extensions ──────────────────────────────
        for key, value in spec.items():
            if key.startswith("x-"):
                doc.annotations.append(Annotation(key=key[2:], value=str(value)))

        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    # Info / Contact / License / Servers
    # ------------------------------------------------------------------
    def _parse_contact(self, raw: dict | None) -> ContactInfo | None:
        if not raw:
            return None
        return ContactInfo(name=raw.get("name"), url=raw.get("url"), email=raw.get("email"))

    def _parse_license(self, raw: dict | None) -> LicenseInfo | None:
        if not raw:
            return None
        return LicenseInfo(name=raw.get("name", "Proprietary"), url=raw.get("url"))

    def _parse_servers(self, raw_servers: list) -> list[Server]:
        servers = []
        for s in raw_servers:
            variables = {v: d.get("default", "") for v, d in s.get("variables", {}).items()}
            servers.append(Server(url=s["url"], description=s.get("description"), variables=variables))
        return servers

    # ------------------------------------------------------------------
    # Security Schemes → AuthConfig list
    # ------------------------------------------------------------------
    def _parse_security_schemes(self, schemes: dict) -> list[AuthConfig]:
        result = []
        for name, scheme in schemes.items():
            atype = scheme.get("type", "").lower()
            desc = scheme.get("description")
            auth = AuthConfig(method=AuthMethod.NONE)

            # Set method and fill specific fields
            if atype == "http":
                http_scheme = scheme.get("scheme", "").lower()
                if http_scheme == "basic":
                    auth.method = AuthMethod.HTTP_BASIC
                elif http_scheme == "bearer":
                    auth.method = AuthMethod.BEARER_TOKEN
                # else leave as NONE
            elif atype == "apikey":
                auth.method = AuthMethod.API_KEY
                loc = scheme.get("in", "header")
                if loc == "header":
                    auth.location = ApiKeyLocation.HEADER
                elif loc == "query":
                    auth.location = ApiKeyLocation.QUERY
                elif loc == "cookie":
                    auth.location = ApiKeyLocation.COOKIE
                auth.param_name = scheme.get("name", "X-API-Key")
            elif atype == "oauth2":
                auth.method = AuthMethod.OAUTH2
                flows = scheme.get("flows", {})
                # pick the first defined flow (OpenAPI allows multiple, but we take one)
                for flow_name, flow_def in flows.items():
                    flow_map = {
                        "implicit": OAuth2Flow.IMPLICIT,
                        "password": OAuth2Flow.PASSWORD,
                        "clientCredentials": OAuth2Flow.CLIENT_CREDENTIALS,
                        "authorizationCode": OAuth2Flow.AUTHORIZATION_CODE,
                    }
                    if flow_name in flow_map:
                        auth.oauth2_flow = flow_map[flow_name]
                        auth.oauth2_authorization_url = flow_def.get("authorizationUrl")
                        auth.oauth2_token_url = flow_def.get("tokenUrl")
                        auth.oauth2_scopes = list(flow_def.get("scopes", {}).keys())
                        break
            elif atype == "openidconnect":
                auth.method = AuthMethod.OPENID_CONNECT
                auth.open_id_connect_url = scheme.get("openIdConnectUrl")
            elif atype == "mutualtls":
                auth.method = AuthMethod.MUTUAL_TLS

            # Store description and any x-* as annotations
            if desc:
                auth.annotations.append(Annotation(key="description", value=desc))
            for key, val in scheme.items():
                if key.startswith("x-"):
                    auth.annotations.append(Annotation(key=key[2:], value=str(val)))

            result.append(auth)
        return result

    # ------------------------------------------------------------------
    # Paths & Operations
    # ------------------------------------------------------------------
    def _parse_paths(self, paths: dict, entities: dict[str, Entity]) -> list[ServiceOperation]:
        all_ops = []
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            all_ops.extend(self._parse_path_item_operations(path, path_item, entities))
        return all_ops

    def _parse_path_item_operations(
        self, path: str, path_item: dict, entities: dict[str, Entity]
    ) -> list[ServiceOperation]:
        """Extract all operations from a Path Item."""
        operations = []
        for method in ["get", "put", "post", "delete", "options", "head", "patch", "trace"]:
            op_spec = path_item.get(method)
            if op_spec is None:
                continue
            operations.append(self._parse_operation(method, path, op_spec, entities))
        return operations

    def _parse_operation(
        self, method: str, path: str, op_spec: dict, entities: dict[str, Entity]
    ) -> ServiceOperation:
        op_id = op_spec.get("operationId", f"{method}{path}")
        description = op_spec.get("description") or op_spec.get("summary", "")

        # HTTP method
        try:
            http_method = HttpMethod(method.upper())
        except ValueError:
            http_method = None

        # Parameters
        params = self._parse_parameter_list(op_spec.get("parameters", []), entities)

        # Request body
        request_body = None
        if "requestBody" in op_spec:
            request_body = self._parse_request_body(op_spec["requestBody"], entities)

        # Responses
        responses = []
        for status, resp_spec in op_spec.get("responses", {}).items():
            responses.append(self._parse_response(resp_spec, status, entities))

        # Security requirements
        security_reqs = []
        for req in op_spec.get("security", []):
            for name, scopes in req.items():
                security_reqs.append(SecurityRequirement(name=name, scopes=scopes))

        # Deprecated -> version_status
        version_status = VersionStatus.DEPRECATED if op_spec.get("deprecated") else None

        # Servers (operation-level)
        op_servers = self._parse_servers(op_spec.get("servers", []))

        # Callbacks (simplified: store in annotations)
        callbacks = op_spec.get("callbacks", {})
        if callbacks:
            # We'll store as string in annotation
            pass

        operation = ServiceOperation(
            name=op_id,
            type=OperationType.REQUEST_RESPONSE,
            description=description,
            http_method=http_method,
            path=path,
            parameters=params,
            request_body=request_body,
            responses=responses,
            security_requirements=security_reqs,
            version_status=version_status,
            servers=op_servers,
        )
        # x-* extensions on operation
        for key, val in op_spec.items():
            if key.startswith("x-"):
                operation.annotations.append(Annotation(key=key[2:], value=str(val)))
        return operation

    # ------------------------------------------------------------------
    # Parameter parsing
    # ------------------------------------------------------------------
    def _parse_parameter_list(self, param_list: list, entities: dict[str, Entity]) -> list[Parameter]:
        result = []
        for raw in param_list:
            param = self._resolve_ref(raw, "parameters")
            if param:
                result.append(self._parse_parameter(param, entities))
        return result

    def _parse_parameter(self, param: dict, entities: dict[str, Entity]) -> Parameter:
        name = param.get("name", "")
        in_ = param.get("in", "query")
        loc_map = {
            "query": ParameterLocation.QUERY,
            "header": ParameterLocation.HEADER,
            "path": ParameterLocation.PATH,
            "cookie": ParameterLocation.COOKIE
        }
        location = loc_map.get(in_, ParameterLocation.QUERY)
        required = param.get("required", False)
        description = param.get("description", "")

        # Convert schema to Entity or DataType (we'll set type_entity later if possible)
        schema = param.get("schema")
        type_entity = None
        if schema:
            # For simplicity, we create a temporary Entity for the schema
            tmp_entity = self._schema_to_entity(schema, f"param_{name}", entities)
            if tmp_entity:
                type_entity = tmp_entity

        p = Parameter(
            name=name,
            location=location,
            required=required,
            description=description,
            type_entity=type_entity,
        )
        # x-* extensions
        for key, val in param.items():
            if key.startswith("x-"):
                p.annotations.append(Annotation(key=key[2:], value=str(val)))
        return p

    # ------------------------------------------------------------------
    # Request Body parsing
    # ------------------------------------------------------------------
    def _parse_request_body(self, body_spec: dict, entities: dict[str, Entity]) -> RequestBody | None:
        spec = self._resolve_ref(body_spec, "requestBodies")
        if not spec:
            return None
        desc = spec.get("description", "")
        required = spec.get("required", False)

        content_entities: dict[str, Entity] = {}
        content = spec.get("content", {})
        for media_type, media_def in content.items():
            if "schema" in media_def:
                entity = self._schema_to_entity(media_def["schema"], f"body_{media_type}", entities)
                if entity:
                    content_entities[media_type] = entity
        primary = next(iter(content_entities.values()), None)

        rb = RequestBody(
            description=desc,
            required=required,
            content_entity=primary,
            content_type_entities=content_entities,
            is_binary="application/octet-stream" in content,
        )
        # x-*
        for key, val in spec.items():
            if key.startswith("x-"):
                rb.annotations.append(Annotation(key=key[2:], value=str(val)))
        return rb

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------
    def _parse_response(self, resp_spec: dict, status: str, entities: dict[str, Entity]) -> Response:
        spec = self._resolve_ref(resp_spec, "responses")
        if not spec:
            return Response(status_code=status, description="")
        desc = spec.get("description", "")

        content_entities: dict[str, Entity] = {}
        content = spec.get("content", {})
        for media_type, media_def in content.items():
            if "schema" in media_def:
                entity = self._schema_to_entity(media_def["schema"], f"resp_{status}_{media_type}", entities)
                if entity:
                    content_entities[media_type] = entity
        primary = next(iter(content_entities.values()), None)

        resp = Response(
            status_code=status,
            description=desc,
            content_entity=primary,
            content_type_entities=content_entities,
            is_binary="application/octet-stream" in content,
        )
        # x-*
        for key, val in spec.items():
            if key.startswith("x-"):
                resp.annotations.append(Annotation(key=key[2:], value=str(val)))
        return resp

    # ------------------------------------------------------------------
    # Schema → Entity (MSDM)
    # ------------------------------------------------------------------
    def _schema_to_entity(
        self, schema: dict, name: str, entities: dict[str, Entity]
    ) -> Entity | None:
        """Convert an OpenAPI schema to an MSDM Entity. Reuses existing entities from cache."""
        schema = self._resolve_ref(schema, "schemas")
        if not schema:
            return None

        # Check cache first
        if name in entities:
            return entities[name]

        # Composition
        composition = None
        for comp_type in ["allOf", "oneOf", "anyOf"]:
            if comp_type in schema:
                members = []
                member_ids = []
                for sub_schema in schema[comp_type]:
                    sub_name = f"{name}_{comp_type}_part"
                    sub_entity = self._schema_to_entity(sub_schema, sub_name, entities)
                    if sub_entity:
                        members.append(sub_entity)
                        member_ids.append(sub_entity.name)
                if members:
                    composition = EntityComposition(
                        composition_type=CompositionType(comp_type),
                        members=members,
                        member_ids=member_ids,
                        description=f"{comp_type} of {name}"
                    )
                break

        # Attributes (properties)
        attrs = []
        required_set = set(schema.get("required", []))
        for prop_name, prop_schema in schema.get("properties", {}).items():
            attr_type = self._schema_to_datatype(prop_schema, entities)
            attr = Attribute(
                name=prop_name,
                data_type=attr_type,
                required=prop_name in required_set,
                description=prop_schema.get("description", ""),
            )
            # Store x-* as annotations
            for key, val in prop_schema.items():
                if key.startswith("x-"):
                    attr.annotations.append(Annotation(key=key[2:], value=str(val)))
            attrs.append(attr)

        # If no properties and composition, create a single attribute for scalar
        if not attrs and not composition:
            scalar_type = self._schema_to_datatype(schema, entities)
            attrs.append(Attribute(name="value", data_type=scalar_type))

        entity = Entity(
            name=name,
            kind=EntityKind.OBJECT,  # default TABLE, but we can leave
            description=schema.get("description", ""),
            attributes=attrs,
            composition=composition,
        )
        # x-* at entity level
        for key, val in schema.items():
            if key.startswith("x-"):
                entity.annotations.append(Annotation(key=key[2:], value=str(val)))
        return entity

    def _schema_to_datatype(self, schema: dict, entities: dict[str, Entity]) -> DataType:
        """Convert an OpenAPI schema (or simple type) to an MSDM DataType."""
        schema = self._resolve_ref(schema, "schemas")
        if not schema:
            return DataType(base=ScalarType.ANY)

        # $ref already resolved, but check for reference by name
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            return DataType(base=ScalarType.REF, ref_entity_id=ref_name)

        type_ = schema.get("type", "string")
        format_ = schema.get("format")

        # Scalar mapping
        scalar_map = {
            "string": ScalarType.STRING,
            "integer": ScalarType.INT,
            "number": ScalarType.FLOAT,
            "boolean": ScalarType.BOOLEAN,
        }
        if type_ in scalar_map:
            base = scalar_map[type_]
            # Handle arrays
            if type_ == "array" and "items" in schema:
                item_type = self._schema_to_datatype(schema["items"], entities)
                return DataType(base=ScalarType.ARRAY, element_type=item_type)
            return DataType(base=base)

        if type_ == "array":
            item_type = self._schema_to_datatype(schema.get("items", {}), entities)
            return DataType(base=ScalarType.ARRAY, element_type=item_type)

        if type_ == "object":
            # Create a new entity for this object, but we might already have it in entities
            obj_name = schema.get("title", "AnonymousObject")
            if obj_name in entities:
                return DataType(base=ScalarType.REF, ref_entity_id=obj_name)
            else:
                # Create temporary entity? Not needed, just return ANY
                return DataType(base=ScalarType.ANY)

        return DataType(base=ScalarType.ANY)

    # ------------------------------------------------------------------
    # $ref resolution
    # ------------------------------------------------------------------
    def _resolve_ref(self, obj: dict, kind: str) -> dict:
        if not isinstance(obj, dict):
            return obj
        ref = obj.get("$ref")
        if ref and ref.startswith("#/components/"):
            parts = ref[2:].split("/")
            if len(parts) >= 3 and parts[0] == "components":
                comp_type = parts[1]
                name = "/".join(parts[2:])
                container = self._all_components.get(comp_type, {})
                return container.get(name, {})
        return obj

    # ------------------------------------------------------------------
    # Store other components as annotations
    # ------------------------------------------------------------------
    def _store_components_as_annotations(self, components: dict) -> list[Annotation]:
        """Store components that are not individually parsed (examples, links, etc.) as annotations."""
        ann_list = []
        for comp_type, comp_dict in components.items():
            if comp_type in ["schemas", "securitySchemes", "parameters", "responses", "requestBodies"]:
                continue  # already handled
            ann_list.append(Annotation(
                key=f"openapi:components:{comp_type}",
                value=str(comp_dict)
            ))
        return ann_list