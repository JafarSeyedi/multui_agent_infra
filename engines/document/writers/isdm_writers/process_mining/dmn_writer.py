import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast, BinaryIO, TextIO

from engines.document.writers.base import BaseKnowledgeWriter, BaseDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import ProcessMiningDocument


DMN_NS = 'http://www.omg.org/spec/DMN/20180521/MODEL/'
DI_NS = 'http://www.omg.org/spec/DMN/20180521/DMNDI/'
DC_NS = 'http://www.omg.org/spec/DMN/20180521/DC/'


class DmnWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["dmn_xml"]

    def can_write(self, document) -> bool:
        return isinstance(document, ProcessMiningDocument)

    async def write(self, document: ProcessMiningDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        root = ET.Element(f'{{{DMN_NS}}}definitions')
        root.set('id', options.get('id', 'definitions'))
        root.set('name', options.get('name', 'Decision'))
        root.set('xmlns:dmndi', DI_NS)
        root.set('xmlns:dc', DC_NS)
        decision = ET.SubElement(root, f'{{{DMN_NS}}}decision')
        decision.set('id', 'decision1')
        decision.set('name', 'Decision')
        ET.indent(ET.ElementTree(root), space='  ')
        xml_bytes = ET.tostring(root, encoding='unicode').encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                cast(BinaryIO, destination).write(xml_bytes)
        return xml_bytes


can_write = DmnWriter.can_write
write = DmnWriter.write
