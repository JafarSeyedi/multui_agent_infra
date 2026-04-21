# engines/document/writers/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncIterator
from pathlib import Path
from ..models.base import BaseDocument


from pydantic import BaseModel

class WriteOptions(BaseModel):  
    """Options for document writing across all standards."""
    
    # General options
    encoding: str = "utf-8"
    
    # USDM-specific options
    include_metadata: bool = True
    pretty_print: bool = False
    
    # Markdown-specific options
    heading_style: str = "atx"  # "atx" or "setext"
    bullet_style: str = "-"     # "-", "*", or "+"
    code_block_style: str = "```"  # "```" or "~~~"
    
    # Custom extensions
    custom: Dict[str, Any] = {}


class BaseDocumentWriter(ABC):
    """Base class for all document writers."""
    def __init__(self, options: Optional[WriteOptions] = None):
        self.options=options
    
    @abstractmethod
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        yield b""  # این فقط برای جلوگیری از خطای abstract است
           
    @abstractmethod
    async def write(self, document: BaseDocument) -> bytes:
        pass
    
    @abstractmethod
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        pass
    
    @abstractmethod
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        pass
