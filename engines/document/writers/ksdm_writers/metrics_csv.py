from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.ksdm_models import KSDMMetricsDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class MetricsCSVWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: KSDMMetricsDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: KSDMMetricsDocument) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric_name", "type", "value", "timestamp", "labels"])
        for m in document.metrics:
            labels = ";".join(f"{k}={v}" for k, v in (m.labels or {}).items())
            writer.writerow([m.name, m.type.value if m.type else "", m.value, m.timestamp or "", labels])
        return output.getvalue().encode("utf-8")

    async def write_to_file(self, document: KSDMMetricsDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["text/csv"]

    def get_supported_extensions(self) -> list[str]:
        return [".csv"]
