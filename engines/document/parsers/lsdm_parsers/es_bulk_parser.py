from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from engines.document.models.lsdm_models import (
    EsBulkAction,
    EsBulkActionMeta,
    EventLogDocument,
    LogEvent,
    LogSource,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from engines.document.models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions


class EsBulkParser(BaseDocumentParser):
    name = "es_bulk_parser"
    supported_extensions = [".ndjson", ".es.bulk"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        text = data.decode("utf-8")
        events: list[LogEvent] = []
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            try:
                action_line = json.loads(line)
            except json.JSONDecodeError:
                i += 1
                continue
            if not isinstance(action_line, dict):
                i += 1
                continue
            action: EsBulkAction | None = None
            index_name = ""
            doc_id: str | None = None
            for action_key in ("index", "create", "update", "delete"):
                if action_key in action_line:
                    action = EsBulkAction(action_key)
                    meta = action_line[action_key]
                    if isinstance(meta, dict):
                        index_name = meta.get("_index", "")
                        doc_id = meta.get("_id")
                    break
            if action is None:
                i += 1
                continue
            source: dict[str, Any] = {}
            if action in (EsBulkAction.INDEX, EsBulkAction.CREATE):
                i += 1
                if i < len(lines) and lines[i].strip():
                    try:
                        source = json.loads(lines[i])
                    except json.JSONDecodeError:
                        pass
            elif action == EsBulkAction.UPDATE:
                i += 1
                if i < len(lines) and lines[i].strip():
                    try:
                        update_doc = json.loads(lines[i])
                        source = update_doc.get("doc", update_doc)
                    except json.JSONDecodeError:
                        pass
            events.append(LogEvent(
                source=LogSource.ES_BULK,
                es_action_meta=EsBulkActionMeta(
                    action=action,
                    index=index_name,
                    doc_id=doc_id,
                ),
                es_source=source,
            ))
            i += 1
        return EventLogDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.LSDM,
            source=LogSource.ES_BULK,
            events=events,
            media_type=cast(MediaType, MEDIA_TYPES.get("es_bulk")),
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> EventLogDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)
