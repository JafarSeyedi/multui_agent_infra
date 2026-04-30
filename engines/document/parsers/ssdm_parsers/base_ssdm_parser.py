# engines/document/parsers/ssdm_parsers/base_ssdm_parser.py
"""
Base class for all SSDM (Service Standard Definition Model) parsers.
"""

from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Union, AsyncIterator

from ..base import BaseDocumentParser, ParseOptions
from ...models.ssdm_models import SSDM_DOCUMENT
from ...models.base import BaseDocument


class BaseSSDMParser(BaseDocumentParser):
    """
    Common base for parsers that produce an SSDM_DOCUMENT.

    Subclasses must implement:
    - `_parse_to_document(data, source_name, options) -> SSDM_DOCUMENT`
    - `supported_extensions` (class attribute)
    """

    name: str = "ssdm"
    supported_extensions: tuple[str, ...] = ()

    def __init__(self, options: Optional[ParseOptions] = None):
        self.options = options or ParseOptions()

    # ── Core parse methods ──────────────────────────────────────
    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> SSDM_DOCUMENT:
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
        path: Union[str, Path],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> SSDM_DOCUMENT:
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(data, document_id, file_path.name, metadata, options)

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> SSDM_DOCUMENT:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    # ── Abstract method ─────────────────────────────────────────
    @abstractmethod
    async def _parse_to_document(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> SSDM_DOCUMENT:
        """
        Subclasses must implement this to produce an SSDM_DOCUMENT.
        """
        ...

    # ── Common helpers ──────────────────────────────────────────
    def _detect_version(self, source_name: str) -> str:
        """Try to detect version from filename (e.g., 'api_v2.0.0.yaml')."""
        import re
        match = re.search(r"_v(\d+\.\d+\.\d+)", source_name)
        return match.group(1) if match else "1.0.0"

    def _create_base_document(self, source_name: str, options: ParseOptions) -> SSDM_DOCUMENT:
        """Create a new SSDM_DOCUMENT with default metadata."""
        doc = SSDM_DOCUMENT(
            title=Path(source_name).stem,
            version=self._detect_version(source_name),
        )
        return doc