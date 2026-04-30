# engines/document/parsers/msdm_parsers/base_msdm_parser.py
"""
Base class for all MSDM format parsers.
"""

from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Any, Dict, Union, AsyncIterator

from ..base import BaseDocumentParser, ParseOptions
from ...models.msdm_models import MSDMDocument


class BaseMSDMParser(BaseDocumentParser):
    """Common base for parsers that produce an MSDMDocument."""

    def __init__(self, options: Optional[ParseOptions] = None):
        self.options = options or ParseOptions()

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> MSDMDocument:
        opts = options or self.options
        doc = await self._parse_to_msdm(data, source_name, opts)
        doc.document_id = document_id
        doc.title = source_name or document_id
        doc.metadata = metadata or {}
        doc.file_extension = Path(source_name).suffix if source_name else ""
        # Media type detection is left to the concrete parser or the registry
        return doc

    async def parse_path(
        self,
        path: Union[str, Path],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> MSDMDocument:
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
    ) -> MSDMDocument:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    @abstractmethod
    async def _parse_to_msdm(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> MSDMDocument:
        """
        Override in each format parser.
        Must return a fully populated MSDMDocument.
        """
        ...