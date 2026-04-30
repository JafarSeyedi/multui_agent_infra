"""
mcp_parser.py – MCP (Model Context Protocol) server definition parser → SSDM_DOCUMENT
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..base import ParseOptions
from ..ssdm_parsers.base_ssdm_parser import BaseSSDMParser
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    MCPNorthBoundBinding,
    MCPToolBinding,
    MCPResourceBinding,
    MCPPromptBinding,
    InternalServiceBinding,
    InternalComponentType,
    CoordinationProtocol,
    ParameterMapping,
    ResponseMapping,
    Parameter,
    RequestBody,
    Response,
    Operation,
    OperationType,
    ParameterLocation,
    AuthConfig,
    AuthMethod,
    Transport,
    RetryPolicy,
)
from ...models.msdm_models import MSDMDocument, Entity, Attribute


class MCPParser(BaseSSDMParser):
    """
    Parses an MCP server definition (JSON/YAML) into SSDM_DOCUMENT.
    Supports both stdio and SSE transports.
    """

    name = "mcp"
    supported_extensions = (".json", ".yaml", ".yml")

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        text = data.decode(options.encoding)
        fmt = "yaml" if Path(source_name).suffix.lower() in (".yaml", ".yml") else "json"
        if fmt == "json":
            spec = json.loads(text)
        else:
            import yaml
            spec = yaml.safe_load(text)

        if not isinstance(spec, dict):
            raise ValueError("MCP definition must be a JSON object")

        doc = SSDM_DOCUMENT(
            document_id="",  # will be filled by caller
            title=spec.get("server_name", Path(source_name).stem),
            version=spec.get("version", "1.0.0"),
            description=spec.get("description", ""),
            servers=[],  # MCP does not have servers in the same sense
            security_schemes=[],
            operations=[],
            mcp_binding=None,
            mib_module=None,
            type_definitions=None,
        )

        # Parse MCP North‑bound binding
        mcp_binding = self._parse_mcp_binding(spec)
        doc.mcp_binding = mcp_binding

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

        tools = []
        for t in spec.get("tools", []):
            tools.append(self._parse_tool_binding(t))

        resources = []
        for r in spec.get("resources", []):
            resources.append(self._parse_resource_binding(r))

        prompts = []
        for p in spec.get("prompts", []):
            prompts.append(self._parse_prompt_binding(p))

        return MCPNorthBoundBinding(
            server_name=spec.get("server_name", ""),
            transport=transport,
            server_url=spec.get("server_url"),
            command=spec.get("command"),
            tools=tools,
            resources=resources,
            prompts=prompts,
            server_auth=server_auth,
        )

    # ------------------------------------------------------------------
    #  Auth config
    # ------------------------------------------------------------------
    def _parse_auth(self, auth_spec: Optional[dict]) -> Optional[AuthConfig]:
        if not auth_spec:
            return None
        method_str = auth_spec.get("method", "none")
        try:
            method = AuthMethod(method_str)
        except ValueError:
            method = AuthMethod.NONE

        # Minimal mapping – you can extend as needed
        return AuthConfig(
            method=method,
            value=auth_spec.get("value"),
            param_name=auth_spec.get("param_name"),
            location=auth_spec.get("location"),
            oauth2_token_url=auth_spec.get("oauth2_token_url"),
            oauth2_client_id=auth_spec.get("oauth2_client_id"),
            # … other fields can be added here
        )

    # ------------------------------------------------------------------
    #  Internal service binding (common)
    # ------------------------------------------------------------------
    def _parse_internal_binding(self, spec: Optional[dict]) -> Optional[InternalServiceBinding]:
        if not spec:
            return None
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
    def _tools_to_operations(self, tool_bindings: list, tool_specs: list) -> List[Operation]:
        ops = []
        for binding, spec in zip(tool_bindings, tool_specs):
            # Build MSDM entity for the tool's input parameters (JSON Schema)
            params_schema = spec.get("parameters", {})
            if params_schema and params_schema.get("type") == "object":
                entity = self._json_schema_to_entity(params_schema, spec["name"] + "_input")
                if entity:
                    req_body = RequestBody(
                        description=f"Input for {spec['name']}",
                        required=True,
                        content_entity=entity,
                    )
                else:
                    req_body = None
            else:
                req_body = None

            # No path/query/header parameters – everything is in the body
            operation = Operation(
                name=spec["name"],
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,      # not HTTP
                path=f"mcp://{spec['name']}",
                parameters=[],
                request_body=req_body,
                responses=[],          # responses could be derived later
                security=[],
                tags=["MCP", "Tool"],
                deprecated=spec.get("deprecated", False),
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Generate operations from resources
    # ------------------------------------------------------------------
    def _resources_to_operations(self, resource_bindings: list, resource_specs: list) -> List[Operation]:
        ops = []
        for binding, spec in zip(resource_bindings, resource_specs):
            uri = spec["uri"]
            # Extract path parameters from URI pattern (e.g., "file:///{path}" becomes one param)
            path_params = []
            uri_pattern = re.sub(r"\{(\w+)\}", r"{\1}", uri)  # normalize
            for match in re.finditer(r"\{(\w+)\}", uri):
                param_name = match.group(1)
                path_params.append(
                    Parameter(name=param_name, location=ParameterLocation.PATH, type_string="string")
                )

            operation = Operation(
                name=f"get_resource_{spec.get('name', spec['uri'])}",
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,
                path=uri,
                parameters=path_params,
                request_body=None,  # resources usually have no request body
                responses=[],
                security=[],
                tags=["MCP", "Resource"],
                deprecated=spec.get("deprecated", False),
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Generate operations from prompts
    # ------------------------------------------------------------------
    def _prompts_to_operations(self, prompt_bindings: list, prompt_specs: list) -> List[Operation]:
        ops = []
        for binding, spec in zip(prompt_bindings, prompt_specs):
            # Prompts have an "arguments" array: each argument has name, description, required
            args = spec.get("arguments", [])
            params = []
            for arg in args:
                params.append(
                    Parameter(
                        name=arg["name"],
                        location=ParameterLocation.BODY,   # they are passed in the prompt request body
                        required=arg.get("required", False),
                        description=arg.get("description", ""),
                        type_string="string",
                    )
                )
            operation = Operation(
                name=spec["name"],
                type=OperationType.REQUEST_RESPONSE,
                description=spec.get("description", ""),
                http_method=None,
                path=f"mcp://{spec['name']}",
                parameters=params,
                request_body=None,  # arguments become separate parameters for simplicity
                responses=[],
                security=[],
                tags=["MCP", "Prompt"],
                deprecated=spec.get("deprecated", False),
            )
            ops.append(operation)
        return ops

    # ------------------------------------------------------------------
    #  Helper: JSON Schema → MSDM Entity
    # ------------------------------------------------------------------
    def _json_schema_to_entity(self, schema: dict, name: str) -> Optional[Entity]:
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
            attr_type = self._json_schema_type_string(prop_schema)
            attr = Attribute(
                name=prop_name,
                type=attr_type,
                required=prop_name in required,
                description=prop_schema.get("description", ""),
            )
            attrs.append(attr)
        return Entity(name=name, attributes=attrs)

    @staticmethod
    def _json_schema_type_string(schema: dict) -> str:
        type_map = {
            "string": "string",
            "integer": "int",
            "number": "float",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
        }
        t = schema.get("type", "string")
        if t == "array":
            items = schema.get("items", {})
            inner = MCPParser._json_schema_type_string(items) if items else "string"
            return f"array<{inner}>"
        return type_map.get(t, "string")