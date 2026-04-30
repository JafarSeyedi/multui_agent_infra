# engines/document/parsers/base.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any, Dict, Iterable, Sequence, Union, AsyncIterator
from pydantic import BaseModel


from ..models.base import BaseDocument

class ParseOptions(BaseModel):
    """Options for document parsing across all standards."""
    
    # General options
    encoding: str = "utf-8"
    strict: bool = False
    max_depth: Optional[int] = None
    max_size_bytes: Optional[int] = None
    
    # DSDM-specific options
    preserve_order: bool = True  # For JSON/XML element order
    parse_comments: bool = False  # For JSON/YAML comments
    parse_metadata: bool = True  # Include schema/namespace info
    binary_encoding: str = "base64"  # How to encode binary data
    
    # USDM-specific options
    extract_tables: bool = True
    preserve_layout: bool = False
    include_empty_pages: bool = False
    password: Optional[str] = None
    
    # ESDM-specific options
    sheet_names: Optional[list[str]] = None
    header_row: int = 0
    skip_rows: int = 0
    
    # CSDM-specific options
    include_metadata: bool = True
    layer_filter: Optional[list[str]] = None
    
    # Custom extensions
    custom: Dict[str, Any] = {}
    additional_options: Dict[str, Any] = {}
    
    unsafe_operations_allowed: bool = False


class BaseDocumentParser(ABC):
    """Shared parser contract for document formats."""
    name: str = "base"
    supported_extensions: Sequence[str] = ()

    @abstractmethod
    async def parse_bytes(self, data: bytes, document_id: str, source_name: str, 
                         metadata: Optional[Dict[str, Any]] = None, 
                         options: Optional[ParseOptions] = None) -> BaseDocument:
        pass

    
    @abstractmethod
    async def parse_path(self, path: Union[str, Path], document_id: str,
                        metadata: Optional[Dict[str, Any]] = None,
                        options: Optional[ParseOptions] = None) -> BaseDocument:
        file_path = Path(path)
        return await self.parse_bytes(
            data=file_path.read_bytes(),
            document_id=document_id,
            source_name=file_path.name,
            metadata=metadata,
            options=options,
        )

    @abstractmethod
    async def parse_stream(self, stream: AsyncIterator[bytes], document_id: str, 
                          source_name: str, metadata: Optional[Dict[str, Any]] = None,
                          options: Optional[ParseOptions] = None) -> BaseDocument:
        """Parse from a stream of bytes."""
        pass

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in {item.lower() for item in self.supported_extensions}

    def iter_supported_extensions(self) -> Iterable[str]:
        return tuple(self.supported_extensions)

