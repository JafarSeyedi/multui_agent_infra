from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.query_models import UnifiedQueryDocument, PowerQueryM
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class PowerQueryMWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.m_query is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        m = doc.m_query or PowerQueryM()

        if m.let_expression:
            text = m.let_expression
        else:
            parts = ["let"]
            for name, expr in m.variables.items():
                parts.append(f"    {name} = {expr},")
            if m.output:
                parts.append("in")
                parts.append(f"    {m.output}")
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
        return [".m"]
