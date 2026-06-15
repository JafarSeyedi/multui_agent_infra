from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.query.models import UnifiedQueryDocument, JpqlQuery
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class JpqlWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.jpql is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        jpql = doc.jpql or JpqlQuery()

        if jpql.statement:
            text = jpql.statement
        else:
            cols = ", ".join(jpql.fields) if jpql.fields else "*"
            text = f"SELECT {cols} FROM {jpql.entity_name or 'Entity'}"

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
        return [".jpql"]
