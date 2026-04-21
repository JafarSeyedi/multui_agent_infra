# engines/document/writers/json_writer.py
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import base64

from ..models.base import BaseDocument
from ..models.dsdm_models import (
    DataDocument, DataNode, DataNodeKind, DataValue, 
    ScalarType, node_to_python
)
from .base import BaseDocumentWriter


class JsonDocumentWriter(BaseDocumentWriter):
    """
    Writer for JSON documents following DSDM standard.
    Supports various JSON serialization options.
    """
    
    def __init__(self):
        self._supported_media_types = [
            "application/json",
            "application/json+dsdm",
            "text/json"
        ]
        self._supported_extensions = [".json", ".jsonld"]
        
    async def write(self, document: BaseDocument) -> bytes:
        """
        Write document to JSON bytes.
        
        Args:
            document: Document to write (must be DataDocument)
            
        Returns:
            JSON data as bytes
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Convert DataNode tree to Python structure
        python_data = self._document_to_python(document)
        
        # Default JSON serialization options
        json_kwargs: Dict[str, Any] = {
            'indent': None,
            'ensure_ascii': False,
            'sort_keys': False,
            'default': self._json_default_serializer
        }
        
        # Convert to JSON string
        try:
            json_str = json.dumps(python_data, **json_kwargs)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize to JSON: {e}")
        
        # Encode to bytes
        return json_str.encode('utf-8')
    
    def _document_to_python(self, document: DataDocument) -> Any:
        """
        Convert DataDocument to Python native structure.
        
        Args:
            document: DataDocument to convert
            
        Returns:
            Python native structure (dict/list/scalar)
        """
        if document.root is None:
            return None
        
        # Use the enhanced node_to_python function
        return node_to_python(document.root)
    
    def _json_default_serializer(self, obj: Any) -> Any:
        """
        Default JSON serializer for unsupported types.
        Extends Python's json.dumps default handling.
        """
        # Handle datetime objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Handle Decimal objects
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle bytes (convert to base64)
        if isinstance(obj, bytes):
            return {
                "__type__": "binary",
                "encoding": "base64",
                "data": base64.b64encode(obj).decode('ascii')
            }
        
        # Handle DataValue objects directly
        if isinstance(obj, DataValue):
            return obj.value
        
        # Handle DataNode objects
        if isinstance(obj, DataNode):
            return node_to_python(obj)
        
        # For other types, try to get string representation
        try:
            return str(obj)
        except:
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
    
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write document to JSON file.
        
        Args:
            document: Document to write
            target: Target file path
            options: Writing options:
                - indent: Indentation level (int or None)
                - ensure_ascii: Ensure ASCII output (bool)
                - sort_keys: Sort dictionary keys (bool)
                - encoding: File encoding (str)
                - pretty: Pretty print (bool, alias for indent=2)
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Default options
        default_options: Dict[str, Any] = {
            'indent': None,
            'ensure_ascii': False,
            'sort_keys': False,
            'encoding': 'utf-8',
            'pretty': False
        }
        
        if options:
            default_options.update(options)
        
        # Handle pretty print alias
        if default_options.get('pretty', False):
            default_options['indent'] = 2
        
        # Convert DataNode tree to Python structure
        python_data = self._document_to_python(document)
        
        # Get JSON serialization options with proper typing
        json_kwargs: Dict[str, Any] = {
            'indent': default_options['indent'],
            'ensure_ascii': bool(default_options['ensure_ascii']),
            'sort_keys': bool(default_options['sort_keys']),
            'default': self._json_default_serializer
        }
        
        # Override default serializer if provided
        if 'default' in default_options:
            json_kwargs['default'] = default_options['default']
        
        # Convert to JSON string
        try:
            json_str = json.dumps(python_data, **json_kwargs)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Failed to serialize to JSON: {e}")
        
        # Write to file
        encoding = str(default_options['encoding'])
        try:
            with open(target, 'w', encoding=encoding) as f:
                f.write(json_str)
        except IOError as e:
            raise ValueError(f"Cannot write to file {target}: {e}")
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_media_types
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions
