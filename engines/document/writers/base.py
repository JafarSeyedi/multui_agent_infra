# engines/document/writers/base.py
from __future__ import annotations

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from ..models.base import BaseDocument

class WriteOptions(BaseModel):
    """Options for document writing across all standards."""

    encoding: str = "utf-8"

    # USDM-specific options
    include_metadata: bool = True
    pretty_print: bool = False

    # Markdown-specific options
    heading_style: str = "atx"
    bullet_style: str = "-"
    code_block_style: str = "```"

    # Custom extensions
    custom: dict[str, Any] = {}


class WriteResult(BaseModel):
    success: bool = True
    data: bytes = b""
    metadata: dict[str, Any] = {}


class BaseDocumentWriter(ABC):
    """Base class for all document writers."""
    def __init__(self, options: WriteOptions | None = None):
        self.options = options or WriteOptions()

    @abstractmethod
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield b""

    @abstractmethod
    async def write(self, document: BaseDocument) -> bytes:
        pass

    @abstractmethod
    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        pass

    @abstractmethod
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""

    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""


class BaseKnowledgeWriter(ABC):
    @abstractmethod
    async def write_knowledge(self, document: BaseDocument) -> "WriteResult":
        pass
