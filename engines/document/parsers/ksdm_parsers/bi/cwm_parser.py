import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, BinaryIO, TextIO

from engines.document.parsers.base import BaseDocumentParser, ParseResult
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.ksdm_models import (
    BiAggregationDocument,
    BiAggregationKind,
    CwmAssociation,
    CwmAttribute,
    CwmClass,
    CwmSchema,
)


class CwmParser(BaseDocumentParser):
    supported_format = MEDIA_TYPES["cwm_xmi"]

    def can_parse(self, source: str | Path) -> bool:
        if isinstance(source, str) and source.endswith(('.cwm', '.cwm.xml', '.xmi')):
            return True
        try:
            data = Path(source).read_bytes()[:200] if Path(source).exists() else b""
            return b"CWM" in data or b"<XMI" in data or b"<cwm:" in data
        except Exception:
            return False

    def parse(self, source: str | Path | BinaryIO | TextIO, **options: Any) -> ParseResult:
        try:
            if isinstance(source, (str, Path)):
                data: bytes = Path(source).read_bytes()
            elif hasattr(source, 'read'):
                _raw = source.read()
                data = _raw.encode('utf-8') if isinstance(_raw, str) else _raw
            else:
                raise Exception("Unsupported source type")
            root = ET.fromstring(data)
            ns = {'cwm': 'http://www.omg.org/spec/CWM/', 'xmi': 'http://www.omg.org/XMI'}
            schema = CwmSchema(name=root.get('name'), package=root.get('package'))
            for cls_elem in root.findall('.//cwm:Class', ns) + root.findall('.//Class', ns):
                cls = CwmClass(
                    name=cls_elem.get('name', ''),
                    package=cls_elem.get('package', schema.package),
                    attributes=[]
                )
                # Fix: iterate over the element's children directly
                for child in cls_elem:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    if tag == 'Attribute' or child.tag in (f'{{{ns["cwm"]}}}Attribute', 'Attribute'):
                        attr = CwmAttribute(
                            name=child.get('name', ''),
                            data_type=child.get('type', child.get('dataType', '')),
                            nullable=child.get('nullable', 'true').lower() != 'false',
                            is_key=child.get('isKey', 'false').lower() == 'true'
                        )
                        cls.attributes.append(attr)
                schema.classes.append(cls)
            for assoc_elem in root.findall('.//cwm:Association', ns) + root.findall('.//Association', ns):
                schema.associations.append(CwmAssociation(
                    name=assoc_elem.get('name', ''),
                    source_class=assoc_elem.get('sourceClass', assoc_elem.get('source', '')),
                    target_class=assoc_elem.get('targetClass', assoc_elem.get('target', '')),
                    multiplicity=assoc_elem.get('multiplicity')
                ))
            doc = BiAggregationDocument(bi_aggregation_kind=BiAggregationKind.CWM_WAREHOUSE, cwm_schema=schema)
            return ParseResult(document=doc)
        except Exception as e:
            raise Exception(f"CWM parse failed: {e}")
