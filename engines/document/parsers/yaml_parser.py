# engines/document/parsers/yaml_parser.py
import yaml
from typing import Optional, Dict, Any, Union, Sequence
from pathlib import Path

from ..models.base import BaseDocument
from ..models.dsdm_models import (
    DataDocument, DataNode, DataNodeKind, DataValue, 
    ScalarType, DataDocumentCapabilities, build_node_from_python
)
from .base import BaseDocumentParser, ParseOptions


class YamlDocumentParser(BaseDocumentParser):
    """
    Parser for YAML documents following DSDM standard.
    Supports YAML 1.2 specification.
    """
    
    def __init__(self):
        self._supported_media_types = [
            "application/yaml",
            "application/x-yaml",
            "text/yaml",
            "text/x-yaml",
            "application/yaml+dsdm"
        ]
        self._supported_extensions = [".yaml", ".yml"]
        
    async def parse_bytes(
        self, 
        data: bytes, 
        document_id: str, 
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None, 
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse YAML data from bytes.
        
        Args:
            data: YAML data as bytes
            document_id: Unique identifier for the document
            source_name: Name of the source
            metadata: Additional metadata
            options: Parsing options
            
        Returns:
            DataDocument containing parsed YAML structure
        """
        # Default options
        if options is None:
            options = ParseOptions()
        
        # Merge metadata
        merged_metadata = metadata or {}
        
        try:
            # Decode bytes to string with appropriate encoding
            encoding = options.encoding or "utf-8"
            yaml_str = data.decode(encoding)
            
            # Parse YAML
            # Use SafeLoader for security
            yaml_data = yaml.safe_load(yaml_str)
            
            # Handle empty documents
            if yaml_data is None:
                yaml_data = {}
            
            # Build DataNode tree from Python structure
            root_node = build_node_from_python(
                yaml_data, 
                path="$", 
                name="root",
                node_id_prefix="yaml"
            )
            
            # Create DocumentMetadata - بررسی فیلدهای موجود
            # ابتدا فیلدهای اصلی را تنظیم می‌کنیم
            doc_metadata_kwargs: Dict[str, Any] = {}
            
            # بررسی فیلدهای موجود در DocumentMetadata
            # فرض می‌کنیم DocumentMetadata فیلدهای زیر را دارد:
            # id: str (document_id)
            # name: str (source_name)
            # size: Optional[int] (size_bytes)
            # و فیلدهای دیگر...
            
            # تنظیم فیلدهای اصلی
            doc_metadata_kwargs['id'] = document_id
            doc_metadata_kwargs['name'] = source_name
            doc_metadata_kwargs['size'] = len(data)
            
            # اضافه کردن metadataهای اضافی
            if merged_metadata:
                doc_metadata_kwargs.update(merged_metadata)
            
            # اضافه کردن اطلاعات format-specific
            doc_metadata_kwargs['additional_metadata'] = {
                "yaml_version": "1.2",
                "parsed_with": "PyYAML",
                "encoding": encoding,
                "media_type": "application/yaml",
                "loader": "SafeLoader"
            }
            
            # Create DocumentMetadata
            doc_metadata = doc_metadata_kwargs
            
            # Create DataDocumentCapabilities
            capabilities = DataDocumentCapabilities()
            
            # Create DataDocument
            # بررسی فیلدهای DataDocument
            document_kwargs: Dict[str, Any] = {
                'id': document_id,
                'metadata': doc_metadata,
                'root': root_node,
                'capabilities': capabilities,
                'media_type': 'application/yaml'
            }
            
            document = DataDocument(**document_kwargs)
            
            # اگر فیلد format_specific_metadata وجود دارد، آن را تنظیم کن
            if hasattr(document, 'format_specific_metadata'):
                document.format_specific_metadata = {
                    "yaml_version": "1.2",
                    "parsed_with": "PyYAML",
                    "encoding": encoding,
                    "media_type": "application/yaml",
                    "loader": "SafeLoader"
                }
            
            return document
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML data: {e}")
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
        Parse YAML data from file path.
        
        Args:
            path: Path to YAML file
            document_id: Unique identifier for the document
            metadata: Additional metadata
            options: Parsing options
            
        Returns:
            DataDocument containing parsed YAML structure
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
