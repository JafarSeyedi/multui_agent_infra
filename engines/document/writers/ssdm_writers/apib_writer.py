# engines/document/writers/ssdm_writers/apib_writer.py
"""
API Blueprint Writer – serialises an SSDM_DOCUMENT into API Blueprint (apib) format.

All output is derived from typed SSDM fields; no annotations are used.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, List, Dict, cast

from .base_ssdm_writer import BaseSSDMWriter, SSDMWriteOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    Server,
)
from ...models.base import BaseDocument


class APIBlueprintWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to API Blueprint (apib)."""

    name = "apib"
    supported_extensions = (".apib",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        lines: List[str] = []
        lines.append("FORMAT: 1A")
        lines.append("")

        # ── API Name & Description ──────────────────────────
        if document.title:
            lines.append(f"# {document.title}")
        else:
            lines.append("# Untitled API")
        lines.append("")
        if document.description:
            lines.append(document.description)
            lines.append("")

        # ── Version ─────────────────────────────────────────
        if document.version:
            lines.append(f"## Version: {document.version}")
            lines.append("")

        # ── Servers (HOST) ──────────────────────────────────
        if document.servers:
            for server in document.servers:
                lines.append(f"## HOST: {server.url}")
                if server.description:
                    lines.append(f"// {server.description}")
                lines.append("")

        # ── Contact / License (as comments) ─────────────────
        if document.contact:
            contact = document.contact
            if contact.name:
                lines.append(f"// Contact: {contact.name}")
            if contact.url:
                lines.append(f"// Contact URL: {contact.url}")
            if contact.email:
                lines.append(f"// Contact Email: {contact.email}")
            lines.append("")
        if document.license:
            lic = document.license
            lines.append(f"// License: {lic.name}")
            if lic.url:
                lines.append(f"// License URL: {lic.url}")
            lines.append("")

        # ── Security Schemes (as comments) ──────────────────
        if document.security_schemes:
            lines.append("// Security:")
            for scheme in document.security_schemes:
                lines.append(f"//   {scheme.type.value}: {scheme.name}")
            lines.append("")

        # ── Group operations by path ────────────────────────
        operations_by_path: Dict[str, List[Operation]] = {}
        for op in document.operations:
            path = op.path or "/"
            operations_by_path.setdefault(path, []).append(op)

        # ── Write resource groups ───────────────────────────
        for path, ops in operations_by_path.items():
            # Resource section header
            resource_name = path.strip("/") or "Root"
            lines.append(f"## {resource_name} [{path}]")
            if ops and ops[0].description:
                lines.append(ops[0].description)
            lines.append("")

            for op in ops:
                lines.append(f"### {op.http_method.value if op.http_method else 'GET'} {path}")
                if op.description:
                    lines.append(op.description)
                lines.append("")

                # Request section (parameters + body)
                has_request = False
                if op.parameters or op.request_body:
                    has_request = True
                    lines.append("+ Request")
                    if op.parameters:
                        for param in op.parameters:
                            self._write_parameter(lines, param)
                    if op.request_body:
                        self._write_body(lines, op.request_body, indent="    ")

                # Response section
                if op.responses:
                    lines.append("")
                    for resp in op.responses:
                        lines.append(f"+ Response {resp.status_code}")
                        if resp.description:
                            lines.append(f"    {resp.description}")
                        if resp.content_entity:
                            # Write MSDM entity as JSON Schema inline (simplified)
                            lines.append("    + Body")
                            lines.append("")
                            lines.append("            {" + self._entity_to_json_schema(resp.content_entity) + "}")
                elif not has_request:
                    # Placeholder response for actions without definition
                    lines.append("+ Response 200")
                    lines.append("")

                lines.append("")

        # ── Type definitions (MSDM) as Data Structures ───────
        if document.type_definitions:
            lines.append("# Data Structures")
            for entity in document.type_definitions.entities:
                lines.append(f"## {entity.name} (object)")
                for attr in entity.attributes:
                    lines.append(f"+ {attr.name}: {self._datatype_to_apib(attr.data_type)}")
                lines.append("")

        return "\n".join(lines).encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["text/vnd.apiblueprint+markdown"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Helpers ──────────────────────────────────────────────────
    @staticmethod
    def _write_parameter(lines: List[str], param: Parameter):
        """Write a single parameter in API Blueprint format."""
        loc = param.location.value
        if loc == "path":
            lines.append(f"    + Parameters")
            lines.append(f"        + {param.name}: ({param.type_string or 'string'}) - {param.description or ''}")
        elif loc == "query":
            lines.append(f"    + Query Parameters")
            lines.append(f"        + {param.name}: ({param.type_string or 'string'}) - {param.description or ''}")
        elif loc == "header":
            lines.append(f"    + Headers")
            lines.append(f"        {param.name}: {param.description or ''}")
        elif loc == "cookie":
            lines.append(f"    + Cookies")
            lines.append(f"        {param.name}: {param.description or ''}")

    @staticmethod
    def _write_body(lines: List[str], body: RequestBody, indent: str = "    "):
        """Write request body."""
        lines.append(f"{indent}+ Request (application/json)")
        if body.content_entity:
            # generate a simple JSON example or schema description
            lines.append(f"{indent}    " + "{ ... }")

    @staticmethod
    def _entity_to_json_schema(entity) -> str:
        """Convert an MSDM Entity to a simple JSON object string."""
        props = []
        for attr in entity.attributes:
            props.append(f'"{attr.name}": "{APIBlueprintWriter._datatype_to_json(attr.data_type)}"')
        return ", ".join(props)

    @staticmethod
    def _datatype_to_apib(dt) -> str:
        """Map MSDM DataType to API Blueprint type string."""
        from ...models.msdm_models import ScalarType
        mapping = {
            ScalarType.STRING: "string",
            ScalarType.INT: "number",
            ScalarType.FLOAT: "number",
            ScalarType.BOOLEAN: "boolean",
            ScalarType.ANY: "any",
        }
        return mapping.get(dt.base, "string")

    @staticmethod
    def _datatype_to_json(dt) -> str:
        """Map MSDM DataType to JSON type example."""
        from ...models.msdm_models import ScalarType
        mapping = {
            ScalarType.STRING: "string",
            ScalarType.INT: "integer",
            ScalarType.FLOAT: "number",
            ScalarType.BOOLEAN: "boolean",
        }
        return mapping.get(dt.base, "string")