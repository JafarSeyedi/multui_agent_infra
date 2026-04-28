# engines/document/parsers/spreadsheet_parser/base_spreadsheet_parser.py
from __future__ import annotations
from abc import abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Union, AsyncIterator
import io

from ...base import BaseDocumentParser, ParseOptions
from ....models.esdm_models import ESDMDocument, Workbook
from ....models.media_detection import detect_media_type


class BaseSpreadsheetParser(BaseDocumentParser):
    """
    Common base for all ESDM parsers.
    Subclasses implement _parse_to_workbook().
    """

    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> ESDMDocument:
        options = options or ParseOptions()
        # Detect media type from data (or use extension if available)
        media_type = detect_media_type(path=source_name, data=data)

        workbook = await self._parse_to_workbook(data, source_name, options)

        doc = ESDMDocument(
            title=source_name or document_id,
            document_id=document_id,
            media_type=media_type,
            file_extension=Path(source_name).suffix if source_name else "",
            metadata=metadata or {},
            workbook=workbook,
            raw_binary=None,  # or keep original bytes if needed
        )
        return doc

    async def parse_path(
        self,
        path: Union[str, Path],
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> ESDMDocument:
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(
            data=data,
            document_id=document_id,
            source_name=file_path.name,
            metadata=metadata,
            options=options,
        )

    async def parse_stream(
        self,
        stream: AsyncIterator[bytes],
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> ESDMDocument:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(
            data=data,
            document_id=document_id,
            source_name=source_name,
            metadata=metadata,
            options=options,
        )

    @abstractmethod
    async def _parse_to_workbook(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> Workbook:
        """Convert raw bytes into a populated Workbook model."""
        ...