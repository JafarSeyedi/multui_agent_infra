# engines/document/models/exceptions.py
"""
Hierarchical error system for document management
"""

class DocumentError(Exception):
    """Base error for all document-related errors"""


class DocumentParseError(DocumentError):
    """Error while parsing document"""


class DocumentWriteError(DocumentError):
    """Error while writing document"""


class DocumentValidationError(DocumentError):
    """Document validation error"""


class UnsupportedFormatError(DocumentError):
    """Document format is not supported"""
    def __init__(self, format_name: str, supported_formats: list[str] | None = None):
        self.format_name = format_name
        self.supported_formats = supported_formats or []
        message = f"Format '{format_name}' is not supported"
        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
        super().__init__(message)


class BinaryEncodingError(DocumentError):
    """Binary encoding/decoding error"""


class StreamingError(DocumentError):
    """Streaming operation error"""


class RegistryError(DocumentError):
    """Registry system error"""


class CompressionError(DocumentError):
    """Compression/decompression error"""


class SchemaValidationError(DocumentValidationError):
    """Schema validation error"""


class ContentDetectionError(DocumentError):
    """Content detection error"""
