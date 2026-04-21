# engines/document/parsers/json_parser.py
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path

from ..models.base import BaseDocument
from ..models.media_detection import detect_by_extension
from ..models.dsdm_models import (
    DataDocument, DataNode, DataNodeKind, DataValue, 
    ScalarType, DataDocumentCapabilities, build_node_from_python
)
from .base import BaseDocumentParser, ParseOptions


class JsonDocumentParser(BaseDocumentParser):
    """
    Parser for JSON documents following DSDM standard.
    Supports standard JSON format with various encodings.
    """
    
    def __init__(self):
        self._supported_media_types = [
            "application/json",
            "application/json+dsdm",
            "text/json"
        ]
        self._supported_extensions = [".json", ".jsonld"]
        
    async def parse_bytes(
        self, 
        data: bytes, 
        document_id: str, 
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None, 
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse JSON data from bytes.
        
        Args:
            data: JSON data as bytes
            document_id: Unique identifier for the document
            source_name: Name of the source
            metadata: Additional metadata
            options: Parsing options
            
        Returns:
            DataDocument containing parsed JSON structure
        """
        # Default options
        if options is None:
            options = ParseOptions()
        
        # Merge metadata
        merged_metadata = metadata
        if not merged_metadata:
            merged_metadata = {}
        
        try:
            # Decode bytes to string with appropriate encoding
            encoding = "utf-8"  # Default encoding for JSON
            json_str = data.decode(encoding)
            
            # Parse JSON
            json_data = json.loads(json_str)
            
            # Build DataNode tree from Python structure
            root_node = build_node_from_python(
                json_data, 
                path="$", 
                name="root",
                node_id_prefix="json"
            )
            
            doc_metadata = merged_metadata
            specific_metadata: Dict[str, Any] = {
                "document_id": document_id,
                "source_name": source_name,
                "size_bytes": len(data),
                "json_version": "RFC 8259",
                "parsed_with": "json.loads",
                "encoding": encoding,
                "media_type": "application/json",
            }
            doc_metadata.update( specific_metadata )
            
            # Create DataDocumentCapabilities
            capabilities = DataDocumentCapabilities()
            
            mt=detect_by_extension("json")
            # Create DataDocument
            document = DataDocument(
                document_id=document_id,
                media_type=mt,
                title=source_name,
                metadata=doc_metadata,
                root=root_node,
                capabilities=capabilities
            )
            
            return document
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Encoding error: {e}")
    
    async def parse_path(
        self, 
        path: Union[str, Path], 
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None, 
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse JSON data from file path.
        
        Args:
            path: Path to JSON file
            document_id: Unique identifier for the document
            metadata: Additional metadata
            options: Parsing options
            
        Returns:
            DataDocument containing parsed JSON structure
        """
        # Convert to Path if string
        file_path = Path(path) if isinstance(path, str) else path
        
        # Read file
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise ValueError(f"Cannot read file {file_path}: {e}")
        
        # Use source name from file path
        source_name = file_path.name
        
        # Parse using bytes method
        return await self.parse_bytes(
            data, 
            document_id, 
            source_name, 
            metadata, 
            options
        )
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_media_types
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions
