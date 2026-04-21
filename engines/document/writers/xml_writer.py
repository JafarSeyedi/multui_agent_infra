# engines/document/writers/xml_writer.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Optional, Dict, Any
from pathlib import Path
import hashlib

from ..models.base import BaseDocument
from ..models.dsdm_models import (
    DataDocument, DataNode, DataNodeKind, DataValue,
    ScalarType, node_to_python
)
from .base import BaseDocumentWriter


class XmlDocumentWriter(BaseDocumentWriter):
    """
    Writer for XML documents using DSDM model.
    Supports XML 1.0 specification with proper formatting.
    """
    
    def __init__(self):
        self._supported_media_types = [
            "application/xml",
            "text/xml",
            "application/xml+dsdm"
        ]
        self._supported_extensions = [".xml"]
        
    async def write(self, document: BaseDocument) -> bytes:
        """
        Write document to XML bytes.
        
        Args:
            document: Document to write (must be DataDocument)
            
        Returns:
            XML data as bytes
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Convert DataNode to XML string
        xml_str = self._document_to_xml_string(document)
        
        # Encode to bytes
        return xml_str.encode('utf-8')
    
    async def write_to_file(
        self, 
        document: BaseDocument, 
        target: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Write document to XML file.
        
        Args:
            document: Document to write
            target: Target file path
            options: Writing options:
                - encoding: XML encoding (default: 'utf-8')
                - xml_declaration: Include XML declaration (bool, default: True)
                - pretty_print: Pretty print with indentation (bool, default: True)
                - indent: Indentation string (default: '  ')
                - standalone: Standalone declaration (bool, default: None)
                - doctype: DOCTYPE declaration (str)
        """
        if not isinstance(document, DataDocument):
            raise TypeError(f"Expected DataDocument, got {type(document).__name__}")
        
        # Default options
        default_options: Dict[str, Any] = {
            'encoding': 'utf-8',
            'xml_declaration': True,
            'pretty_print': True,
            'indent': '  ',
            'standalone': None,
            'doctype': None
        }
        
        if options:
            default_options.update(options)
        
        # Convert DataNode to XML string
        xml_str = self._document_to_xml_string(document, default_options)
        
        # Write to file
        encoding = str(default_options['encoding'])
        try:
            with open(target, 'w', encoding=encoding) as f:
                f.write(xml_str)
        except IOError as e:
            raise ValueError(f"Cannot write to file {target}: {e}")
    
    def _document_to_xml_string(
        self, 
        document: DataDocument, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Convert DataDocument to XML string.
        """
        if document.root is None:
            return ""
        
        # Convert DataNode to ElementTree Element
        root_element = self._dsdm_to_element(document.root)
        
        # Create ElementTree
        tree = ET.ElementTree(root_element)
        
        # Convert to string
        xml_bytes = ET.tostring(
            root_element, 
            encoding='utf-8',
            xml_declaration=options.get('xml_declaration', True) if options else True,
            method='xml',
            short_empty_elements=True
        )
        
        xml_str = xml_bytes.decode('utf-8')
        
        # Pretty print if requested
        if options and options.get('pretty_print', True):
            xml_str = self._pretty_print_xml(xml_str, options.get('indent', '  '))
        
        # Add DOCTYPE if specified
        if options and options.get('doctype'):
            doctype = f'<!DOCTYPE {options["doctype"]}>'
            if '<?xml' in xml_str:
                # Insert after XML declaration
                lines = xml_str.split('\n', 1)
                xml_str = f'{lines[0]}\n{doctype}\n{lines[1]}'
            else:
                xml_str = f'{doctype}\n{xml_str}'
        
        return xml_str
    
    def _dsdm_to_element(self, node: DataNode) -> ET.Element:
        """
        Convert DSDM DataNode to ElementTree Element.
        """
        # Handle different node kinds
        if node.kind == DataNodeKind.XML_ELEMENT:
            return self._handle_xml_element(node)
        elif node.kind == DataNodeKind.OBJECT:
            # Convert object to element (for non-XML structures)
            return self._handle_object_as_element(node)
        else:
            # Create a wrapper element for other node types
            elem = ET.Element("dsdm_wrapper")
            elem.text = str(node.value.value) if node.value else ""
            return elem
    
    def _handle_xml_element(self, node: DataNode) -> ET.Element:
        """Handle XML element node."""
        # Create element with namespace if present
        element_name = node.name or "element"
        if node.namespace:
            element_name = f"{node.namespace}:{element_name}"
        
        elem = ET.Element(element_name)
        
        # Add attributes
        for attr_node in node.attributes:
            if attr_node.kind == DataNodeKind.XML_ATTRIBUTE:
                attr_name = attr_node.name or ""
                if attr_node.namespace:
                    attr_name = f"{attr_node.namespace}:{attr_name}"
                
                attr_value = ""
                if attr_node.value:
                    attr_value = str(attr_node.value.value)
                
                elem.set(attr_name, attr_value)
        
        # Add namespace declarations from metadata
        if node.metadata and "xmlns" in node.metadata:
            for prefix, uri in node.metadata["xmlns"].items():
                if prefix:
                    elem.set(f"xmlns:{prefix}", uri)
                else:
                    elem.set("xmlns", uri)
        
        # Add children
        for child in node.children:
            if child.kind == DataNodeKind.XML_ELEMENT:
                # Child element
                child_elem = self._handle_xml_element(child)
                elem.append(child_elem)
            elif child.kind == DataNodeKind.XML_TEXT:
                # Text content
                if child.value:
                    text = str(child.value.value)
                    if elem.text:
                        elem.text += text
                    else:
                        elem.text = text
            elif child.kind == DataNodeKind.XML_CDATA:
                # CDATA section
                if child.value:
                    cdata = str(child.value.value)
                    cdata_elem = ET.Element("![CDATA[")
                    cdata_elem.text = cdata
                    elem.append(cdata_elem)
            elif child.kind == DataNodeKind.XML_COMMENT:
                # Comment
                if child.value:
                    comment = ET.Comment(str(child.value.value))
                    elem.append(comment)
            elif child.kind == DataNodeKind.XML_PROCESSING_INSTRUCTION:
                # Processing instruction
                if child.value:
                    pi = ET.ProcessingInstruction(
                        child.name or "xml",
                        str(child.value.value)
                    )
                    elem.append(pi)
        
        return elem
    
    def _handle_object_as_element(self, node: DataNode) -> ET.Element:
        """Convert object node to XML element."""
        elem_name = node.name or "object"
        elem = ET.Element(elem_name)
        
        # Add children as sub-elements
        for child in node.children:
            if child.kind in [DataNodeKind.OBJECT, DataNodeKind.XML_ELEMENT]:
                child_elem = self._dsdm_to_element(child)
                elem.append(child_elem)
            elif child.kind == DataNodeKind.ARRAY:
                # Handle arrays
                for array_child in child.children:
                    array_elem = self._dsdm_to_element(array_child)
                    elem.append(array_elem)
            elif child.kind == DataNodeKind.SCALAR:
                # Add as attribute or text
                if child.name and child.value:
                    elem.set(child.name, str(child.value.value))
                elif child.value:
                    elem.text = str(child.value.value)
        
        return elem
    
    def _pretty_print_xml(self, xml_str: str, indent: str = '  ') -> str:
        """Pretty print XML string."""
        try:
            parsed = minidom.parseString(xml_str)
            return parsed.toprettyxml(indent=indent)
        except Exception:
            # If pretty printing fails, return original
            return xml_str
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_media_types
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions
