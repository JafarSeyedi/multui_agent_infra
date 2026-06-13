from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.knowledge.models.ksdm_models import UnifiedBiAggregationDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class TableauHyperWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, UnifiedBiAggregationDocument)

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        raise RuntimeError(
            "Tableau .hyper is a binary format requiring the Tableau Hyper API Python library. "
            "Install `pip install tableauhyperapi` to write .hyper files."
        )

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        raise RuntimeError(
            "Tableau .hyper is a binary format requiring the Tableau Hyper API Python library."
        )
        if False:
            yield b""

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        raise RuntimeError(
            "Tableau .hyper is a binary format requiring the Tableau Hyper API Python library. "
            "Install `pip install tableauhyperapi` and use the TableauHyperParser with a file path."
        )

    def get_supported_media_types(self) -> list[str]:
        return ["application/octet-stream"]

    def get_supported_extensions(self) -> list[str]:
        return [".hyper"]
