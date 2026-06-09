from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    MondrianSchema,
)
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class MondrianSchemaWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, BiAggregationDocument) and document.bi_aggregation_kind == BiAggregationKind.MONDRIAN_SCHEMA

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        schema = getattr(document, 'mondrian_schema', MondrianSchema())
        root = ET.Element('Schema')
        root.set('xmlns', 'http://mondrian.sourceforge.net')
        root.set('name', schema.name or 'mondrian_schema')
        if schema.table:
            root.set('table', schema.table)
        for dim in schema.dimensions:
            cube_elem = ET.SubElement(root, 'Cube')
            cube_elem.set('name', dim.name)
            dim_elem = ET.SubElement(cube_elem, 'Dimension')
            dim_elem.set('name', dim.name)
            dim_elem.set('type', dim.type)
            if dim.hierarchy:
                h_elem = ET.SubElement(dim_elem, 'Hierarchy')
                h_elem.set('hasAll', 'true' if dim.hierarchy.has_all else 'false')
                if dim.hierarchy.primary_key:
                    h_elem.set('primaryKey', dim.hierarchy.primary_key)
                for lvl in dim.hierarchy.levels:
                    lvl_elem = ET.SubElement(h_elem, 'Level')
                    lvl_elem.set('name', lvl.name)
                    lvl_elem.set('table', lvl.table)
                    lvl_elem.set('column', lvl.column)
                    if lvl.name_column:
                        lvl_elem.set('nameColumn', lvl.name_column)
                    lvl_elem.set('uniqueMembers', 'true' if lvl.unique_members else 'false')
                    lvl_elem.set('levelType', lvl.level_type)
            for m in schema.measures:
                m_elem = ET.SubElement(cube_elem, 'Measure')
                m_elem.set('name', m.name)
                m_elem.set('column', m.column)
                m_elem.set('aggregator', m.aggregator_name)
                m_elem.set('visible', 'true' if m.visible else 'false')
        ET.indent(ET.ElementTree(root), space='  ')
        xml_bytes = ET.tostring(root, encoding='unicode').encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                cast(BinaryIO, destination).write(xml_bytes)
        return xml_bytes

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return [".mondrian.xml"]
