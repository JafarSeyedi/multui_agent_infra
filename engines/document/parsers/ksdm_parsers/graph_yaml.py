from __future__ import annotations

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


class KSDMYAMLParser(BaseDocumentParser):
    name = "ksdm_yaml"
    supported_extensions = [".ksdm.yaml", ".ksdm.yml"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> KSDMDocument:
        import yaml
        raw = yaml.safe_load(data)
        entities = [
            Entity(
                id=e["id"],
                type=EntityType(e["type"]),
                label=e.get("label", ""),
                properties=e.get("properties", {}),
            )
            for e in raw.get("entities", [])
        ]
        relations = [
            Relation(
                id=r["id"],
                source_id=r["source_id"],
                target_id=r["target_id"],
                type=RelationType(r["type"]),
            )
            for r in raw.get("relations", [])
        ]
        return KSDMDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.KSDM,
            media_type=cast(MediaType, MEDIA_TYPES.get("yaml")),
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
