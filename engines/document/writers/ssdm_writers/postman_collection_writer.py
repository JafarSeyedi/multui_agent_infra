# engines/document/writers/ssdm_writers/postman_collection_writer.py
"""
Postman Collection Writer – serialises an SSDM_DOCUMENT into a Postman Collection JSON (v2.1).

All data is obtained from typed SSDM fields; no annotations are used.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, cast

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
from ...models.msdm_models import (
    Entity,
    Attribute,
    DataType,
    ScalarType,
)
from ...models.base import BaseDocument


class PostmanCollectionWriter(BaseSSDMWriter):
    """Serialises an SSDM_DOCUMENT to a Postman Collection JSON file."""

    name = "postman_collection"
    supported_extensions = (".postman_collection.json",)

    def __init__(self, options: Optional[SSDMWriteOptions] = None):
        super().__init__(options)

    async def _write_design(self, document: SSDM_DOCUMENT) -> bytes:
        collection: Dict[str, Any] = {
            "info": {
                "name": document.title or "Untitled Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

        if document.description:
            collection["info"]["description"] = document.description

        # Build variables from server variables (if any)
        if document.servers:
            collection["variable"] = []
            for server in document.servers:
                for var_name, default_val in server.variables.items():
                    collection["variable"].append({
                        "key": var_name,
                        "value": default_val,
                    })

        # Convert operations to request items
        for op in document.operations:
            item = self._build_request_item(op)
            collection["item"].append(item)

        json_str = json.dumps(collection, indent=2, ensure_ascii=False)
        return json_str.encode(self.options.encoding or "utf-8")

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return list(self.supported_extensions)

    # ── Build a request item from an operation ─────────────────────
    def _build_request_item(self, op: Operation) -> dict:
        method = op.http_method.value if op.http_method else "GET"
        url_path = op.path or "/"

        item: Dict[str, Any] = {
            "name": op.name,
            "request": {
                "method": method,
                "header": [],
                "url": {
                    "raw": f"{{base_url}}{url_path}",
                    "host": ["{{base_url}}"],
                    "path": [seg for seg in url_path.strip("/").split("/") if seg],
                },
            },
        }

        if op.description:
            item["request"]["description"] = op.description

        # Parameters
        if op.parameters:
            for param in op.parameters:
                if param.location == ParameterLocation.HEADER:
                    item["request"]["header"].append({
                        "key": param.name,
                        "value": param.type_string or "",
                        "description": param.description or "",
                    })
                elif param.location == ParameterLocation.QUERY:
                    item["request"]["url"].setdefault("query", []).append({
                        "key": param.name,
                        "value": param.type_string or "",
                        "description": param.description or "",
                    })
                elif param.location == ParameterLocation.PATH:
                    # Replace placeholder in the path
                    item["request"]["url"]["path"] = [
                        p if p != f"{{{param.name}}}" else f":{param.name}"
                        for p in item["request"]["url"]["path"]
                    ]

        # Request body
        if op.request_body:
            body_mode = "raw"
            body_options = {"raw": {"language": "json"}}
            if op.request_body.content_entity:
                body_options["raw"]["body"] = self._entity_to_json_example(
                    op.request_body.content_entity
                )
            item["request"]["body"] = {
                "mode": body_mode,
                "options": body_options,
            }

        # Responses (examples)
        if op.responses:
            item.setdefault("response", [])
            for resp in op.responses:
                example = {
                    "name": resp.description or f"Status {resp.status_code}",
                    "status": resp.status_code,
                    "code": int(resp.status_code) if resp.status_code.isdigit() else 200,
                }
                if resp.content_entity:
                    example["body"] = self._entity_to_json_example(resp.content_entity)
                item["response"].append(example)

        return item

    # ── MSDM Entity → JSON example string ─────────────────────────
    def _entity_to_json_example(self, entity: Entity) -> str:
        """Produce a JSON example from an MSDM Entity."""
        obj = {}
        for attr in entity.attributes:
            obj[attr.name] = self._attribute_to_example(attr)
        return json.dumps(obj, indent=2)

    def _attribute_to_example(self, attr: Attribute) -> Any:
        dt = attr.data_type
        base = dt.base
        if base == ScalarType.ARRAY:
            if dt.element_type:
                inner = self._attribute_to_example(
                    Attribute(name="item", data_type=dt.element_type)
                )
                return [inner]
            return ["string"]
        if base == ScalarType.MAP:
            return {"key": "value"}
        if base == ScalarType.REF:
            return f"ref:{dt.ref_entity}"
        if base == ScalarType.STRUCT:
            return {}
        return self._scalar_example(base)

    @staticmethod
    def _scalar_example(base: ScalarType) -> Any:
        mapping = {
            ScalarType.STRING: "string",
            ScalarType.INT: 0,
            ScalarType.LONG: 0,
            ScalarType.FLOAT: 0.0,
            ScalarType.DOUBLE: 0.0,
            ScalarType.BOOLEAN: True,
            ScalarType.DATE: "2025-01-01",
            ScalarType.TIME: "12:00:00",
            ScalarType.TIMESTAMP: "2025-01-01T00:00:00Z",
            ScalarType.DURATION: "PT1H",
            ScalarType.UUID: "550e8400-e29b-41d4-a716-446655440000",
            ScalarType.BINARY: "<binary>",
            ScalarType.DECIMAL: 0.0,
            ScalarType.ANY: None,
        }
        return mapping.get(base, "string")