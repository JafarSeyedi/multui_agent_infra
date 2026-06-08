from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from engines.document.models.lsdm_models import EsBulkAction, EventLogDocument
from engines.document.writers.base import BaseDocumentWriter, WriteOptions

ACTION_KEY_MAP = {
    EsBulkAction.INDEX: "index",
    EsBulkAction.CREATE: "create",
    EsBulkAction.UPDATE: "update",
    EsBulkAction.DELETE: "delete",
}


class EsBulkWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: EventLogDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: EventLogDocument) -> bytes:
        lines: list[str] = []
        for event in document.events:
            meta = event.es_action_meta
            if meta:
                action_key = ACTION_KEY_MAP.get(meta.action, "index")
                action_line = {action_key: {"_index": meta.index}}
                if meta.doc_id:
                    action_line[action_key]["_id"] = meta.doc_id
                lines.append(json.dumps(action_line))
                if meta.action != EsBulkAction.DELETE:
                    lines.append(json.dumps(event.es_source))
        return "\n".join(lines).encode("utf-8")

    async def write_to_file(self, document: EventLogDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-ndjson"]

    def get_supported_extensions(self) -> list[str]:
        return [".ndjson", ".es.bulk"]
