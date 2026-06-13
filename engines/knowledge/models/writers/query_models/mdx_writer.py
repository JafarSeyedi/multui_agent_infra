from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.knowledge.models.query_models import UnifiedQueryDocument, MdxQuery
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class MdxWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedQueryDocument) and document.mdx is not None

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        doc = cast(UnifiedQueryDocument, document)
        mdx = doc.mdx or MdxQuery()

        parts: list[str] = []

        if mdx.calculated_members:
            with_block = "WITH\n"
            for cm in mdx.calculated_members:
                with_block += f"  MEMBER {cm.name} AS '{cm.expression}'\n"
            parts.append(with_block)

        select = "SELECT\n"
        if mdx.non_empty:
            select += "  NON EMPTY\n"

        for i, axis in enumerate(mdx.axes):
            prefix = "  " if i == 0 else "  "
            select += f"{prefix}{axis.set_expression or '[Measures].members'} ON {axis.axis}"
            if i < len(mdx.axes) - 1:
                select += ",\n"

        parts.append(select)

        if mdx.cube_name:
            parts.append(f"FROM [{mdx.cube_name}]")

        if mdx.slicer:
            parts.append(f"WHERE ({mdx.slicer})")

        if mdx.cell_properties:
            parts.append(f"CELL PROPERTIES {', '.join(mdx.cell_properties)}")

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
        return [".mdx"]
