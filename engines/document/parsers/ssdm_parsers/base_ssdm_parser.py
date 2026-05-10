# engines/document/parsers/ssdm_parsers/base_ssdm_parser.py
"""
Base class for all SSDM (Service Standard Definition Model) parsers.
"""
from __future__ import annotations

from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from ...models.base import BaseDocument
from ...models.ssdm_models import SSDMDocument 
from ..base import BaseDocumentParser
from ..base import ParseOptions


class BaseSSDMParser(BaseDocumentParser):
    """
    Common base for parsers that produce an SSDMDocument .

    Subclasses must implement:
    - `_parse_to_document(data, source_name, options) -> SSDMDocument `
    - `supported_extensions` (class attribute)
    """

    name: str = "ssdm"
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
    ) -> SSDMDocument :
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
    ) -> SSDMDocument :
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
    ) -> SSDMDocument :
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    # ── Abstract method ─────────────────────────────────────────
    @abstractmethod
    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDMDocument :
        """
        Subclasses must implement this to produce an SSDMDocument .
        """
        ...

    # ── Common helpers ──────────────────────────────────────────
    def _detect_version(self, source_name: str) -> str:
        """Try to detect version from filename (e.g., 'api_v2.0.0.yaml')."""
        import re
        match = re.search(r"_v(\d+\.\d+\.\d+)", source_name)
        return match.group(1) if match else "1.0.0"
