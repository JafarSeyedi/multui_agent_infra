# engines/document/models/base
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from .media_types import MEDIA_TYPES
from .media_types import MediaType

# ============================================================
# LEVEL 1 — ELEMENT TYPES
# ============================================================
# Enums
class ElementType(str, Enum):
    TEXT = "text"
    PARAGRAPH = "paragraph"
    RICH_TEXT = "rich_text"
    HEADING = "heading"
    SECTION = "section"
    DIVIDER = "divider"
    QUOTE = "quote"
    LIST = "list"
    LIST_ITEM = "list_item"
    CODE = "code"
    MATH = "math"
    FORMULA = "formula"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TABLE = "table"
    DRAWING = "drawing"
    SHAPE = "shape"
    ANNOTATION = "annotation"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    COMMENT = "comment"
    BOOKMARK = "bookmark"
    LINK = "link"
    PAGE_BREAK = "page_break"
    LINE_BREAK = "line_break"
    COLUMN_BREAK = "column_break"
    EMBEDDED_OBJECT = "embedded_object"
    OLE_OBJECT = "ole_object"
    SPREADSHEET = "spreadsheet"
    DATA = "data"
    BINARY = "binary"
    CAD = "cad"
    CHART = "chart"
    TEXT_BOX = "text_box"
    SECTION_BREAK = "section_break"
    HEADER = "header"
    FOOTER = "footer"
    TOC = "toc"
    FORM_FIELD = "form_field"
    CAPTION = "caption"
    SEMANTIC_HTML = "semantic_html"
    LATEX_COMMAND = "latex_command"
    LATEX_ENVIRONMENT = "latex_environment"
    MACRO = "macro"
    WATERMARK = "watermark"

class BinaryEncoding(str, Enum):
    BASE64 = "base64"
    RAW = "hex"# HEX
    BASE32 = "base32"
    BASE16 = "base16"
    ASCII85 = "ascii85"
    URL_SAFE_BASE64 = "url_safe_base64"

class CompressionMethod(str, Enum):
    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"
    BROTLI = "brotli"
    LZ4 = "lz4"
    ZSTD = "zstd"

class BaseDocument(BaseModel):
    """Base model for all documents"""

    title: str = Field(description="Document title")
    # Identifiers
    document_id: str = Field(description="Unique document identifier")
    version: str = Field(default="1.0", description="Document model version")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation date")
    modified_at: datetime = Field(default_factory=datetime.utcnow, description="Last modified date")

    # Main content
    raw_binary: BinaryPayload | None = None
    raw_text: str | None = None

    # Encoding and compression info
    binary_encoding: BinaryEncoding = Field(
        default=BinaryEncoding.BASE64,
        description="Binary encoding method"
    )
    compression_method: CompressionMethod = Field(
        default=CompressionMethod.NONE,
        description="Compression method"
    )
    decompressed_size: int | None = None #"Original size before compression (bytes)"

    media_type: MediaType
    file_extension: str | None = None

    # Validation
    is_valid: bool = Field(default=True, description="Document validity status")
    validation_errors: list[str] = Field(
        default_factory=list,
        description="List of validation errors"
    )

    # Pydantic v2 configuration
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.decode('utf-8', errors='ignore') if v else ""
        }
    )

    @property
    def has_binary_content(self) -> bool:
        """Does the document have binary content?"""
        return self.raw_binary is not None and self.raw_binary.size_bytes > 0

    @property
    def has_text_content(self) -> bool:
        """Does the document have text content?"""
        return self.raw_text is not None and len(self.raw_text.strip()) > 0

    @property
    def content_size(self) -> int:
        """Document content size (bytes)"""
        if self.raw_binary:
            return self.raw_binary.size_bytes
        elif self.raw_text:
            return len(self.raw_text.encode('utf-8'))
        return 0

    def get_effective_content(self) -> bytes | str | None:
        """Return effective content (binary priority)"""
        if self.raw_binary:
            if self.raw_binary.bytes_content:
                return self.raw_binary.bytes_content
            return self.raw_binary.data
        elif self.raw_text:
            return self.raw_text
        raise ValueError("Document has no main content")


class BinaryPayload(BaseModel):
    media_type: MediaType = MEDIA_TYPES["binary"]
    encoding: BinaryEncoding = BinaryEncoding.BASE64

    # Only one of these should be filled
    bytes_content: bytes | None = None  # For raw binary data
    data: str | None = None     # encoded_data For encoded data

    size_bytes: int = 0
    sha256: str = ""

    # For chunked data
    chunk_index: int = 0
    total_chunks: int = 1

    # Compression
    compressed: bool = False
    compression_algorithm: str | None = None  # "gzip", "zlib", "brotli"
    original_size: int | None = None  # Size before compression

    @property
    def has_content(self) -> bool:
        return self.bytes_content is not None or self.data is not None


# Resolve forward references for pydantic v2 with from __future__ import annotations
BaseDocument.model_rebuild()
