# engines/document/writers/binary_writer
from __future__ import annotations

import pickle
import warnings
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator
import asyncio

try:
    import msgpack # type: ignore[import-untyped]
    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False
    msgpack = None

try:
    import cbor2 # type: ignore[import-untyped]
    CBOR_AVAILABLE = True
except ImportError:
    CBOR_AVAILABLE = False

try:
    import bson # type: ignore[import-untyped]
    BSON_AVAILABLE = True
except ImportError:
    BSON_AVAILABLE = False

from .base import BaseDocumentWriter, WriteOptions
from ..models.base import BaseDocument, BinaryEncoding
from ..models.media_types import MEDIA_TYPES
from ..models.exceptions import DocumentWriteError, UnsupportedFormatError


class BinaryWriter(BaseDocumentWriter):
    """Writer for serialized binary formats (MessagePack, CBOR, BSON, Pickle)"""
    
    def __init__(self, options: Optional[WriteOptions] = None):
        super().__init__(options)
        self._supported_formats = ['msgpack', 'cbor', 'bson', 'pickle', 'raw']
        self._supported_extensions = ['.msgpack', '.mpack', '.cbor', '.bson', '.pkl', '.pickle', '.bin']
        self._supported_mime_types = [
            'application/msgpack',
            'application/x-msgpack',
            'application/cbor',
            'application/bson',
            'application/x-bson',
            'application/python-pickle',
            'application/octet-stream'
        ]
    
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        """Write document as async stream of bytes."""
        try:
            # Serialize document to binary
            binary_data = await self._serialize_document(document)
            
            # Yield in chunks (e.g., 64KB chunks)
            chunk_size = 65536
            for i in range(0, len(binary_data), chunk_size):
                yield binary_data[i:i + chunk_size]
                await asyncio.sleep(0)  # Yield control
                
        except Exception as e:
            raise DocumentWriteError(f"Error writing binary stream: {str(e)}") from e
    
    async def write(self, document: BaseDocument) -> bytes:
        """Write document to bytes."""
        try:
            return await self._serialize_document(document)
        except Exception as e:
            raise DocumentWriteError(f"Error writing binary document: {str(e)}") from e
    
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """Write document to file."""
        try:
            # Get binary data
            binary_data = await self._serialize_document(document, options)
            
            # Ensure parent directory exists
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            target.write_bytes(binary_data)
            
        except Exception as e:
            raise DocumentWriteError(f"Error writing binary file: {str(e)}") from e
    
    async def _serialize_document(
        self, 
        document: BaseDocument, 
        options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Serialize document to binary format."""
        
        # Determine output format
        output_format = self._determine_output_format(document, options)
        
        # Prepare data for serialization
        data_to_serialize = self._prepare_data_for_serialization(document, options)
        
        # Serialize to binary
        return self._serialize_to_binary(data_to_serialize, output_format, options)
    
    def _determine_output_format(
        self, 
        document: BaseDocument, 
        options: Optional[Dict[str, Any]]
    ) -> str:
        """Determine output format from document and options."""
        
        # Priority 1: Options override
        if options and 'format' in options:
            fmt = options['format'].lower()
            if fmt in self._supported_formats:
                return fmt
        
        # Priority 2: Document media type
        if document.media_type:
            mime = document.media_type.mime.lower()
            if 'msgpack' in mime:
                return 'msgpack'
            elif 'cbor' in mime:
                return 'cbor'
            elif 'bson' in mime:
                return 'bson'
            elif 'pickle' in mime:
                return 'pickle'
            elif 'octet-stream' in mime:
                return 'raw'
        
        # Priority 3: File extension
        if document.file_extension:
            ext = document.file_extension.lower()
            if ext in ['.msgpack', '.mpack']:
                return 'msgpack'
            elif ext == '.cbor':
                return 'cbor'
            elif ext == '.bson':
                return 'bson'
            elif ext in ['.pkl', '.pickle']:
                return 'pickle'
            elif ext in ['.bin', '.dat', '.raw']:
                return 'raw'
        
        # Default: msgpack (most efficient)
        return 'msgpack'
    
    def _prepare_data_for_serialization(
        self, 
        document: BaseDocument, 
        options: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare document data for serialization."""
        
        # Basic document data
        data: Dict[str, Any] = {
            'metadata': document.metadata.copy(),
            'document_id': document.document_id,
            'title': document.title,
            'version': document.version,
            'created_at': document.created_at.isoformat() if document.created_at else None,
            'modified_at': document.modified_at.isoformat() if document.modified_at else None,
            'media_type': {
                'mime': document.media_type.mime,
                'format': document.media_type.format.value,
                'kind': document.media_type.kind.value
            } if document.media_type else None,
            'file_extension': document.file_extension,
            'is_valid': document.is_valid,
            'validation_errors': document.validation_errors.copy() if document.validation_errors else []
        }
        
        # Add text content
        if document.raw_text:
            data['raw_text'] = document.raw_text
        
        # Add binary content if available
        if document.raw_binary:
            binary_data = document.raw_binary
            data['binary_payload'] = {
                'media_type': binary_data.media_type.mime if binary_data.media_type else None,
                'encoding': binary_data.encoding.value,
                'size_bytes': binary_data.size_bytes,
                'sha256': binary_data.sha256,
                'compressed': binary_data.compressed,
                'compression_algorithm': binary_data.compression_algorithm,
                'chunk_index': binary_data.chunk_index,
                'total_chunks': binary_data.total_chunks
            }
            
            # Include binary data if present
            if binary_data.bytes_content:
                import base64
                data['binary_data'] = base64.b64encode(binary_data.bytes_content).decode('ascii')
            elif binary_data.data:
                data['binary_data'] = binary_data.data
        
        # Add any additional data from options
        if options and 'extra_data' in options:
            extra_data = options['extra_data']
            if isinstance(extra_data, dict):
                data.update(extra_data)
        
        return data
    
    def _serialize_to_binary(
        self, 
        data: Dict[str, Any], 
        format_type: str, 
        options: Optional[Dict[str, Any]]
    ) -> bytes:
        """Serialize data to binary format."""
        
        # Check if unsafe operations are allowed
        unsafe_allowed = options.get('unsafe_operations_allowed', False) if options else False
        
        try:
            if format_type == 'msgpack':
                if not MSGPACK_AVAILABLE:
                    raise ImportError("msgpack module not installed. Install with: pip install msgpack")
                return msgpack.packb(
                    data,
                    use_bin_type=True,
                    datetime=True
                )
            
            elif format_type == 'cbor':
                if not CBOR_AVAILABLE:
                    raise ImportError("cbor2 module not installed. Install with: pip install cbor2")
                return cbor2.dumps(data)
            
            elif format_type == 'bson':
                if not BSON_AVAILABLE:
                    raise ImportError("bson module not installed. Install with: pip install pymongo")
                return bson.encode(data)
            
            elif format_type == 'pickle':
                # Security warning
                if not unsafe_allowed:
                    warnings.warn(
                        "Pickle serialization can be dangerous. "
                        "To allow unsafe pickle, set unsafe_operations_allowed=True in options",
                        UserWarning
                    )
                
                # Use highest protocol for efficiency
                protocol = options.get('pickle_protocol', pickle.HIGHEST_PROTOCOL) if options else pickle.HIGHEST_PROTOCOL
                return pickle.dumps(data, protocol=protocol)
            
            elif format_type == 'raw':
                # For raw format, return as bytes if possible
                if 'binary_data' in data and isinstance(data['binary_data'], str):
                    import base64
                    return base64.b64decode(data['binary_data'])
                elif 'raw_text' in data:
                    encoding = self.options.encoding if self.options else 'utf-8'
                    return data['raw_text'].encode(encoding)
                else:
                    # Convert to JSON and encode
                    import json
                    return json.dumps(data, ensure_ascii=False).encode('utf-8')
            
            else:
                raise UnsupportedFormatError(f"Unsupported binary format: {format_type}")
                
        except Exception as e:
            raise DocumentWriteError(f"Error serializing to {format_type}: {str(e)}") from e
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_mime_types.copy()
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions.copy()
