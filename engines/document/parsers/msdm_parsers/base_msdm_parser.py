# engines/document/parsers/msdm_parsers/base_msdm_parser.py
"""
Base class for all MSDM format parsers.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.msdm_models import MSDMDocument, Entity, Attribute, Constraint, DataType, ScalarType
from ..base import BaseDocumentParser
from ..base import ParseOptions


class BaseMSDMParser(BaseDocumentParser):
    """Common base for parsers that produce an MSDMDocument."""

    def __init__(self, options: ParseOptions | None = None):
        self.options = options or ParseOptions()

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> MSDMDocument:
        opts = options or self.options
        doc = await self._parse_to_msdm(data, source_name, opts)
        doc.document_id = document_id
        doc.title = source_name or document_id
        doc.metadata = metadata or {}
        doc.file_extension = Path(source_name).suffix if source_name else ""
        # Media type detection is left to the concrete parser or the registry
        return doc

    async def parse_path(
        self,
        path: str | Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> MSDMDocument:
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(data, document_id, file_path.name, metadata, options)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> MSDMDocument:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    @abstractmethod
    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        """
        Override in each format parser.
        Must return a fully populated MSDMDocument.
        """
        ...
    # ------------------------------------------------------------------
    # Reference resolution (second pass)
    # ------------------------------------------------------------------
    def resolve_references(self, doc: MSDMDocument) -> None:
        """Resolve string references to actual entity objects."""
        entity_map = {e.name: e for e in doc.entities}
        # Also map by possible aliases (e.g., xmi:id not used here)

        for entity in doc.entities:
            # Resolve extends
            extends_str = entity.extends_ref_id
            if extends_str and extends_str in entity_map:
                entity.extends = entity_map[extends_str]
            augments_str = entity.augments_ref_id
            if augments_str and augments_str in entity_map:
                entity.augments = entity_map[augments_str]
            # Resolve implements
            for impl_str in entity.implements_ref_ids:
                if impl_str in entity_map:
                    entity.implements.append(entity_map[impl_str])

        for entity in doc.entities:
            for c in entity.constraints:
                self._resolve_constraint(c, entity_map)

        # Resolve DataType ref_entity from string to Entity
        for entity in doc.entities:
            for attr in entity.attributes:
                self._resolve_attribute(attr, entity_map)

        for rel in doc.relationships:
            from_str = rel.from_ref_id
            if from_str and from_str in entity_map:
                rel.from_entity = entity_map[from_str]
            to_str = rel.to_ref_id
            if to_str and to_str in entity_map:
                rel.to_entity = entity_map[to_str]
            
    def _resolve_attribute(self, attr: Attribute, entity_map: dict[str, Entity]) -> None:
        template_str = attr.template_id
        if template_str and template_str in entity_map:
            attr.template = entity_map[template_str]

        self._resolve_data_type(attr.data_type, entity_map)
        for c in attr.constraints:
            self._resolve_constraint(c, entity_map)

    def _resolve_constraint(self, c: Constraint, entity_map: dict[str, Entity]) -> None:
        if c.ref_entity_id:
            ref_name = c.ref_entity_id
            if isinstance(ref_name, str) and ref_name in entity_map:
                c.ref_entity = entity_map[ref_name]

    def _resolve_data_type(self, dt: DataType, entity_map: dict[str, Entity]) -> None:
        if dt.base == ScalarType.REF and dt.ref_entity_id:
            ref_name = dt.ref_entity_id
            if isinstance(ref_name, str) and ref_name in entity_map:
                dt.ref_entity = entity_map[ref_name]
        if dt.element_type:
            self._resolve_data_type(dt.element_type, entity_map)
        if dt.key_type:
            self._resolve_data_type(dt.key_type, entity_map)
        if dt.value_type:
            self._resolve_data_type(dt.value_type, entity_map)
