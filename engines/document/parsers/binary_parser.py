from __future__ import annotations

import pickle # type: ignore[import-untyped]
import warnings
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, AsyncIterator, Union, Sequence, Iterable
import hashlib # type: ignore[import-untyped]
import base64 # type: ignore[import-untyped]
import binascii # type: ignore[import-untyped]

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

from .base import BaseDocumentParser, ParseOptions
from ..models.base import BaseDocument, BinaryPayload, BinaryEncoding
from ..models.media_types import MediaType, MEDIA_TYPES
from ..models.exceptions import DocumentParseError, UnsupportedFormatError


class BinaryParser(BaseDocumentParser):
    """Parser for serialized binary files (MessagePack, CBOR, BSON, Pickle, raw binary)"""
    
    name: str = "binary_parser"
    supported_extensions: Sequence[str] = (
        '.msgpack', '.mpack', '.cbor', '.bson', '.pkl', '.pickle', 
        '.bin', '.dat', '.raw'
    )
    
    def __init__(self):
        super().__init__()
    
    async def parse_bytes(
        self, 
        data: bytes, 
        document_id: str, 
        source_name: str, 
        metadata: Optional[Dict[str, Any]] = None, 
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse binary data from bytes.
        
        Args:
            data: Binary data to parse
            document_id: Unique document identifier
            source_name: Name of the source file/stream
            metadata: Additional metadata
            options: Parsing options
            
        Returns:
            Parsed BaseDocument
        """
        try:
            # Merge metadata
            merged_metadata = metadata.copy() if metadata else {}
            
            # Detect format
            format_type = self._detect_format(data, source_name)
            
            # Parse binary data
            parsed_data = self._parse_binary_data(data, format_type, options)
            
            # Create document
            return self._create_document(
                data=data,
                parsed_data=parsed_data,
                format_type=format_type,
                document_id=document_id,
                source_name=source_name,
                metadata=merged_metadata,
                options=options
            )
            
        except Exception as e:
            if isinstance(e, (DocumentParseError, UnsupportedFormatError)):
                raise
            raise DocumentParseError(f"Error parsing binary file: {str(e)}") from e
    
    async def parse_path(
        self, 
        path: Union[str, Path], 
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """Parse binary data from file path."""
        file_path = Path(path)
        data = file_path.read_bytes()
        
        return await self.parse_bytes(
            data=data,
            document_id=document_id,
            source_name=file_path.name,
            metadata=metadata,
            options=options
        )
    
    async def parse_stream(
        self, 
        stream: AsyncIterator[bytes], 
        document_id: str, 
        source_name: str, 
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """Parse binary data from async stream."""
        try:
            # Collect all bytes from stream
            data = b''
            async for chunk in stream:
                data += chunk
            
            return await self.parse_bytes(
                data=data,
                document_id=document_id,
                source_name=source_name,
                metadata=metadata,
                options=options
            )
        except Exception as e:
            raise DocumentParseError(f"Error parsing binary stream: {str(e)}") from e
    
    def _detect_format(self, data: bytes, source_name: str) -> str:
        """Detect binary format from data and filename."""
        
        # Check by file extension first
        if source_name:
            source_lower = source_name.lower()
            if any(ext in source_lower for ext in ['.msgpack', '.mpack']):
                return 'msgpack'
            elif '.cbor' in source_lower:
                return 'cbor'
            elif '.bson' in source_lower:
                return 'bson'
            elif any(ext in source_lower for ext in ['.pkl', '.pickle']):
                return 'pickle'
            elif any(ext in source_lower for ext in ['.bin', '.dat', '.raw']):
                return 'raw'
        
        # Detect by magic bytes
        if len(data) >= 2:
            # MessagePack detection
            if data[0] in range(0x80, 0x90):  # fixmap, fixarray, fixstr
                if MSGPACK_AVAILABLE:
                    try:
                        msgpack.unpackb(data[:10])
                        return 'msgpack'
                    except:
                        pass
            
            # CBOR detection
            if data[0] in range(0xa0, 0xb8) or data[0] in range(0x80, 0x98):
                if CBOR_AVAILABLE:
                    try:
                        cbor2.loads(data[:10])
                        return 'cbor'
                    except:
                        pass
            
            # BSON detection
            if len(data) >= 4:
                doc_length = int.from_bytes(data[:4], 'little')
                if 5 <= doc_length <= len(data) and data[doc_length-1] == 0x00:
                    if BSON_AVAILABLE:
                        try:
                            bson.decode(data[:doc_length])
                            return 'bson'
                        except:
                            pass
            
            # Pickle detection
            if data[:2] in [b'\x80', b'\x81', b'\x82', b'\x83', b'\x84', b'\x85']:
                return 'pickle'
        
        # Default to raw binary
        return 'raw'
    
    def _parse_binary_data(
        self, 
        data: bytes, 
        format_type: str, 
        options: Optional[ParseOptions]
    ) -> Any:
        """Parse binary data based on format."""
        
        # Check if unsafe operations are allowed
        unsafe_allowed = options.unsafe_operations_allowed if options else False
        
        try:
            if format_type == 'msgpack':
                if not MSGPACK_AVAILABLE:
                    raise ImportError("msgpack module not installed. Install with: pip install msgpack")
                return msgpack.unpackb(data, raw=False)
            
            elif format_type == 'cbor':
                if not CBOR_AVAILABLE:
                    raise ImportError("cbor2 module not installed. Install with: pip install cbor2")
                return cbor2.loads(data)
            
            elif format_type == 'bson':
                if not BSON_AVAILABLE:
                    raise ImportError("bson module not installed. Install with: pip install pymongo")
                return bson.decode(data)
            
            elif format_type == 'pickle':
                if not unsafe_allowed:
                    warnings.warn(
                        "Pickle parsing can be dangerous. "
                        "To allow unsafe pickle, set options.unsafe_operations_allowed=True",
                        UserWarning
                    )
                    # Use restricted unpickler
                    class RestrictedUnpickler(pickle.Unpickler):
                        def find_class(self, module, name):
                            # Only allow standard Python modules
                            if module.startswith('__builtins__') or module in ['builtins', 'copyreg', '_codecs']:
                                return super().find_class(module, name)
                            raise pickle.UnpicklingError(f"Access to module not allowed: {module}.{name}")
                    
                    import io
                    return RestrictedUnpickler(io.BytesIO(data)).load()
                else:
                    return pickle.loads(data)
            
            elif format_type == 'raw':
                # Return raw bytes as is
                return data
            
            else:
                raise UnsupportedFormatError(f"Unsupported binary format: {format_type}")
                
        except Exception as e:
            raise DocumentParseError(f"Error parsing {format_type}: {str(e)}") from e
    
    def _create_document(
        self,
        data: bytes,
        parsed_data: Any,
        format_type: str,
        document_id: str,
        source_name: str,
        metadata: Dict[str, Any],
        options: Optional[ParseOptions]
    ) -> BaseDocument:
        """Create BaseDocument from parsed data."""
        
        # Determine media type
        media_type_map = {
            'msgpack': MEDIA_TYPES.get('messagepack'),
            'cbor': MEDIA_TYPES.get('cbor'),
            'bson': MEDIA_TYPES.get('bson'),
            'pickle': MEDIA_TYPES.get('binary'),
            'raw': MEDIA_TYPES.get('binary'),
        }
        
        media_type = media_type_map.get(format_type, MEDIA_TYPES['binary'])
        if media_type is None:
            media_type = MEDIA_TYPES['binary']
        
        # Determine encoding from options
        encoding_str = options.binary_encoding if options else "base64"
        encoding = BinaryEncoding(encoding_str)
        
        # Calculate hash
        sha256_hash = hashlib.sha256(data).hexdigest()
        
        # Create BinaryPayload
        binary_payload = BinaryPayload(
            media_type=media_type,
            encoding=encoding,
            bytes_content=data,
            data=self._encode_binary(data, encoding),
            size_bytes=len(data),
            sha256=sha256_hash,
            chunk_index=0,
            total_chunks=1,
            compressed=False,
            compression_algorithm=None,
            original_size=len(data)
        )
        
        # Update metadata
        metadata.update({
            'parsed_format': format_type,
            'parsed_data_type': type(parsed_data).__name__,
            'source_name': source_name,
            'parse_timestamp': datetime.now().isoformat(),
            'binary_size': len(data),
            'binary_encoding': encoding.value,
        })
        
        # Create raw_text representation
        raw_text = None
        if format_type != 'raw':
            try:
                import json
                raw_text = json.dumps(parsed_data, ensure_ascii=False, indent=2)
            except:
                raw_text = repr(parsed_data)
        else:
            raw_text = f"Raw binary data: {len(data)} bytes"
        
        # Determine file extension
        file_extension = self._get_extension_from_format(format_type)
        
        # Create BaseDocument
        return BaseDocument(
            title=f"Binary Document - {format_type.upper()}",
            document_id=document_id,
            metadata=metadata,
            raw_binary=binary_payload,
            raw_text=raw_text,
            binary_encoding=encoding,
            decompressed_size=len(data),
            media_type=media_type,
            file_extension=file_extension,
            is_valid=True,
            validation_errors=[]
        )
    
    def _encode_binary(self, data: bytes, encoding: BinaryEncoding) -> str:
        """Encode binary data to string."""
        if encoding == BinaryEncoding.BASE64:
            return base64.b64encode(data).decode('ascii')
        elif encoding == BinaryEncoding.URL_SAFE_BASE64:
            return base64.urlsafe_b64encode(data).decode('ascii')
        elif encoding == BinaryEncoding.BASE32:
            return base64.b32encode(data).decode('ascii')
        elif encoding == BinaryEncoding.BASE16:
            return binascii.hexlify(data).decode('ascii')
        elif encoding == BinaryEncoding.ASCII85:
            return base64.a85encode(data).decode('ascii')
        elif encoding == BinaryEncoding.RAW:
            return data.hex()
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
    
    def _get_extension_from_format(self, format_type: str) -> str:
        """Get file extension from format type."""
        extension_map = {
            'msgpack': '.msgpack',
            'cbor': '.cbor',
            'bson': '.bson',
            'pickle': '.pickle',
            'raw': '.bin'
        }
        return extension_map.get(format_type, '.bin')
    
    def supports_extension(self, extension: str) -> bool:
        """Check if parser supports given extension."""
        ext_lower = extension.lower().lstrip('.')
        supported = {ext.lstrip('.') for ext in self.supported_extensions}
        return ext_lower in supported
    
    def iter_supported_extensions(self) -> Iterable[str]:
        """Iterate over supported extensions."""
        return self.supported_extensions
