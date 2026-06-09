from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, BinaryIO, TextIO, cast

from engines.document.models.ksdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    CwmSchema,
)
from engines.document.writers.base import BaseDocument, BaseDocumentWriter


class CwmWriter(BaseDocumentWriter):
    supported_format = None

    def can_write(self, document) -> bool:
        return isinstance(document, BiAggregationDocument) and document.bi_aggregation_kind == BiAggregationKind.CWM_WAREHOUSE

    async def write(self, document: BaseDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        schema = getattr(document, 'cwm_schema', CwmSchema())
        root = ET.Element('XMI')
        root.set('xmlns:xmi', 'http://www.omg.org/XMI')
        root.set('xmlns:cwm', 'http://www.omg.org/spec/CWM/')
        if schema.name:
            root.set('name', schema.name)
        if schema.package:
            root.set('package', schema.package)
        for cls in schema.classes:
            cls_elem = ET.SubElement(root, 'Class')
            cls_elem.set('name', cls.name)
            if cls.package:
                cls_elem.set('package', cls.package)
            for attr in cls.attributes:
                attr_elem = ET.SubElement(cls_elem, 'Attribute')
                attr_elem.set('name', attr.name)
                attr_elem.set('type', attr.data_type)
                if not attr.nullable:
                    attr_elem.set('nullable', 'false')
                if attr.is_key:
                    attr_elem.set('isKey', 'true')
        for assoc in schema.associations:
            assoc_elem = ET.SubElement(root, 'Association')
            assoc_elem.set('name', assoc.name)
            assoc_elem.set('sourceClass', assoc.source_class)
            assoc_elem.set('targetClass', assoc.target_class)
            if assoc.multiplicity:
                assoc_elem.set('multiplicity', assoc.multiplicity)
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
        return [".xmi", ".cwm"]
