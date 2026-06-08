from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.ksdm_models import KSDMDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions


class KSDMJSONWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: KSDMDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: KSDMDocument) -> bytes:
        data = {
            "version": "1.0",
            "entities": [
                {
                    "id": e.id,
                    "type": e.type.value if e.type else "Unknown",
                    "label": e.label,
                    "properties": e.properties,
                    "embedding": e.embedding,
                }
                for e in document.entities
            ],
            "relations": [
                {
                    "id": r.id,
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type.value if r.type else "related",
                    "weight": r.weight,
                    "timestamp": r.timestamp,
                }
                for r in document.relations
            ],
        }
        return json.dumps(data).encode("utf-8")

    async def write_to_file(self, document: KSDMDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/json"]

    def get_supported_extensions(self) -> list[str]:
        return [".ksdm.json"]
