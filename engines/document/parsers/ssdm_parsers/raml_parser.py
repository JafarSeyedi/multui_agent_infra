# engines/document/parsers/ssdm_parsers/raml_parser.py
"""
RAML 1.0 Parser – converts a .raml file into an SSDM_DOCUMENT.

Mapping rules (RAML → SSDM):
- title, version, description           → SSDM_DOCUMENT fields
- baseUri, baseUriParameters             → Server (with variables)
- types                                  → MSDM entities (type_definitions)
- /resource                              → operations grouped by path
  - get, post, put, delete, etc.         → Operation (http_method, name derived from path+method)
  - queryParameters                      → Parameter (location=QUERY)
  - headers                              → Parameter (location=HEADER)
  - body (each media type)               → RequestBody (content_type_entities)
  - responses (status codes)             → Response objects (content_entity per media type)
- securitySchemes                        → SecurityScheme
- securedBy                              → operation.security
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union

from .base_ssdm_parser import BaseSSDMParser
from ..base import ParseOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    OperationType,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    SecurityScheme,
    SecurityType,
    ApiKeyLocation,
    Server,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
    Constraint,
    ConstraintType,
)
from ...models.base import BaseDocument

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required for RAML parser. Install with: pip install pyyaml")


class RAMLParser(BaseSSDMParser):
    """Parser for RAML 1.0 files (.raml)."""

    name = "raml"
    supported_extensions = (".raml",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        raml = yaml.safe_load(text)

        doc = SSDM_DOCUMENT(
            title=raml.get("title", Path(source_name).stem),
            version=raml.get("version", "1.0.0"),
        )
        description = raml.get("description")
        if description:
            doc.description = description

        # Servers
        base_uri = raml.get("baseUri")
        base_uri_params = raml.get("baseUriParameters")
        if base_uri:
            server = Server(url=base_uri)
            if base_uri_params:
                server.variables = {k: v.get("default", "") for k, v in base_uri_params.items() if isinstance(v, dict)}
            doc.servers.append(server)

        # Types
        types = raml.get("types")
        if types:
            msdm = MSDMDocument()
            for type_name, type_def in types.items():
                entity = self._parse_raml_type(type_name, type_def)
                msdm.entities.append(entity)
            doc.type_definitions = msdm

        # Security schemes
        security_schemes = raml.get("securitySchemes")
        if security_schemes:
            for scheme_name, scheme_def in security_schemes.items():
                doc.security_schemes.append(self._parse_security_scheme(scheme_name, scheme_def))

        # Resources (paths)
        resources = raml.get("/", {})
        if isinstance(raml, dict):
            # The top-level RAML may contain resource keys starting with "/"
            for key, value in raml.items():
                if key.startswith("/"):
                    self._parse_resource(doc, key, value)
        # The root resource "/" is special: we must handle if RAML root is the resource itself.
        # Usually, RAML has a root level with properties, and resources are under the key "/".
        # However, some RAML files put everything under "/".
        # The above loop handles any key starting with "/". Good.

        return doc

    def _parse_resource(self, doc: SSDM_DOCUMENT, path: str, resource: Any) -> None:
        """Parse a RAML resource node and create operations for each HTTP method."""
        if not isinstance(resource, dict):
            return
        # Methods
        for method in ("get", "post", "put", "delete", "patch", "head", "options", "trace"):
            method_def = resource.get(method)
            if method_def is not None:
                op = self._parse_method(method, path, method_def)
                doc.operations.append(op)

        # Nested resources (sub‑paths)
        for key, value in resource.items():
            if key.startswith("/"):
                nested_path = path.rstrip("/") + key
                self._parse_resource(doc, nested_path, value)

    def _parse_method(self, method: str, path: str, method_def: Dict) -> Operation:
        op_name = f"{method.upper()} {path}"
        op = Operation(
            name=op_name,
            http_method=method.upper(),
            path=path,
            type=OperationType.REQUEST_RESPONSE,
        )
        if method_def.get("description"):
            op.description = method_def["description"]

        # Query parameters
        query_params = method_def.get("queryParameters") or method_def.get("queryString")  # RAML 0.8/1.0
        if query_params:
            for param_name, param_def in query_params.items():
                if isinstance(param_def, dict):
                    op.parameters.append(self._parse_parameter(param_name, param_def, ParameterLocation.QUERY))
                else:
                    op.parameters.append(Parameter(name=param_name, location=ParameterLocation.QUERY))

        # Headers
        headers = method_def.get("headers")
        if headers:
            for header_name, header_def in headers.items():
                if isinstance(header_def, dict):
                    op.parameters.append(self._parse_parameter(header_name, header_def, ParameterLocation.HEADER))
                else:
                    op.parameters.append(Parameter(name=header_name, location=ParameterLocation.HEADER))

        # URI parameters (from path variables) – should be defined at resource level with uriParameters;
        # we won't parse deeply here, but can be added.

        # Body
        body = method_def.get("body")
        if body:
            request_body = RequestBody(required=True)
            if body.get("description"):
                request_body.description = body["description"]
            for media_type, media_def in body.items():
                if media_type in ("description", "required", "displayName"):
                    continue
                # media_def is a dict with "type" field (or inline type)
                entity = self._inline_type_to_entity(f"{op_name}_body", media_def)
                if entity:
                    request_body.content_type_entities[media_type] = entity
            if request_body.content_type_entities:
                op.request_body = request_body

        # Responses
        responses = method_def.get("responses")
        if responses:
            for status_code, resp_def in responses.items():
                response = Response(status_code=str(status_code))
                if isinstance(resp_def, dict):
                    response.description = resp_def.get("description")
                    resp_body = resp_def.get("body")
                    if resp_body:
                        for media_type, media_def in resp_body.items():
                            if media_type in ("description", "required"):
                                continue
                            entity = self._inline_type_to_entity(f"{op_name}_resp_{status_code}", media_def)
                            if entity:
                                response.content_type_entities[media_type] = entity
                op.responses.append(response)

        # Security
        secured_by = method_def.get("securedBy")
        if secured_by:
            op.security = secured_by if isinstance(secured_by, list) else [secured_by]

        return op

    def _parse_parameter(self, name: str, param_def: Dict, location: ParameterLocation) -> Parameter:
        required = param_def.get("required", False)
        ptype = param_def.get("type")
        param = Parameter(
            name=name,
            location=location,
            required=required,
            description=param_def.get("description"),
            type_string=ptype,
        )
        return param

    # ── RAML type → MSDM Entity ─────────────────────────────────
    def _parse_raml_type(self, type_name: str, type_def: Union[Dict, str]) -> Entity:
        entity = Entity(name=type_name)
        if isinstance(type_def, str):
            # Simple type alias, e.g., "string"
            pass  # Not an object
        elif isinstance(type_def, dict):
            if type_def.get("type") == "object" or "properties" in type_def:
                properties = type_def.get("properties", {})
                for prop_name, prop_def in properties.items():
                    dt = self._raml_prop_to_datatype(prop_def)
                    required = prop_def.get("required", False) if isinstance(prop_def, dict) else False
                    attr = Attribute(name=prop_name, data_type=dt, required=required)
                    entity.attributes.append(attr)
        return entity

    def _raml_prop_to_datatype(self, prop_def: Union[Dict, str]) -> DataType:
        if isinstance(prop_def, str):
            return DataType(base=self._raml_scalar(prop_def))
        if isinstance(prop_def, dict):
            ptype = prop_def.get("type", "string")
            if ptype == "array":
                items = prop_def.get("items", "string")
                inner = self._raml_prop_to_datatype(items)
                return DataType(base=ScalarType.ARRAY, element_type=inner)
            if ptype == "object":
                # Could be a reference to another type
                ref = prop_def.get("properties", {}).get("type")
                if ref:
                    return DataType(base=ScalarType.REF, ref_entity=ref)
                return DataType(base=ScalarType.STRUCT)
            return DataType(base=self._raml_scalar(ptype))
        return DataType(base=ScalarType.ANY)

    def _raml_scalar(self, name: str) -> ScalarType:
        mapping = {
            "string": ScalarType.STRING,
            "number": ScalarType.FLOAT,
            "integer": ScalarType.INT,
            "boolean": ScalarType.BOOLEAN,
            "date-only": ScalarType.DATE,
            "time-only": ScalarType.TIME,
            "datetime-only": ScalarType.TIMESTAMP,
            "datetime": ScalarType.TIMESTAMP,
            "file": ScalarType.BINARY,
            "any": ScalarType.ANY,
        }
        return mapping.get(name, ScalarType.ANY)

    # ── Inline body type → MSDM Entity (helper) ─────────────────
    def _inline_type_to_entity(self, base_name: str, media_def: Union[Dict, str]) -> Optional[Entity]:
        if isinstance(media_def, str):
            # Reference to a named type
            entity = Entity(name=media_def)
            # It's a reference; we won't add attributes. But we need something.
            return entity
        elif isinstance(media_def, dict):
            type_name = media_def.get("type", base_name)
            if isinstance(type_name, dict):
                # Inline object definition
                inline_entity = Entity(name=base_name)
                properties = type_name.get("properties", {})
                for pname, pdef in properties.items():
                    dt = self._raml_prop_to_datatype(pdef)
                    inline_entity.attributes.append(Attribute(name=pname, data_type=dt))
                return inline_entity
            else:
                # type_name is a reference string
                ref_entity = Entity(name=type_name)
                return ref_entity
        return None

    # ── Security scheme ─────────────────────────────────────────
    def _parse_security_scheme(self, name: str, scheme_def: Dict) -> SecurityScheme:
        stype = scheme_def.get("type", "OAuth 2.0")
        type_map = {
            "OAuth 2.0": SecurityType.OAUTH2,
            "Basic Authentication": SecurityType.HTTP_BASIC,
            "Digest Authentication": SecurityType.HTTP_BASIC,   # not exact
            "Pass Through": SecurityType.API_KEY,
            "x-": SecurityType.API_KEY,
        }
        security_type = type_map.get(stype, SecurityType.API_KEY)
        scheme = SecurityScheme(name=name, type=security_type)
        scheme.description = scheme_def.get("description")
        if security_type == SecurityType.API_KEY:
            described_by = scheme_def.get("describedBy", {})
            headers = described_by.get("headers", {})
            for hname, hdef in headers.items():
                scheme.api_key_param_name = hname
                scheme.api_key_location = ApiKeyLocation.HEADER
                break
        return scheme