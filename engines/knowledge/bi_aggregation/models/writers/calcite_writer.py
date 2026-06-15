from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.bi_aggregation.models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class CalciteWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedBiAggregationDocument, document)

        payload: dict[str, Any] = {
            "version": "1.0",
            "defaultSchema": doc.name or "default",
        }

        schemas: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        for src in doc.sources:
            tbl: dict[str, Any] = {
                "name": src.name,
                "type": src.source_type if src.source_type in ("custom", "view") else "custom",
                "factory": "unified_datasource",
            }
            oper: dict[str, Any] = {}
            columns: list[dict[str, str]] = []
            for dim in doc.dimensions:
                if dim.source_table == src.name:
                    for attr in dim.attributes:
                        col: dict[str, str] = {"name": attr.name}
                        if attr.data_type:
                            col["type"] = attr.data_type
                        columns.append(col)
            if columns:
                oper["columns"] = columns
            if oper:
                tbl["operand"] = oper
            tables.append(tbl)

        if tables:
            schemas.append({
                "name": doc.name or "default",
                "tables": tables,
            })
        if schemas:
            payload["schemas"] = schemas

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
        return [".calcite.json", ".model.json"]
