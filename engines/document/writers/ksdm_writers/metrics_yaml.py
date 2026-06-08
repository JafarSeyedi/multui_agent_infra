from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import yaml

from engines.document.models.ksdm_models import KSDMMetricsDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class KSDMMetricsYAMLWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: KSDMMetricsDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: KSDMMetricsDocument) -> bytes:
        data = {
            "version": "2.0",
            "granularity": document.granularity.value if document.granularity else "day",
            "dimensions": document.dimensions,
            "metrics": [{"name": m.name, "type": m.type.value if m.type else "gauge"} for m in document.metrics],
        }
        return yaml.dump(data).encode("utf-8")

    async def write_to_file(self, document: KSDMMetricsDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-yaml"]

    def get_supported_extensions(self) -> list[str]:
        return [".ksdm_metrics.yaml", ".isfm.yaml"]
