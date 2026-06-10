from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.query_models import UnifiedQueryDocument, SqlTabularQuery
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class SqlTabularWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.sql is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        sql = doc.sql or SqlTabularQuery()

        if sql.dialect == "dax_evaluate":
            text = sql.statement
        else:
            cols = ", ".join(f"[{c}]" for c in sql.columns) if sql.columns else "*"
            parts = [f"SELECT {cols}"]

            table_ref = ""
            if sql.dmv_name:
                table_ref = f"$SYSTEM.{sql.dmv_name}"
            elif sql.tables:
                table_ref = sql.tables[0]
                if sql.schema_name:
                    table_ref = f"[{sql.schema_name}].{table_ref}"
                if sql.catalog:
                    table_ref = f"[{sql.catalog}].{table_ref}"

            parts.append(f"FROM {table_ref}")
            text = "\n".join(parts)

        result = text.encode("utf-8")
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(result)
            else:
                cast(BinaryIO, destination).write(result)
        return result

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["text/plain"]

    def get_supported_extensions(self) -> list[str]:
        return [".sql.tabular"]
