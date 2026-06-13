from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class TmslWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)

        model: dict[str, Any] = {"name": doc.name or "tmsl_model"}

        if doc.description:
            model["description"] = doc.description

        tables: list[dict[str, Any]] = []
        for src in doc.sources:
            table: dict[str, Any] = {"name": src.name}
            columns: list[dict[str, Any]] = []
            for dim in doc.dimensions:
                if dim.source_table == src.name:
                    for attr in dim.attributes:
                        col: dict[str, Any] = {"name": attr.name}
                        if attr.source_column:
                            col["sourceColumn"] = attr.source_column
                        if attr.data_type:
                            col["dataType"] = attr.data_type
                        columns.append(col)

            table_measures: list[dict[str, Any]] = []
            for meas in doc.measures:
                table_measures.append({
                    "name": meas.name,
                    "expression": meas.source_column or meas.name,
                    "formatString": meas.format_string or "",
                })

            if columns:
                table["columns"] = columns
            if table_measures:
                table["measures"] = table_measures
            tables.append(table)

        if tables:
            model["tables"] = tables

        relationships: list[dict[str, str]] = []
        for rel in doc.relationships:
            relationships.append({
                "name": rel.name,
                "fromTable": rel.source_table,
                "fromColumn": rel.source_column,
                "toTable": rel.target_table,
                "toColumn": rel.target_column,
            })
        if relationships:
            model["relationships"] = relationships

        payload: dict[str, Any] = {"model": model}
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
        return [".bim"]
