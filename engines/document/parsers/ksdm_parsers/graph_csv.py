from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast

from engines.document.models.ksdm_models import (
    Entity,
    EntityType,
    KSDMDocument,
    Relation,
    RelationType,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from engines.document.models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions


class CSVGraphParser(BaseDocumentParser):
    name = "ksdm_csv_graph"
    supported_extensions = [".csv"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMDocument:
        import csv
        import io
        text = data.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text))
        entity_ids: set[str] = set()
        relations: list[Relation] = []
        for row in reader:
            source_id = row["source_id"]
            target_id = row["target_id"]
            entity_ids.add(source_id)
            entity_ids.add(target_id)
            ts_raw = row.get("timestamp")
            relations.append(Relation(
                id=f"rel_{len(relations)}",
                source_id=source_id,
                target_id=target_id,
                type=RelationType(row.get("relation_type", "related")),
                weight=float(row["weight"]) if row.get("weight") else 1.0,
                timestamp=datetime.fromisoformat(ts_raw) if ts_raw else None,
            ))
        entities = [Entity(id=eid, type=EntityType.UNKNOWN, label=eid) for eid in entity_ids]
        return KSDMDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.KSDM,
            media_type=cast(MediaType, MEDIA_TYPES.get("csv")),
            entities=entities,
            relations=relations,
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name, metadata, options)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> KSDMDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)
