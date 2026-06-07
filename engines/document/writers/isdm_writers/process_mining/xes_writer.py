import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast, BinaryIO, TextIO

from engines.document.writers.base import BaseKnowledgeWriter, BaseDocument
from engines.document.models.media_types import MEDIA_TYPES
from engines.document.models.isdm_models import ProcessMiningDocument


XES_NS = 'http://www.xes-standard.org/'


ET.register_namespace('', XES_NS)
ET.register_namespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance')


class XesWriter(BaseKnowledgeWriter):
    supported_format = MEDIA_TYPES["xes_xml"]

    def can_write(self, document) -> bool:
        return isinstance(document, ProcessMiningDocument)

    async def write(self, document: ProcessMiningDocument, destination: str | Path | BinaryIO | TextIO | None = None, **options: Any) -> bytes:
        if not document.xes_log:
            raise ValueError("No XES log data to write")
        log = document.xes_log
        root = ET.Element(f'{{{XES_NS}}}log')
        root.set('xes.version', '1.0')
        root.set('xes.features', '')
        if log.extensions:
            for ext in log.extensions:
                ext_elem = ET.SubElement(root, f'{{{XES_NS}}}extension')
                ext_elem.set('name', ext.name)
                ext_elem.set('prefix', ext.prefix)
                ext_elem.set('uri', ext.uri)
        if log.classifiers:
            for cls in log.classifiers:
                cls_elem = ET.SubElement(root, f'{{{XES_NS}}}classifier')
                cls_elem.set('name', cls.name)
                cls_elem.set('keys', ','.join(cls.keys))
        for trace in log.traces:
            trace_elem = ET.SubElement(root, f'{{{XES_NS}}}trace')
            if trace.attributes:
                for attr in trace.attributes:
                    attr_elem = ET.SubElement(trace_elem, f'{{{XES_NS}}}string')
                    attr_elem.set('key', attr.key)
                    attr_elem.set('value', attr.value)
            for event in trace.events:
                event_elem = ET.SubElement(trace_elem, f'{{{XES_NS}}}event')
                if event.attributes:
                    for attr in event.attributes:
                        tag = f'{{{XES_NS}}}{attr.typ or "string"}'
                        event_attr = ET.SubElement(event_elem, tag)
                        event_attr.set('key', attr.key)
                        event_attr.set('value', attr.value)
        ET.indent(ET.ElementTree(root), space='  ')
        xml_bytes = ET.tostring(root, encoding='unicode').encode('utf-8')
        if destination is not None:
            if isinstance(destination, (str, Path)):
                Path(destination).write_bytes(xml_bytes)
            else:
                cast(BinaryIO, destination).write(xml_bytes)
        return xml_bytes


can_write = XesWriter.can_write
write = XesWriter.write
