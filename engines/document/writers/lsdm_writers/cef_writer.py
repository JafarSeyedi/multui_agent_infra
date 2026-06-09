from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast

from engines.document.models.lsdm_models import CefSeverity, EventLogDocument
from engines.document.writers.base import BaseDocument, BaseDocumentWriter, WriteOptions

SEVERITY_MAP = {
    CefSeverity.LOW: "3",
    CefSeverity.MEDIUM: "5",
    CefSeverity.HIGH: "7",
    CefSeverity.CRITICAL: "9",
    CefSeverity.UNKNOWN: "0",
}


class CefWriter(BaseDocumentWriter):
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield await self.write(cast(EventLogDocument, document))

    async def write(self, document: BaseDocument) -> bytes:
        doc = cast(EventLogDocument, document)
        lines: list[str] = []
        for event in doc.events:
            vendor = event.cef_device_vendor or "Unknown"
            product = event.cef_device_product or "Unknown"
            version = event.cef_device_version or "0"
            sig_id = event.cef_signature_id or "0"
            name = event.cef_name or "Event"
            severity = SEVERITY_MAP.get(event.cef_severity, "0")
            ext_parts = [f"{k}={v}" for k, v in event.cef_extensions.items()]
            ext_str = " ".join(ext_parts) if ext_parts else ""
            lines.append(f"CEF:0|{vendor}|{product}|{version}|{sig_id}|{name}|{severity}|{ext_str}")
        return "\n".join(lines).encode("utf-8")

    async def write_to_file(self, document: BaseDocument, target: Path, options: dict[str, Any] | None = None) -> None:
        target.write_bytes(await self.write(cast(EventLogDocument, document)))

    def get_supported_media_types(self) -> list[str]:
        return ["application/x-cef"]

    def get_supported_extensions(self) -> list[str]:
        return [".cef"]