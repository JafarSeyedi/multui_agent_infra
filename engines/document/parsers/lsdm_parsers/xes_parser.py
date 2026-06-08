from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, cast
from xml.etree import ElementTree as ET

from engines.document.models.lsdm_models import (
    EventLogDocument,
    LogAttribute,
    LogEvent,
    LogSource,
    XesClassifier,
    XesExtension,
    XesTrace,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from engines.document.models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions

XES_NS = "http://www.xes-standard.org/"


class XesParser(BaseDocumentParser):
    name = "xes_parser"
    supported_extensions = [".xes"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        root = ET.fromstring(data)
        if root.tag != f"{{{XES_NS}}}log":
            raise ValueError("Root element must be <log>")
        extensions = []
        classifiers = []
        global_attrs = []
        traces = []
        for child in root:
            tag = child.tag
            if tag == f"{{{XES_NS}}}extension":
                extensions.append(XesExtension(
                    name=child.get("name", ""),
                    prefix=child.get("prefix", ""),
                    uri=child.get("uri", ""),
                ))
            elif tag == f"{{{XES_NS}}}classifier":
                classifiers.append(XesClassifier(
                    name=child.get("name", ""),
                    keys=child.get("keys", "").split(",") if child.get("keys") else [],
                ))
            elif tag == f"{{{XES_NS}}}string" or tag.endswith("}string"):
                global_attrs.append(LogAttribute(
                    key=child.get("key", ""),
                    value=child.get("value", ""),
                    type="string",
                ))
            elif tag == f"{{{XES_NS}}}trace":
                traces.append(self._parse_trace(child))
        events = []
        for trace in traces:
            for attr in trace.events:
                events.append(LogEvent(
                    id=attr.key,
                    timestamp=None,
                    source=LogSource.XES,
                    attributes=[attr],
                ))
        return EventLogDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.LSDM,
            source=LogSource.XES,
            events=events,
            traces=traces,
            extensions=extensions,
            classifiers=classifiers,
            attributes=global_attrs,
            media_type=cast(MediaType, MEDIA_TYPES.get("xes_xml")),
        )

    async def parse_path(
        self, path: str | Path, document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        p = Path(path)
        return await self.parse_bytes(p.read_bytes(), document_id, p.name)

    async def parse_stream(self, stream, document_id: str,
                           source_name: str, metadata=None, options=None) -> EventLogDocument:
        data = b"".join([chunk async for chunk in stream])
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    def _parse_trace(self, elem: ET.Element) -> XesTrace:
        trace_id = elem.get("id") or elem.get("key")
        attributes: list[LogAttribute] = []
        events: list[LogAttribute] = []
        for child in elem:
            tag = child.tag
            key = child.get("key", "")
            value = child.get("value", "")
            attr_type = tag.split("}")[-1] if "}" in tag else tag
            if tag == f"{{{XES_NS}}}event":
                for event_child in child:
                    ek = event_child.get("key", "")
                    ev = event_child.get("value", "")
                    etype = event_child.tag.split("}")[-1] if "}" in event_child.tag else event_child.tag
                    events.append(LogAttribute(key=ek, value=ev, type=etype))
            else:
                attributes.append(LogAttribute(key=key, value=value, type=attr_type))
        return XesTrace(id=trace_id, attributes=attributes, events=events)
