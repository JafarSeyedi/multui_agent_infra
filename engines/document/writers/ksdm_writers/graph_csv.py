from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.ksdm_models import KSDMDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class CSVGraphWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: KSDMDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: KSDMDocument) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["source_id", "target_id", "relation_type", "weight", "timestamp"])
        for r in document.relations:
            writer.writerow([r.source_id, r.target_id, r.type.value if r.type else "", r.weight or "", r.timestamp or ""])
        return output.getvalue().encode("utf-8")

    async def write_to_file(self, document: KSDMDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["text/csv"]

    def get_supported_extensions(self) -> list[str]:
        return [".csv"]
