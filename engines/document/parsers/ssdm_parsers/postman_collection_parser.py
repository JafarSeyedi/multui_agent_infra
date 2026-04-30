# engines/document/parsers/ssdm_parsers/postman_collection_parser.py
"""
Postman Collection Parser – converts a Postman Collection JSON (v2.1) into an
SSDM_DOCUMENT.

Mapping rules (Postman → SSDM):
- info.name                                          → SSDM_DOCUMENT.title
- info.description                                   → SSDM_DOCUMENT.description
- item[]                                             → Operation
  - request.method                                   → Operation.http_method
  - request.url.raw / host + path                    → Operation.path
  - request.url.query[]                              → Parameter (location=QUERY)
  - request.url.variable[]                           → Parameter (location=PATH)
  - request.header[]                                 → Parameter (location=HEADER)
  - request.body (raw, json, etc.)                   → RequestBody (content_entity)
  - response[]                                       → Response objects with content_entity
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from .base_ssdm_parser import BaseSSDMParser
from ..base import ParseOptions
from ...models.ssdm_models import (
    SSDM_DOCUMENT,
    Operation,
    Parameter,
    ParameterLocation,
    RequestBody,
    Response,
    Server,
)
from ...models.msdm_models import (
    MSDMDocument,
    Entity,
    Attribute,
    DataType,
    ScalarType,
)
from ...models.base import BaseDocument


class PostmanCollectionParser(BaseSSDMParser):
    """Parser for Postman Collection JSON files (.postman_collection.json)."""

    name = "postman_collection"
    supported_extensions = (".postman_collection.json",)

    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        encoding = options.encoding or "utf-8"
        text = data.decode(encoding)
        collection = json.loads(text)

        info = collection.get("info", {})
        doc = SSDM_DOCUMENT(
            title=info.get("name", Path(source_name).stem),
            version="1.0.0",
        )
        if info.get("description"):
            doc.description = info["description"]

        # Variables at collection level could become server variables
        variables = collection.get("variable", [])
        if variables:
            server_vars = {v["key"]: v.get("value", "") for v in variables}
            # We'll add a server with base URL extracted from the first request? Not always present.
            # We'll set a placeholder server with these variables.
            base_url = "{{base_url}}"
            doc.servers.append(Server(url=base_url, variables=server_vars))

        # Process items (flatten folders and requests)
        items = collection.get("item", [])
        for item in items:
            self._process_item(doc, item, base_path="")

        return doc

    def _process_item(self, doc: SSDM_DOCUMENT, item: dict, base_path: str) -> None:
        """Recursively process items (folders contain other items)."""
        if "item" in item:
            # It's a folder – recurse with updated base path
            folder_name = item.get("name", "")
            for sub_item in item["item"]:
                self._process_item(doc, sub_item, base_path + "/" + folder_name)
        elif "request" in item:
            # It's a request
            op = self._parse_request(item)
            doc.operations.append(op)

    def _parse_request(self, item: dict) -> Operation:
        name = item.get("name", "Unnamed")
        request = item["request"]
        method = request.get("method", "GET").upper()
        url_def = request.get("url", {})

        # Determine path
        path = url_def.get("path", [])
        raw_url = url_def.get("raw", "")
        if not raw_url and isinstance(path, list):
            # reconstruct raw from host + path
            host = ".".join(url_def.get("host", ["localhost"]))
            raw_url = f"http://{host}/{'/'.join(path)}"

        op = Operation(
            name=f"{method} {name}",
            http_method=method,
            path=raw_url,
        )

        # Query parameters
        query_params = url_def.get("query", [])
        for q in query_params:
            if isinstance(q, dict):
                op.parameters.append(Parameter(
                    name=q.get("key", ""),
                    location=ParameterLocation.QUERY,
                    description=q.get("description"),
                    type_string="string",
                ))

        # Path variables
        variables = url_def.get("variable", [])
        for var in variables:
            if isinstance(var, dict):
                op.parameters.append(Parameter(
                    name=var.get("key", ""),
                    location=ParameterLocation.PATH,
                    required=True,
                    type_string="string",
                ))

        # Headers
        headers = request.get("header", [])
        for hdr in headers:
            if isinstance(hdr, dict):
                op.parameters.append(Parameter(
                    name=hdr.get("key", ""),
                    location=ParameterLocation.HEADER,
                    description=hdr.get("description"),
                    type_string="string",
                ))

        # Request body
        body = request.get("body")
        if body:
            mode = body.get("mode", "")
            if mode == "raw":
                raw_body = body.get("raw", "")
                # Try to parse as JSON and infer schema
                try:
                    data = json.loads(raw_body)
                    entity = self._infer_entity_from_json(data, f"{name}_body")
                    if entity:
                        op.request_body = RequestBody(
                            content_entity=entity,
                            required=True,
                        )
                except json.JSONDecodeError:
                    pass

        # Responses (examples)
        responses = item.get("response", [])
        for resp in responses:
            r = Response(status_code=str(resp.get("code", 200)))
            r.description = resp.get("name")
            resp_body = resp.get("body")
            if resp_body and isinstance(resp_body, str):
                try:
                    data = json.loads(resp_body)
                    entity = self._infer_entity_from_json(data, f"{name}_resp_{resp.get('code')}")
                    if entity:
                        r.content_entity = entity
                except json.JSONDecodeError:
                    pass
            op.responses.append(r)

        return op

    def _infer_entity_from_json(self, data: Any, entity_name: str) -> Optional[Entity]:
        """Create a simple MSDM entity from JSON data by inspecting keys."""
        if not isinstance(data, dict):
            return None
        entity = Entity(name=entity_name)
        for key, value in data.items():
            dt = self._infer_datatype(value)
            entity.attributes.append(Attribute(name=key, data_type=dt, required=True))
        return entity

    def _infer_datatype(self, value: Any) -> DataType:
        """Infer MSDM DataType from a Python value."""
        if isinstance(value, str):
            return DataType(base=ScalarType.STRING)
        if isinstance(value, bool):
            return DataType(base=ScalarType.BOOLEAN)
        if isinstance(value, int):
            return DataType(base=ScalarType.INT)
        if isinstance(value, float):
            return DataType(base=ScalarType.FLOAT)
        if isinstance(value, list):
            if len(value) > 0:
                inner = self._infer_datatype(value[0])
                return DataType(base=ScalarType.ARRAY, element_type=inner)
            return DataType(base=ScalarType.ARRAY)
        if isinstance(value, dict):
            return DataType(base=ScalarType.STRUCT)
        return DataType(base=ScalarType.ANY)