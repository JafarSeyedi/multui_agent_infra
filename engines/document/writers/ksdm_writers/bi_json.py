from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.ksdm_models import BIAggregatorModel
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class BIAggregatorJSONWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: BIAggregatorModel) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: BIAggregatorModel) -> bytes:
        data = {
            "version": document.version,
            "schedule": document.schedule,
            "aggregations": document.aggregations,
            "sources": document.sources,
            "targets": document.targets,
        }
        return json.dumps(data).encode("utf-8")

    async def write_to_file(self, document: BIAggregatorModel, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".bi.json"]
