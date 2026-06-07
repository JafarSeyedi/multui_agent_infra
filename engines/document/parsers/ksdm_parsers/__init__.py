"""KSDM (Knowledge Graph Standard Document Model) parsers."""

from __future__ import annotations

from datetime import datetime

from engines.document.models.ksdm_models import (
    Entity,
    EntityType,
    KSDMDocument,
    Relation,
    RelationType,
)
from engines.document.models.media_types import (
    DocumentFormat,
    MediaContentKind,
    MediaRawType,
    MediaType,
)
from engines.document.models.standard import DocumentStandard

_KSDM_MEDIA_TYPE = MediaType(
    mime="application/x-ksdm+json",
    format=DocumentFormat.UNKNOWN,
    standard=DocumentStandard.KSDM,
    extensions=[".ksdm.json", ".ksdm.yaml", ".ksdm.yml", ".csv"],
    kind=MediaContentKind.STRUCTURED,
    raw_type=MediaRawType.TEXT,
)


class _BaseKSDMParser:
    """Base class for KSDM parsers."""
    
    @property
    def supported_extensions(self) -> list[str]:
        return []
    
    def supports_extension(self, ext: str) -> bool:
        return ext in self.supported_extensions
    
    async def parse_bytes(self, data: bytes, document_id: str, source_file: str) -> KSDMDocument:
        raise NotImplementedError


class KSDMJSONParser(_BaseKSDMParser):
    """Parser for KSDM JSON format."""
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".ksdm.json"]
    
    async def parse_bytes(self, data: bytes, document_id: str, source_file: str) -> KSDMDocument:
        import json
        raw = json.loads(data)
        entities = [
            Entity(
                id=e["id"],
                type=EntityType(e["type"]),
                label=e.get("label", ""),
                properties=e.get("properties", {}),
                embedding=e.get("embedding"),
            )
            for e in raw.get("entities", [])
        ]
        relations = [
            Relation(
                id=r["id"],
                source_id=r["source_id"],
                target_id=r["target_id"],
                type=RelationType(r["type"]),
                weight=r.get("weight"),
                timestamp=r.get("timestamp"),
            )
            for r in raw.get("relations", [])
        ]
        return KSDMDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.KSDM,
            media_type=_KSDM_MEDIA_TYPE,
            entities=entities,
            relations=relations,
        )


class KSDMYAMLParser(_BaseKSDMParser):
    """Parser for KSDM YAML format."""
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".ksdm.yaml", ".ksdm.yml"]
    
    async def parse_bytes(self, data: bytes, document_id: str, source_file: str) -> KSDMDocument:
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
            media_type=_KSDM_MEDIA_TYPE,
            entities=entities,
            relations=relations,
        )


class CSVGraphParser(_BaseKSDMParser):
    """Parser for CSV graph format."""
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".csv"]
    
    async def parse_bytes(self, data: bytes, document_id: str, source_file: str) -> KSDMDocument:
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
            media_type=_KSDM_MEDIA_TYPE,
            entities=entities,
            relations=relations,
        )


class RMLYAMLParser(_BaseKSDMParser):
    """Parser for RML YAML format."""
    
    @property
    def supported_extensions(self) -> list[str]:
        return [".rml.yaml", ".rml.yml"]
    
    async def parse_bytes(self, data: bytes, document_id: str, source_file: str) -> KSDMDocument:
        import yaml
        raw = yaml.safe_load(data)
        return KSDMDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.KSDM,
            media_type=_KSDM_MEDIA_TYPE,
            entities=[],
            relations=[],
            ontology={"rml_mapping": raw.get("mappings", [])},
        )
