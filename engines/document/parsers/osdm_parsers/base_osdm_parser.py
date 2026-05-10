# engines/document/parsers/osdm_parsers/base_osdm_parser.py
"""
Base class for all OSDM format parsers.
Handles common OSDM infrastructure: version detection, source tracking,
and shared helper methods for XML/JSON parsing.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.osdm_models import BaseOSDMDocument
from ..base import BaseDocumentParser, ParseOptions


class BaseOSDMParser(BaseDocumentParser):
    """
    Common base for parsers that produce a BaseOSDMDocument subclass.

    Subclasses must implement:
    - `_parse_to_document(data, source_name, options) -> BaseOSDMDocument`
    - `supported_extensions` (class attribute)
    """

    name: str = "osdm"
    supported_extensions: tuple[str, ...] = ()

    def __init__(self, options: ParseOptions | None = None):
        self.options = options or ParseOptions()

    # ── Core parse methods ──────────────────────────────────────
    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BaseOSDMDocument:
        opts = options or self.options
        doc = await self._parse_to_document(data, source_name, opts)
        doc.document_id = document_id
        doc.title = source_name or document_id
        doc.metadata = metadata or {}
        doc.file_extension = Path(source_name).suffix if source_name else ""
        doc.source_file = source_name
        return doc

    async def parse_path(
        self,
        path: str | Path,
        document_id: str,
        metadata: dict[str, Any] | None = None,
        options: ParseOptions | None = None,
    ) -> BaseOSDMDocument:
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
    ) -> BaseOSDMDocument:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    # ── Abstract method ─────────────────────────────────────────
    @abstractmethod
    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> BaseOSDMDocument:
        """
        Subclasses must implement this to produce the appropriate document type.
        """
        ...

    # ── Common helpers ──────────────────────────────────────────
    def _detect_version(self, source_name: str) -> str:
        """Try to detect version from filename (e.g., 'diagram_v2.1.0.bpmn')."""
        import re
        match = re.search(r"_v(\d+\.\d+\.\d+)", source_name)
        return match.group(1) if match else "1.0.0"