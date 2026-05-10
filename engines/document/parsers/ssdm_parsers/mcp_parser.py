# engines/document/parsers/ssdm_parsers/mcp_parser.py
"""
mcp_parser.py – MCP (Model Context Protocol) server definition parser → SSDMDocument
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from ...models.media_types import MEDIA_TYPES
from ...models.msdm_models import (
    Annotation, Attribute, DataType, Entity, EntityKind, MSDMDocument, ScalarType, VersionStatus
)
from ...models.ssdm_models import (
    AuthConfig, AuthMethod, CoordinationProtocol, InternalComponentType,
    InternalServiceBinding, MCPNorthBoundBinding, MCPPromptBinding,
    MCPResourceBinding, MCPToolBinding, ServiceOperation, OperationType,
    Parameter, ParameterLocation, ParameterMapping, RequestBody,
    ResponseMapping, RetryPolicy, SecurityRequirement, SSDMDocument, Transport
)
from ..base import ParseOptions
from .base_ssdm_parser import BaseSSDMParser


class MCPParser(BaseSSDMParser):
    """
    Parses an MCP server definition (JSON/YAML) into SSDMDocument.
    Supports both stdio and SSE transports.
    """

    name = "mcp"
    supported_extensions = (".json", ".yaml", ".yml")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument:
        text = data.decode(options.encoding)
        fmt = "yaml" if Path(source_name).suffix.lower() in (".yaml", ".yml") else "json"
        if fmt == "json":
            spec = json.loads(text)
        else:
            import yaml
            spec = yaml.safe_load(text)

        if not isinstance(spec, dict):
            raise ValueError("MCP definition must be a JSON object")

        doc = SSDMDocument(
            document_id=source_name,  # will be overwritten by caller
            title=spec.get("server_name", Path(source_name).stem),
            version=spec.get("version", "1.0.0"),
            media_type=MEDIA_TYPES.get("mcp", MEDIA_TYPES["txt"]),
            description=spec.get("description", ""),
            servers=[],
            security_schemes=[],
            operations=[],
        )

        # Parse MCP North‑bound binding and store in metadata
        mcp_binding = self._parse_mcp_binding(spec)
        doc.metadata["mcp"] = {
            "binding": mcp_binding,
            "server_name": spec.get("server_name", ""),
            "version": spec.get("version", "1.0.0"),
        }

        # Generate operations for each tool, resource, prompt
        operations = []
        operations.extend(self._tools_to_operations(mcp_binding.tools, spec.get("tools", [])))
        operations.extend(self._resources_to_operations(mcp_binding.resources, spec.get("resources", [])))
        operations.extend(self._prompts_to_operations(mcp_binding.prompts, spec.get("prompts", [])))
        doc.operations = operations

        doc.is_valid = True
        return doc

    # ------------------------------------------------------------------
    #  MCP binding assembly
    # ------------------------------------------------------------------
    def _parse_mcp_binding(self, spec: dict) -> MCPNorthBoundBinding:
        transport_str = spec.get("transport", "stdio")
        try:
            transport = Transport(transport_str.upper())
        except ValueError:
            transport = Transport.STDIO

        server_auth = self._parse_auth(spec.get("server_auth"))

        tools = [self._parse_tool_binding(t) for t in spec.get("tools", [])]
        resources = [self._parse_resource_binding(r) for r in spec.get("resources", [])]
        prompts = [self._parse_prompt_binding(p) for p in spec.get("prompts", [])]

        return MCPNorthBoundBinding(
            server_name=spec.get("server_name", ""),
            transport=transport,
            server_url=spec.get("server_url"),
            # command field removed because it does not exist in the model
            tools=tools,
            resources=resources,
            prompts=prompts,
            server_auth=server_auth,
        )

    # ------------------------------------------------------------------
    #  Auth config
    # ------------------------------------------------------------------
    def _parse_auth(self, auth_spec: dict | None) -> AuthConfig | None:
        if not auth_spec:
            return None
        method_str = auth_spec.get("method", "none")
        try:
            method = AuthMethod(method_str)
        except ValueError:
            method = AuthMethod.NONE

        return AuthConfig(
            method=method,
            value=auth_spec.get("value"),
            param_name=auth_spec.get("param_name"),
            location=auth_spec.get("location"),
            oauth2_token_url=auth_spec.get("oauth2_token_url"),
            oauth2_client_id=auth_spec.get("oauth2_client_id"),
        )

    # ------------------------------------------------------------------
    #  Internal service binding (common)
    # ------------------------------------------------------------------
    def _parse_internal_binding(self, spec: dict | None) -> InternalServiceBinding:
        if not spec:
            # Return a default fallback
            return InternalServiceBinding(
                component_type=InternalComponentType.TOOL,
                coordination=CoordinationProtocol.DIRECT_CALL,
                address="",
                timeout_ms=30000,
                retry_policy=RetryPolicy.NONE,
                max_retries=3,
                config={},
                parameter_mappings=[],
                response_mappings=[],
                internal_auth=None,
            )
        comp_type_str = spec.get("component_type", "tool")
        try:
            comp_type = InternalComponentType(comp_type_str)
        except ValueError:
            comp_type = InternalComponentType.TOOL

        coord_str = spec.get("coordination", "directCall")
        try:
            coord = CoordinationProtocol(coord_str)
        except ValueError:
            coord = CoordinationProtocol.DIRECT_CALL

        param_mappings = [
            ParameterMapping(source=m["source"], target=m["target"], transform=m.get("transform"))
            for m in spec.get("parameter_mappings", [])
        ]
        resp_mappings = [
            ResponseMapping(source=m["source"], target=m["target"], transform=m.get("transform"))
            for m in spec.get("response_mappings", [])
        ]

        internal_auth = self._parse_auth(spec.get("internal_auth"))

        return InternalServiceBinding(
            component_type=comp_type,
            coordination=coord,
            address=spec.get("address", ""),
            timeout_ms=spec.get("timeout_ms", 30000),
            retry_policy=RetryPolicy(spec.get("retry_policy", "none")),
            max_retries=spec.get("max_retries", 3),
            config=spec.get("config", {}),
            parameter_mappings=param_mappings,
            response_mappings=resp_mappings,
            internal_auth=internal_auth,
        )

    # ------------------------------------------------------------------
    #  Tool binding
    # ------------------------------------------------------------------
    def _parse_tool_binding(self, tool_spec: dict) -> MCPToolBinding:
        internal = self._parse_internal_binding(tool_spec.get("internal_service_binding"))
        return MCPToolBinding(
            tool_name=tool_spec["name"],
            internal=internal,
        )

    # ------------------------------------------------------------------
    #  Resource binding
    # ------------------------------------------------------------------
    def _parse_resource_binding(self, res_spec: dict) -> MCPResourceBinding:
        internal = self._parse_internal_binding(res_spec.get("internal_service_binding"))
        return MCPResourceBinding(
            uri=res_spec["uri"],
            internal=internal,
        )

    # ------------------------------------------------------------------
    #  Prompt binding
    # ------------------------------------------------------------------
    def _parse_prompt_binding(self, prompt_spec: dict) -> MCPPromptBinding:
        internal = self._parse_internal_binding(prompt_spec.get("internal_service_binding"))
        return MCPPromptBinding(
            prompt_name=prompt_spec["name"],
            internal=internal,
        )

    # ------------------------------------------------------------------
    #  Generate operations from tool definitions
    # ------------------------------------------------------------------
    def _tools_to_operations(self, tool_bindings: list, tool_specs: list) -> list[ServiceOperation]:
        ops = []
        for binding, spec in zip(tool_bindings, tool_specs):
            params_schema = spec.get("parameters", {})
            req_body = None
            if params_schema and params_schema.get("type") == "object":
                entity = self._json_schema_to_entity(params_schema, spec["name"] + "_input")
                if entity:
                    req_body = RequestBody(
                        description=f"Input for {spec['name']}",
                        required=True,
                        content_entity=entity,
                    )
            # Security requirements – empty list of SecurityRequirement
            security_reqs: list[SecurityRequirement] = []
            # Deprecation
            version_status = VersionStatus.DEPRECATED if spec.get("deprecated") else None

            operation = ServiceOperation(
                name=spec["name"],
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,
                path=f"mcp://{spec['name']}",
                parameters=[],
                request_body=req_body,
                responses=[],
                security_requirements=security_reqs,
                version_status=version_status,
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Generate operations from resources
    # ------------------------------------------------------------------
    def _resources_to_operations(self, resource_bindings: list, resource_specs: list) -> list[ServiceOperation]:
        ops = []
        for binding, spec in zip(resource_bindings, resource_specs):
            uri = spec["uri"]
            # Extract path parameters from URI pattern
            path_params = []
            for match in re.finditer(r"\{(\w+)\}", uri):
                param_name = match.group(1)
                param = Parameter(
                    name=param_name,
                    location=ParameterLocation.PATH,
                    description=f"URI parameter {param_name}",
                    type_entity=None,
                )
                param.annotations.append(Annotation(key="type", value="string"))
                path_params.append(param)

            version_status = VersionStatus.DEPRECATED if spec.get("deprecated") else None

            operation = ServiceOperation(
                name=f"get_resource_{spec.get('name', spec['uri'])}",
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,
                path=uri,
                parameters=path_params,
                request_body=None,
                responses=[],
                security_requirements=[],
                version_status=version_status,
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Generate operations from prompts
    # ------------------------------------------------------------------
    def _prompts_to_operations(self, prompt_bindings: list, prompt_specs: list) -> list[ServiceOperation]:
        ops = []
        for binding, spec in zip(prompt_bindings, prompt_specs):
            args = spec.get("arguments", [])
            params = []
            for arg in args:
                param = Parameter(
                    name=arg["name"],
                    location=ParameterLocation.BODY,
                    required=arg.get("required", False),
                    description=arg.get("description", ""),
                    type_entity=None,
                )
                param.annotations.append(Annotation(key="type", value="string"))
                params.append(param)

            version_status = VersionStatus.DEPRECATED if spec.get("deprecated") else None

            operation = ServiceOperation(
                name=spec["name"],
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,
                path=f"mcp://{spec['name']}",
                parameters=params,
                request_body=None,
                responses=[],
                security_requirements=[],
                version_status=version_status,
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Helper: JSON Schema → MSDM Entity
    # ------------------------------------------------------------------
    def _json_schema_to_entity(self, schema: dict, name: str) -> Entity | None:
        """
        Minimal JSON Schema to Entity conversion for MCP tool input objects.
        Only supports flat objects with primitive properties.
        """
        if not schema:
            return None
        if schema.get("type") != "object" or "properties" not in schema:
            return None
        required = set(schema.get("required", []))
        attrs = []
        for prop_name, prop_schema in schema["properties"].items():
            data_type = self._json_schema_to_datatype(prop_schema)
            attr = Attribute(
                name=prop_name,
                data_type=data_type,
                required=prop_name in required,
                description=prop_schema.get("description", ""),
            )
            # Store any extra info as annotations
            if "default" in prop_schema:
                attr.annotations.append(Annotation(key="default", value=str(prop_schema["default"])))
            attrs.append(attr)
        return Entity(name=name, kind=EntityKind.OBJECT, attributes=attrs)

    def _json_schema_to_datatype(self, schema: dict) -> DataType:
        """Convert a JSON Schema type to MSDM DataType."""
        t = schema.get("type", "string")
        if t == "array":
            items = schema.get("items", {})
            item_dt = self._json_schema_to_datatype(items)
            return DataType(base=ScalarType.ARRAY, element_type=item_dt)
        if t == "integer":
            return DataType(base=ScalarType.INT)
        if t == "number":
            return DataType(base=ScalarType.FLOAT)
        if t == "boolean":
            return DataType(base=ScalarType.BOOLEAN)
        if t == "object":
            return DataType(base=ScalarType.ANY)  # complex objects not fully supported
        return DataType(base=ScalarType.STRING)