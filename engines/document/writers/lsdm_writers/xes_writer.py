from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from engines.document.models.lsdm_models import EventLogDocument, LogSource
from engines.document.writers.base import BaseDocumentWriter, WriteOptions

XES_NS = "http://www.xes-standard.org/"


class XesWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: EventLogDocument) -> AsyncIterator[bytes]:
        yield await self.write(document)

    async def write(self, document: EventLogDocument) -> bytes:
        root = ET.Element(f"{{{XES_NS}}}log")
        root.set("xes.version", "1.0")
        root.set("xes.features", "")
        for ext in document.extensions:
            elem = ET.SubElement(root, f"{{{XES_NS}}}extension")
            elem.set("name", ext.name)
            elem.set("prefix", ext.prefix)
            elem.set("uri", ext.uri)
        for cls in document.classifiers:
            elem = ET.SubElement(root, f"{{{XES_NS}}}classifier")
            elem.set("name", cls.name)
            elem.set("keys", ",".join(cls.keys))
        if document.traces:
            for trace in document.traces:
                trace_elem = ET.SubElement(root, f"{{{XES_NS}}}trace")
                if trace.id:
                    trace_elem.set("id", trace.id)
                for attr in trace.attributes:
                    child = ET.SubElement(trace_elem, f"{{{XES_NS}}}string")
                    child.set("key", attr.key)
                    child.set("value", attr.value)
                for event_attr in trace.events:
                    event_elem = ET.SubElement(trace_elem, f"{{{XES_NS}}}event")
                    child = ET.SubElement(event_elem, f"{{{XES_NS}}}string")
                    child.set("key", event_attr.key)
                    child.set("value", event_attr.value)
        else:
            for event in document.events:
                trace_elem = ET.SubElement(root, f"{{{XES_NS}}}trace")
                event_elem = ET.SubElement(trace_elem, f"{{{XES_NS}}}event")
                for attr in event.attributes:
                    child = ET.SubElement(event_elem, f"{{{XES_NS}}}string")
                    child.set("key", attr.key)
                    child.set("value", attr.value)
        ET.indent(ET.ElementTree(root), space="  ")
        return ET.tostring(root, encoding="unicode").encode("utf-8")

    async def write_to_file(self, document: EventLogDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(document))

    def get_supported_media_types(self) -> list[str]:
        return ["application/xml"]

    def get_supported_extensions(self) -> list[str]:
        return [".xes"]
