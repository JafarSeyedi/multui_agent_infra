# engines/document/parsers/tsdm_parsers/base_tsdm_parser.py
from abc import abstractmethod
from typing import Optional, Dict, Any, Union, AsyncIterator
from pathlib import Path
from ..base import BaseDocumentParser, ParseOptions
from ...models.tsdm_models import TSDMDocument

class BaseTSDMParser(BaseDocumentParser):
    name = "tsdm"
    supported_extensions = (".tsdm.json", ".tools.json")

    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                          metadata: Optional[Dict[str, Any]] = None,
                          options: Optional[ParseOptions] = None) -> TSDMDocument:
        opts = options or ParseOptions()
        doc = await self._parse_to_tsdm(data, source_name, opts)
        doc.document_id = document_id
        doc.title = source_name or document_id
        doc.metadata = metadata or {}
        doc.file_extension = Path(source_name).suffix if source_name else ""
        return doc

    async def parse_path(self, path, document_id, metadata=None, options=None):
        file_path = Path(path)
        data = file_path.read_bytes()
        return await self.parse_bytes(data, document_id, file_path.name, metadata, options)

    async def parse_stream(self, stream, document_id, source_name, metadata=None, options=None):
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        data = b"".join(chunks)
        return await self.parse_bytes(data, document_id, source_name, metadata, options)

    @abstractmethod
    async def _parse_to_tsdm(self, data: bytes, source_name: str, options: ParseOptions) -> TSDMDocument:
        ...