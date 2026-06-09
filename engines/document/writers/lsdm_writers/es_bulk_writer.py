from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from engines.document.models.lsdm_models import EsBulkAction, EventLogDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter, WriteOptions

ACTION_KEY_MAP = {
    EsBulkAction.INDEX: "index",
    EsBulkAction.CREATE: "create",
    EsBulkAction.UPDATE: "update",
    EsBulkAction.DELETE: "delete",
}


class EsBulkWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(cast(EventLogDocument, document))

    async def write(self, document: BaseDocument) -> bytes:
        doc = cast(EventLogDocument, document)
        lines: list[str] = []
        for event in doc.events:
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

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(cast(EventLogDocument, document)))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-ndjson"]

    def get_supported_extensions(self) -> list[str]:
        return [".ndjson", ".es.bulk"]