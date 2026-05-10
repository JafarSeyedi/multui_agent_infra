# engines/document/parsers/base.py
from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from collections.abc import Iterable
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..models.base import BaseDocument

class ParseOptions(BaseModel):
    """Options for document parsing across all standards."""

    # General options
    encoding: str = "utf-8"
    strict: bool = True
    max_depth: int | None = None
    max_size_bytes: int | None = None

    # DSDM-specific options
    preserve_order: bool = True  # For JSON/XML element order
    parse_comments: bool = False  # For JSON/YAML comments
    parse_metadata: bool = True  # Include schema/namespace info
    binary_encoding: str = "base64"  # How to encode binary data

    # USDM-specific options
    extract_tables: bool = True
    preserve_layout: bool = False
    include_empty_pages: bool = False
    password: str | None = None

    # ESDM-specific options
    sheet_names: list[str] | None = None
    header_row: int = 0
    skip_rows: int = 0

    # CSDM-specific options
    include_metadata: bool = True
    layer_filter: list[str] | None = None

    log_level: str | None = None

    # Custom extensions
    custom: dict[str, Any] = {}
    additional_options: dict[str, Any] = {}

    unsafe_operations_allowed: bool = False


class BaseDocumentParser(ABC):
    """Shared parser contract for document formats."""
    name: str = "base"
    supported_extensions: Sequence[str] = ()

    @abstractmethod
    async def parse_bytes(self, data: bytes, document_id: str, source_name: str,
                         metadata: dict[str, Any] | None = None,
                         options: ParseOptions | None = None) -> BaseDocument:
        pass


    @abstractmethod
    async def parse_path(self, path: str | Path, document_id: str,
                        metadata: dict[str, Any] | None = None,
                        options: ParseOptions | None = None) -> BaseDocument:
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
                          source_name: str, metadata: dict[str, Any] | None = None,
                          options: ParseOptions | None = None) -> BaseDocument:
        """Parse from a stream of bytes."""

    def supports_extension(self, extension: str) -> bool:
        return extension.lower() in {item.lower() for item in self.supported_extensions}

    def iter_supported_extensions(self) -> Iterable[str]:
        return tuple(self.supported_extensions)