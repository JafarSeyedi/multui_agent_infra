# engines/document/writers/yaml_writer.py
import yaml
from typing import Optional, Dict, Any, Sequence, Union, cast
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


class YamlDocumentWriter(BaseDocumentWriter):
    """
    Writer for YAML documents following DSDM standard.
    Supports YAML 1.2 specification with various options.
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
        
    async def write(self, document: BaseDocument) -> bytes:
        """
        Write document to YAML bytes.
        
        Args:
            document: Document to write (must be DataDocument)
            
        Returns:
            YAML data as bytes
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Convert DataNode tree to Python structure
        python_data = self._document_to_python(document)
        
        # Default YAML serialization options
        yaml_kwargs: Dict[str, Any] = {
            'default_flow_style': False,
            'allow_unicode': True,
            'encoding': 'utf-8',
            'Dumper': yaml.SafeDumper
        }
        
        # Convert to YAML string
        try:
            yaml_str = yaml.dump(
                python_data, 
                **yaml_kwargs,
                default_style=None,
                default_flow_style=False
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to serialize to YAML: {e}")
        
        # Encode to bytes
        return yaml_str.encode('utf-8')
    
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
    
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write document to YAML file.
        
        Args:
            document: Document to write
            target: Target file path
            options: Writing options:
                - default_flow_style: Flow style (bool)
                - allow_unicode: Allow Unicode (bool)
                - encoding: File encoding (str)
                - indent: Indentation level (int)
                - width: Line width (int)
                - explicit_start: Add document start marker (bool)
                - explicit_end: Add document end marker (bool)
                - canonical: Canonical format (bool)
                - default_style: Default scalar style (None, '"', "'", '|', '>')
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Default options
        default_options: Dict[str, Any] = {
            'default_flow_style': False,
            'allow_unicode': True,
            'encoding': 'utf-8',
            'indent': 2,
            'width': 80,
            'explicit_start': False,
            'explicit_end': False,
            'canonical': False,
            'default_style': None
        }
        
        if options:
            default_options.update(options)
        
        # Convert DataNode tree to Python structure
        python_data = self._document_to_python(document)
        
        # Create custom Dumper with representers
        class CustomDumper(yaml.SafeDumper):
            """Custom YAML dumper with support for additional types."""
            
            # Representer functions defined as static methods inside the class
            @staticmethod
            def datetime_representer(dumper: CustomDumper, data: datetime) -> yaml.Node:
                """Representer for datetime objects."""
                return dumper.represent_scalar(
                    'tag:yaml.org,2002:timestamp',
                    data.isoformat()
                )
            
            @staticmethod
            def date_representer(dumper: CustomDumper, data: date) -> yaml.Node:
                """Representer for date objects."""
                return dumper.represent_scalar(
                    'tag:yaml.org,2002:timestamp',
                    data.isoformat()
                )
            
            @staticmethod
            def bytes_representer(dumper: CustomDumper, data: bytes) -> yaml.Node:
                """Representer for bytes objects."""
                return dumper.represent_scalar(
                    'tag:yaml.org,2002:binary',
                    base64.b64encode(data).decode('ascii')
                )
            
            @staticmethod
            def decimal_representer(dumper: CustomDumper, data: Decimal) -> yaml.Node:
                """Representer for Decimal objects."""
                return dumper.represent_scalar(
                    'tag:yaml.org,2002:float',
                    str(float(data))
                )
            
            @staticmethod
            def datavalue_representer(dumper: CustomDumper, data: DataValue) -> yaml.Node:
                """Representer for DataValue objects."""
                return dumper.represent_data(data.value)
            
            @staticmethod
            def datanode_representer(dumper: CustomDumper, data: DataNode) -> yaml.Node:
                """Representer for DataNode objects."""
                python_data = node_to_python(data)
                return dumper.represent_data(python_data)
                    
        # Add custom representers - now the types match exactly
        CustomDumper.add_representer(datetime, CustomDumper.datetime_representer)
        CustomDumper.add_representer(date, CustomDumper.date_representer)
        CustomDumper.add_representer(bytes, CustomDumper.bytes_representer)
        CustomDumper.add_representer(Decimal, CustomDumper.decimal_representer)
        CustomDumper.add_representer(DataValue, CustomDumper.datavalue_representer)
        CustomDumper.add_representer(DataNode, CustomDumper.datanode_representer)
        
        # Get YAML serialization options
        yaml_kwargs: Dict[str, Any] = {
            'default_flow_style': bool(default_options['default_flow_style']),
            'allow_unicode': bool(default_options['allow_unicode']),
            'indent': int(default_options['indent']),
            'width': int(default_options['width']),
            'explicit_start': bool(default_options['explicit_start']),
            'explicit_end': bool(default_options['explicit_end']),
            'canonical': bool(default_options['canonical']),
            'default_style': default_options['default_style'],
            'Dumper': CustomDumper
        }
        
        # Convert to YAML string
        try:
            yaml_str = yaml.dump(
                python_data, 
                **yaml_kwargs
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to serialize to YAML: {e}")
        
        # Write to file
        encoding = str(default_options['encoding'])
        try:
            with open(target, 'w', encoding=encoding) as f:
                f.write(yaml_str)
        except IOError as e:
            raise ValueError(f"Cannot write to file {target}: {e}")
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_media_types
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions
