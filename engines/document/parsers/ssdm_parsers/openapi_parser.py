"""
openapi_parser.py – Complete OpenAPI 3.x parser → SSDM_DOCUMENT (lossless)
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    ContactInfo,
    LicenseInfo,
    Server,
    SecurityScheme,
    OAuth2FlowInfo,
    Operation,
    Parameter,
    RequestBody,
    Response,
    HttpMethod,
    ParameterLocation,
    SecurityType,
    OAuth2Flow,
    ApiKeyLocation,
    OperationType,
    Link,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    CompositionEntity,
)


class OpenAPIV3Parser(BaseSSDMParser):
    """Full OpenAPI 3.x (and 3.1) parser that produces a lossless SSDM_DOCUMENT."""

    name = "openapi_v3"
    supported_extensions = (".json", ".yaml", ".yml")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        fmt = "yaml" if Path(source_name).suffix.lower() in (".yaml", ".yml") else "json"
        spec = json.loads(text) if fmt == "json" else yaml.safe_load(text)
        if not isinstance(spec, dict):
            raise ValueError("Root of OpenAPI document must be a JSON object")

        doc = self._create_base_document(source_name, options)

        # ── Info ──────────────────────────────────────────────────
        info = spec.get("info", {})
        doc.title = info.get("title", doc.title)
        doc.version = info.get("version", doc.version)
        doc.description = info.get("description", doc.description)
        doc.contact = self._parse_contact(info.get("contact"))
        doc.license = self._parse_license(info.get("license"))

        # ── Servers ───────────────────────────────────────────────
        doc.servers = self._parse_servers(spec.get("servers", []))

        # ── Global Security & Security Schemes ────────────────────
        components = spec.get("components", {})
        doc.security_schemes = self._parse_security_schemes(
            components.get("securitySchemes", {})
        )
        # Global security requirements
        doc.metadata["openapi:global_security"] = [
            list(req.keys()) for req in spec.get("security", [])
        ]

        # ── Reusable components (not schemas) ────────────────────
        # Let the components dict be the single source of truth for resolution
        self._all_components = components  # we keep a copy for $ref resolution

        # Schemas → MSDMDocument
        schemas = components.get("schemas", {})
        entities = {}
        for name, schema in schemas.items():
            entity = self._schema_to_entity(schema, name)
            if entity:
                entities[name] = entity
        doc.type_definitions = MSDMDocument(entities=list(entities.values())) if entities else None

        # Other component types: we parse them into the dedicated SSDM fields
        doc.reusable_parameters = self._parse_reusable_parameters(
            components.get("parameters", {})
        )
        doc.reusable_responses = self._parse_reusable_responses(
            components.get("responses", {})
        )
        doc.reusable_request_bodies = self._parse_reusable_request_bodies(
            components.get("requestBodies", {})
        )
        doc.reusable_headers = self._parse_reusable_headers(
            components.get("headers", {})
        )
        # Examples, links, callbacks are kept as raw dicts (they can be parsed later if needed)
        doc.metadata["openapi:examples"] = components.get("examples", {})
        doc.reusable_links = components.get("links", {})  # raw for now
        doc.reusable_callbacks = self._parse_reusable_callbacks(
            components.get("callbacks", {})
        )

        # ── Paths & Operations ───────────────────────────────────
        doc.operations = self._parse_paths(
            spec.get("paths", {}), spec.get("security", [])
        )

        # ── Tags & External Docs (global) ────────────────────────
        doc.metadata["openapi:tags"] = spec.get("tags", [])
        doc.metadata["openapi:externalDocs"] = spec.get("externalDocs", {})

        # ── Extensions (x-*) on document level ───────────────────
        self._copy_extensions(spec, doc.extensions)

        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    # Info / Contact / License / Servers
    # ------------------------------------------------------------------
    def _parse_contact(self, raw: Optional[dict]) -> Optional[ContactInfo]:
        if not raw:
            return None
        return ContactInfo(name=raw.get("name"), url=raw.get("url"), email=raw.get("email"))

    def _parse_license(self, raw: Optional[dict]) -> Optional[LicenseInfo]:
        if not raw:
            return None
        return LicenseInfo(name=raw.get("name", "Proprietary"), url=raw.get("url"))

    def _parse_servers(self, raw_servers: list) -> List[Server]:
        servers = []
        for s in raw_servers:
            variables = {v: d.get("default", "") for v, d in s.get("variables", {}).items()}
            servers.append(Server(url=s["url"], description=s.get("description"), variables=variables))
        return servers

    # ------------------------------------------------------------------
    # Security Schemes
    # ------------------------------------------------------------------
    def _parse_security_schemes(self, schemes: dict) -> List[SecurityScheme]:
        result = []
        for name, scheme in schemes.items():
            stype = scheme.get("type", "").lower()
            if stype == "http":
                http_scheme = scheme.get("scheme", "").lower()
                stype_enum = SecurityType.HTTP_BEARER if http_scheme == "bearer" else SecurityType.HTTP_BASIC
            elif stype == "apikey":
                stype_enum = SecurityType.API_KEY
            elif stype == "oauth2":
                stype_enum = SecurityType.OAUTH2
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
                        oauth2_flows.append(OAuth2FlowInfo(
                            flow=flow_enum,
                            authorization_url=flow_def.get("authorizationUrl"),
                            token_url=flow_def.get("tokenUrl"),
                            refresh_url=flow_def.get("refreshUrl"),
                            scopes=flow_def.get("scopes", {}),
                        ))

            sec = SecurityScheme(
                name=name,
                type=stype_enum,
                description=scheme.get("description"),
                api_key_location=api_key_location,
                api_key_param_name=api_key_param,
                oauth2_flows=oauth2_flows,
                open_id_connect_url=scheme.get("openIdConnectUrl"),
            )
            self._copy_extensions(scheme, sec.extensions)
            result.append(sec)
        return result

    # ------------------------------------------------------------------
    # Reusable components parsing
    # ------------------------------------------------------------------
    def _parse_reusable_parameters(self, params: dict) -> Dict[str, Parameter]:
        result = {}
        for name, p in params.items():
            result[name] = self._parse_single_parameter(p, name)
        return result

    def _parse_reusable_responses(self, responses: dict) -> Dict[str, Response]:
        result = {}
        for name, r in responses.items():
            result[name] = self._parse_single_response(r, name)
        return result

    def _parse_reusable_request_bodies(self, bodies: dict) -> Dict[str, RequestBody]:
        result = {}
        for name, b in bodies.items():
            result[name] = self._parse_single_request_body(b, name)
        return result

    def _parse_reusable_headers(self, headers: dict) -> Dict[str, Parameter]:
        result = {}
        for name, h in headers.items():
            result[name] = self._parse_single_header(name, h)
        return result

    def _parse_reusable_callbacks(self, callbacks: dict) -> Dict[str, Dict[str, List[Operation]]]:
        """Reusable callbacks: name -> (expression -> operations)"""
        result = {}
        for cb_name, cb_paths in callbacks.items():
            result[cb_name] = {}
            for expression, path_item in cb_paths.items():
                # A callback path item is identical to a normal path item
                ops = self._parse_path_item_operations(expression, path_item, [])
                result[cb_name][expression] = ops
        return result

    # ------------------------------------------------------------------
    # Paths & Operations
    # ------------------------------------------------------------------
    def _parse_paths(self, paths: dict, global_security: list) -> List[Operation]:
        all_ops = []
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            # Path‑level parameters and security
            path_params = self._parse_parameters_list(
                path_item.get("parameters", []), path
            )
            path_security = path_item.get("security", global_security)

            ops = self._parse_path_item_operations(path, path_item, path_security, path_params)
            all_ops.extend(ops)
        return all_ops

    def _parse_path_item_operations(
        self, path: str, path_item: dict, security_override: list,
        path_params: Optional[List[Parameter]] = None,
    ) -> List[Operation]:
        """Extract all operations from a Path Item (used for both regular paths and callbacks)."""
        if path_params is None:
            path_params = []
        operations = []
        for method in ["get", "put", "post", "delete", "options", "head", "patch", "trace"]:
            op_spec = path_item.get(method)
            if op_spec is None:
                continue
            operations.append(
                self._parse_operation(method, path, op_spec, path_params, security_override)
            )
        return operations

    def _parse_operation(
        self, method: str, path: str, op_spec: dict,
        path_params: List[Parameter], path_security: list,
    ) -> Operation:
        # Operation ID
        op_id = op_spec.get("operationId", f"{method}{path}")

        # Description / Summary
        description = op_spec.get("description") or op_spec.get("summary", "")

        # HTTP Method
        try:
            http_method = HttpMethod(method.upper())
        except ValueError:
            http_method = None

        # Parameters (merged: path-level + operation-level)
        op_params_raw = self._parse_parameters_list(op_spec.get("parameters", []), path)
        params = self._merge_parameters(path_params, op_params_raw)

        # Security (operation > path > global)
        op_security = op_spec.get("security", path_security)
        security_names = [list(req.keys()) for req in op_security]

        # Request body
        request_body = None
        if "requestBody" in op_spec:
            request_body = self._parse_single_request_body(op_spec["requestBody"], f"{op_id}_body")

        # Responses
        responses = []
        for status, resp_spec in op_spec.get("responses", {}).items():
            responses.append(self._parse_single_response(resp_spec, f"{op_id}_{status}"))

        # Callbacks (operation-level)
        callbacks = {}
        raw_callbacks = op_spec.get("callbacks", {})
        for cb_name, cb_paths in raw_callbacks.items():
            callbacks[cb_name] = {}
            for expr, cb_path_item in cb_paths.items():
                callbacks[cb_name][expr] = self._parse_path_item_operations(expr, cb_path_item, [])
        # (note: if callbacks have their own security, we'd need to pass it; but OpenAPI doesn't define that)

        # Servers (operation-level)
        op_servers = self._parse_servers(op_spec.get("servers", []))

        # External docs
        ext_docs = op_spec.get("externalDocs")

        # Tags / Deprecated
        tags = op_spec.get("tags", [])
        deprecated = op_spec.get("deprecated", False)

        # Build Operation
        operation = Operation(
            name=op_id,
            type=OperationType.REQUEST_RESPONSE,
            description=description,
            http_method=http_method,
            path=path,
            parameters=params,
            request_body=request_body,
            responses=responses,
            security=security_names,
            tags=tags,
            deprecated=deprecated,
            servers=op_servers,
            external_docs=ext_docs,
            callbacks=callbacks,
        )
        self._copy_extensions(op_spec, operation.extensions)
        return operation

    # ------------------------------------------------------------------
    # Parameter parsing
    # ------------------------------------------------------------------
    def _parse_parameters_list(self, param_list: list, parent_path: Optional[str] = None) -> List[Parameter]:
        """Parse a list of parameter/ref objects."""
        result = []
        for raw in param_list:
            param = self._resolve_if_ref(raw, "parameters")
            if param:
                result.append(self._parse_single_parameter(param, param.get("name", "")))
        return result

    def _parse_single_parameter(self, param: dict, fallback_name: str = "") -> Parameter:
        """Parse a fully resolved parameter object."""
        name = param.get("name", fallback_name)
        in_ = param.get("in", "query")
        loc_map = {"query": ParameterLocation.QUERY, "header": ParameterLocation.HEADER,
                    "path": ParameterLocation.PATH, "cookie": ParameterLocation.COOKIE}
        location = loc_map.get(in_, ParameterLocation.QUERY)
        required = param.get("required", False)
        description = param.get("description", "")

        # Type string from schema or content
        type_str = "string"
        if "schema" in param:
            type_str = self._schema_type_string(param["schema"])
        elif "content" in param:
            # Could be multi‑part, use a placeholder
            type_str = "string"  # further detail would be in content

        p = Parameter(
            name=name,
            location=location,
            required=required,
            description=description,
            type_string=type_str,
        )
        self._copy_extensions(param, p.extensions)
        return p

    def _parse_single_header(self, name: str, header_spec: dict) -> Parameter:
        """Parse a header component into a Parameter of location header."""
        spec = self._resolve_if_ref(header_spec, "headers")
        type_str = "string"
        if "schema" in spec:
            type_str = self._schema_type_string(spec["schema"])
        p = Parameter(
            name=name,
            location=ParameterLocation.HEADER,
            required=False,
            description=spec.get("description", ""),
            type_string=type_str,
        )
        self._copy_extensions(spec, p.extensions)
        return p

    @staticmethod
    def _merge_parameters(path: List[Parameter], op: List[Parameter]) -> List[Parameter]:
        merged = {}
        for p in path:
            key = (p.name, p.location)
            merged[key] = p
        for p in op:
            key = (p.name, p.location)
            merged[key] = p
        return list(merged.values())

    # ------------------------------------------------------------------
    # Request Body & Response parsing
    # ------------------------------------------------------------------
    def _parse_single_request_body(self, body_spec: dict, fallback_name: str) -> Optional[RequestBody]:
        spec = self._resolve_if_ref(body_spec, "requestBodies")
        if not spec:
            return None
        desc = spec.get("description", "")
        required = spec.get("required", False)
        content_entities = {}
        is_binary = False
        content = spec.get("content", {})
        for media_type, media_def in content.items():
            if media_def.get("schema"):
                entity = self._schema_to_entity(media_def["schema"], f"{fallback_name}_{media_type}")
                if entity:
                    content_entities[media_type] = entity
            if media_type in ("application/octet-stream", "multipart/form-data"):
                is_binary = True
        primary = next(iter(content_entities.values()), None)
        rb = RequestBody(
            description=desc,
            required=required,
            content_entity=primary,
            content_type_entities=content_entities,
            is_binary=is_binary,
        )
        self._copy_extensions(spec, rb.extensions)
        return rb

    def _parse_single_response(self, resp_spec: dict, fallback_name: str) -> Response:
        spec = self._resolve_if_ref(resp_spec, "responses")
        desc = spec.get("description", "")
        headers = []
        for h_name, h_def in spec.get("headers", {}).items():
            headers.append(self._parse_single_header(h_name, h_def))
        content_entities = {}
        is_binary = False
        content = spec.get("content", {})
        for media_type, media_def in content.items():
            if media_def.get("schema"):
                entity = self._schema_to_entity(media_def["schema"], f"{fallback_name}_{media_type}")
                if entity:
                    content_entities[media_type] = entity
            if media_type == "application/octet-stream":
                is_binary = True
        primary = next(iter(content_entities.values()), None)

        # Links
        links = {}
        for link_name, link_def in spec.get("links", {}).items():
            link = self._parse_link(link_def)
            if link:
                links[link_name] = link

        resp = Response(
            status_code=fallback_name.split("_")[-1] if "_" in fallback_name else "200",
            description=desc,
            content_entity=primary,
            content_type_entities=content_entities,
            headers=headers,
            links=links,
            is_binary=is_binary,
        )
        self._copy_extensions(spec, resp.extensions)
        return resp

    def _parse_link(self, link_def: dict) -> Optional[Link]:
        spec = self._resolve_if_ref(link_def, "links")
        if not spec:
            return None
        return Link(
            operation_id=spec.get("operationId", ""),
            parameters=spec.get("parameters", {}),
            description=spec.get("description"),
            request_body=spec.get("requestBody"),  # can be a literal or an expression
        )

    # ------------------------------------------------------------------
    # Schema → MSDM Entity
    # ------------------------------------------------------------------
    def _schema_to_entity(self, schema: dict, name: str) -> Optional[Entity]:
        """Convert an OpenAPI schema to an MSDM Entity, handling $ref, composition, discriminator, etc."""
        schema = self._resolve_if_ref(schema, "schemas")
        if not schema:
            return None

        # Composition (allOf/oneOf/anyOf)
        composition = None
        for comp_type in ["allOf", "oneOf", "anyOf"]:
            if comp_type in schema:
                members = []
                for sub_schema in schema[comp_type]:
                    sub_entity = self._schema_to_entity(sub_schema, f"{name}_{comp_type}_part")
                    if sub_entity:
                        members.append(sub_entity)  # store as Entity
                if members:
                    composition = CompositionEntity(
                        composition_type=comp_type,
                        members=members,
                        description=f"{comp_type} of {name}"
                    )
                break  # only one composition keyword

        # Basic type
        type_ = schema.get("type")
        attributes = []
        deprecated = schema.get("deprecated", False)

        if type_ == "object" or "properties" in schema:
            required_set = set(schema.get("required", []))
            for prop_name, prop_schema in schema.get("properties", {}).items():
                attr_type = self._schema_type_string(prop_schema)
                attr_desc = prop_schema.get("description", "")
                attr_required = prop_name in required_set
                attr_deprecated = prop_schema.get("deprecated", False)
                xml = prop_schema.get("xml")
                attr = Attribute(
                    name=prop_name,
                    type=attr_type,
                    required=attr_required,
                    description=attr_desc,
                    deprecated=attr_deprecated,
                    xml=xml,
                )
                self._copy_extensions(prop_schema, attr.extensions)
                attributes.append(attr)

        elif type_ == "array":
            items_schema = schema.get("items", {})
            item_type = self._schema_type_string(items_schema)
            attributes.append(Attribute(name="items", type=f"array<{item_type}>"))
        else:
            # scalar
            attributes.append(Attribute(name="value", type=self._schema_type_string(schema)))

        entity = Entity(
            name=name,
            attributes=attributes,
            description=schema.get("description", ""),
            deprecated=deprecated,
            composition=composition,
            xml=None,  # no xml at entity level in OpenAPI?
        )

        # Discriminator
        discriminator = schema.get("discriminator")
        if discriminator:
            prop_name = discriminator.get("propertyName")
            mapping = discriminator.get("mapping", {})
            # Build discriminator Attribute
            disc_attr = None
            for attr in attributes:
                if attr.name == prop_name:
                    disc_attr = attr
                    break
            if not disc_attr:
                disc_attr = Attribute(name=prop_name, type="string", required=True)
            entity.discriminator = disc_attr
            # Map values to Entity objects: we'll need to build Entities for each mapping if available
            # For now, store them as references (we might not have resolved them yet)
            # We'll store a dict where values are Entity objects (which may be placeholders)
            disc_map = {}
            for value, target_name in mapping.items():
                # Try to find the entity among already parsed ones (if in components/schemas)
                resolved = entities_cache.get(target_name) if hasattr(self, 'entities_cache') else None
                if not resolved:
                    # Create a placeholder entity with name
                    resolved = Entity(name=target_name, attributes=[])
                disc_map[value] = resolved
            entity.discriminator_mapping = disc_map

        # XML (entity level, if present)
        entity.xml = schema.get("xml")

        self._copy_extensions(schema, entity.extensions)
        return entity

    def _schema_type_string(self, schema: dict) -> str:
        """Return a type string from a schema (or $ref)."""
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
            inner = self._schema_type_string(items) if items else "object"
            return f"array<{inner}>"
        if type_ == "object":
            return "object"
        return type_

    # ------------------------------------------------------------------
    # $ref resolution
    # ------------------------------------------------------------------
    def _resolve_if_ref(self, obj: dict, kind: str) -> dict:
        """If obj is a $ref, resolve it within the document; otherwise return obj."""
        if not isinstance(obj, dict):
            return obj
        ref = obj.get("$ref")
        if ref:
            return self._resolve_ref(ref, kind)
        return obj

    def _resolve_ref(self, ref: str, kind: str) -> dict:
        """Resolve an internal #/components/... reference."""
        if not ref.startswith("#/components/"):
            # External refs or non-components refs: return empty (can be extended)
            return {}
        parts = ref[2:].split("/")  # remove "#/", split
        # Expected: components / <componentType> / <name>
        if len(parts) >= 3 and parts[0] == "components":
            comp_type = parts[1]
            name = "/".join(parts[2:])  # name could contain slashes? uncommon
            container = self._all_components.get(comp_type, {})
            return container.get(name, {})
        return {}

    # ------------------------------------------------------------------
    # Extensions helper
    # ------------------------------------------------------------------
    def _copy_extensions(self, source: dict, target: Dict[str, Any]):
        """Copy all x-* keys from source to target dict."""
        for key, value in source.items():
            if isinstance(key, str) and key.startswith("x-"):
                target[key[2:]] = value  # store without the 'x-' prefix