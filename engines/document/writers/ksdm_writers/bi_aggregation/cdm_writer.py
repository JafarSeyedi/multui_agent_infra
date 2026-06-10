from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class CdmWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)

        payload: dict[str, Any] = {
            "name": doc.name or "cdm_model",
        }
        if doc.description:
            payload["description"] = doc.description

        entities: list[dict[str, Any]] = []
        for src in doc.sources:
            entity: dict[str, Any] = {"name": src.name}
            if src.description:
                entity["description"] = src.description

            attributes: list[dict[str, Any]] = []
            for dim in doc.dimensions:
                if dim.source_table == src.name:
                    for attr in dim.attributes:
                        attr_dict: dict[str, Any] = {"name": attr.name}
                        if attr.data_type:
                            attr_dict["dataType"] = attr.data_type
                        attributes.append(attr_dict)
            if attributes:
                entity["attributes"] = attributes
            entities.append(entity)

        if entities:
            payload["entities"] = entities

        relationships: list[dict[str, str]] = []
        for rel in doc.relationships:
            relationships.append({
                "name": rel.name,
                "fromEntity": rel.source_table,
                "fromAttribute": rel.source_column,
                "toEntity": rel.target_table,
                "toAttribute": rel.target_column,
            })
        if relationships:
            payload["relationships"] = relationships

        json_bytes = json.dumps(payload, indent=2).encode("utf-8")
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(json_bytes)
            else:
                cast(BinaryIO, destination).write(json_bytes)
        return json_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".cdm.json"]
