from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from engines.document.models.lsdm_models import (
    CefSeverity,
    EventLogDocument,
    LogEvent,
    LogSource,
)
from engines.document.models.media_types import MediaType, MEDIA_TYPES
from engines.document.models.standard import DocumentStandard
from ..base import BaseDocumentParser, ParseOptions

CEF_PATTERN = re.compile(
    r"CEF:(?P<cef_version>\d+)\|"
    r"(?P<device_vendor>[^|]*)\|"
    r"(?P<device_product>[^|]*)\|"
    r"(?P<device_version>[^|]*)\|"
    r"(?P<signature_id>[^|]*)\|"
    r"(?P<name>[^|]*)\|"
    r"(?P<severity>\d+)\|"
    r"(?P<extension>.*)"
)


class CefParser(BaseDocumentParser):
    name = "cef_parser"
    supported_extensions = [".cef"]

    async def parse_bytes(
        self, data: bytes, document_id: str, source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> EventLogDocument:
        text = data.decode("utf-8")
        events: list[LogEvent] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            event = self._parse_line(line)
            if event:
                events.append(event)
        return EventLogDocument(
            document_id=document_id,
            title="",
            kind=DocumentStandard.LSDM,
            source=LogSource.CEF,
            events=events,
            media_type=cast(MediaType, MEDIA_TYPES.get("cef")),
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

    def _parse_line(self, line: str) -> LogEvent | None:
        match = CEF_PATTERN.match(line)
        if not match:
            return None
        severity_map = {
            "0": CefSeverity.LOW, "1": CefSeverity.LOW, "2": CefSeverity.LOW,
            "3": CefSeverity.MEDIUM, "4": CefSeverity.MEDIUM,
            "5": CefSeverity.MEDIUM,
            "6": CefSeverity.HIGH, "7": CefSeverity.HIGH,
            "8": CefSeverity.CRITICAL, "9": CefSeverity.CRITICAL,
            "10": CefSeverity.CRITICAL,
        }
        severity_str = match.group("severity")
        severity = severity_map.get(severity_str, CefSeverity.UNKNOWN)
        extensions: dict[str, str] = {}
        ext_text = match.group("extension")
        if ext_text:
            for part in ext_text.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    extensions[k] = v
        return LogEvent(
            source=LogSource.CEF,
            cef_device_vendor=match.group("device_vendor"),
            cef_device_product=match.group("device_product"),
            cef_device_version=match.group("device_version"),
            cef_signature_id=match.group("signature_id"),
            cef_name=match.group("name"),
            cef_severity=severity,
            cef_extensions=extensions,
            raw=line,
        )
