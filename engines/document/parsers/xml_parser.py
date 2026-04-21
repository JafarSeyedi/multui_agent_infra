# engines/document/parsers/xml_parser.py
import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.dom.minidom import Node, Element, Text, Comment, ProcessingInstruction, CDATASection, DocumentType
from typing import Optional, Dict, Any, List, Union, cast
from pathlib import Path
import re
import hashlib

from ..models.media_detection import detect_by_extension
from ..models.base import BaseDocument
from ..models.dsdm_models import (
    DataDocument, DataNode, DataNodeKind, DataValue, 
    ScalarType, DataDocumentCapabilities, DataSchemaReference
)
from .base import BaseDocumentParser, ParseOptions


class XmlDocumentParser(BaseDocumentParser):
    """
    Parser for XML documents using DSDM model.
    Supports XML 1.0 specification with namespaces, comments, PIs, etc.
    """
    
    def __init__(self):
        self._supported_media_types = [
            "application/xml",
            "text/xml",
            "application/xml+dsdm"
        ]
        self._supported_extensions = [".xml"]
        
    async def parse_bytes(
        self, 
        data: bytes, 
        document_id: str, 
        source_name: str, 
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse XML from bytes.
        
        Args:
            data: XML data as bytes
            document_id: Unique identifier for the document
            source_name: Name of the source
            metadata: Additional metadata
            options: Parsing options:
                - encoding: XML encoding (default: 'utf-8')
                - namespaces: Dict of namespace prefixes to URIs
                - strip_namespace: Remove namespace prefixes (bool)
                - preserve_comments: Keep comments (bool, default: True)
                - preserve_pis: Keep processing instructions (bool, default: True)
                - preserve_cdata: Keep CDATA sections (bool, default: True)
                
        Returns:
            DataDocument with XML structure
        """
        # Default options
        default_options: Dict[str, Any] = {
            'encoding': 'utf-8',
            'namespaces': {},
            'strip_namespace': False,
            'preserve_comments': True,
            'preserve_pis': True,
            'preserve_cdata': True
        }
        
        # Merge with provided options
        if options and options.additional_options:
            default_options.update(options.additional_options)
        
        # Decode bytes to string
        encoding = str(default_options['encoding'])
        try:
            xml_str = data.decode(encoding)
        except UnicodeDecodeError:
            # Try common encodings
            for enc in ['utf-8', 'utf-16', 'iso-8859-1', 'cp1256']:
                try:
                    xml_str = data.decode(enc)
                    encoding = enc
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Cannot decode XML data with encoding {encoding}")
        
        # Parse XML
        try:
            # Use minidom for better handling of comments, PIs, etc.
            dom = minidom.parseString(xml_str)
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {e}")
        
        # Convert to DSDM DataNode
        root_node = self._dom_to_dsdm(
            dom.documentElement, 
            path="$", 
            options=default_options
        )
        if not root_node:
            raise ValueError(f"Failed to parse XML")
            
        # Create document metadata
        doc_metadata: Dict[str, Any] = {
            "document_id": document_id,
            "source_name": source_name,
            "size_bytes": len(data),
            "encoding": encoding,
            "media_type": "application/xml"
        }
        
        # Add additional metadata if provided
        if metadata:
            doc_metadata.update(metadata)
        
        # Add document-level information
        if dom.doctype:
            doc_metadata["doctype"] = {
                "name": dom.doctype.name,
                "public_id": dom.doctype.publicId,
                "system_id": dom.doctype.systemId
            }
        
        # Create capabilities
        capabilities = DataDocumentCapabilities(
            supports_comments=bool(default_options['preserve_comments']),
            supports_namespaces=True,
            supports_attributes=True,
            supports_tags=False,
            supports_binary_payloads=False,
            ordered_mappings=True
        )
        
        mt = detect_by_extension("xml")
        return DataDocument(
            document_id=document_id,
            media_type=mt,
            metadata=doc_metadata,
            title=source_name,
            root=root_node,
            capabilities=capabilities
        )
    
    async def parse_path(
        self, 
        path: Union[str, Path], 
        document_id: str, 
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None
    ) -> BaseDocument:
        """
        Parse XML from file path.
        
        Args:
            path: Path to XML file (str or Path)
            document_id: Unique identifier for the document
            metadata: Additional metadata
            options: Same as parse_bytes
            
        Returns:
            DataDocument with XML structure
        """
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"XML file not found: {source_path}")
        
        try:
            with open(source_path, 'rb') as f:
                data = f.read()
        except IOError as e:
            raise ValueError(f"Cannot read XML file {source_path}: {e}")
        
        # Use parse_bytes with file-specific metadata
        file_metadata = metadata or {}
        file_metadata["source_path"] = str(source_path)
        
        return await self.parse_bytes(
            data, 
            document_id, 
            source_path.name,
            file_metadata,
            options
        )
    
    def _dom_to_dsdm(
        self, 
        node: Optional[Node], 
        path: str, 
        options: Dict[str, Any],
        node_counter: int = 0
    ) -> Optional[DataNode]:
        """
        Convert minidom Node to DSDM DataNode.
        Returns None for nodes that should be skipped (empty text, filtered comments, etc.)
        """
        if node is None:
            return None
            
        node_counter += 1
        node_id = f"xml_node_{node_counter}"
        
        # Handle different node types with isinstance checks
        if node.nodeType == Node.ELEMENT_NODE:
            # Type narrowing with isinstance
            if isinstance(node, Element):
                return self._handle_element_node(node, path, options, node_id, node_counter)
        elif node.nodeType == Node.TEXT_NODE:
            if isinstance(node, Text):
                return self._handle_text_node(node, path, node_id)
        elif node.nodeType == Node.COMMENT_NODE:
            if isinstance(node, Comment):
                return self._handle_comment_node(node, path, node_id, options)
        elif node.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
            if isinstance(node, ProcessingInstruction):
                return self._handle_pi_node(node, path, node_id, options)
        elif node.nodeType == Node.CDATA_SECTION_NODE:
            if isinstance(node, CDATASection):
                return self._handle_cdata_node(node, path, node_id, options)
        elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
            if isinstance(node, DocumentType):
                return self._handle_doctype_node(node, path, node_id)
        
        # Unknown node type - create generic element
        node_name = node.nodeName if hasattr(node, 'nodeName') else "unknown"
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_ELEMENT,
            path=path,
            name=node_name
        )
    
    def _handle_element_node(
        self, 
        node: Element, 
        path: str, 
        options: Dict[str, Any],
        node_id: str,
        node_counter: int
    ) -> DataNode:
        """Handle XML element node."""
        # Get element name (handle namespaces)
        element_name = node.nodeName
        namespace = None
        
        if ':' in element_name and not options.get('strip_namespace'):
            parts = element_name.split(':', 1)
            if len(parts) == 2:
                namespace, local_name = parts
                element_name = local_name
        
        # Create element node
        element_node = DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_ELEMENT,
            path=path,
            name=element_name,
            namespace=namespace
        )
        
        # Handle attributes
        if node.attributes:
            for i in range(node.attributes.length):
                attr_item = node.attributes.item(i)
                if attr_item is None:
                    continue
                
                # Cast to Attr type
                from xml.dom.minidom import Attr
                attr = cast(Attr, attr_item)
                    
                attr_name = attr.name
                attr_namespace = None
                
                if attr_name and ':' in attr_name and not options.get('strip_namespace'):
                    parts = attr_name.split(':', 1)
                    if len(parts) == 2:
                        attr_namespace, attr_local = parts
                        attr_name = attr_local
                
                attr_path = f"{path}@{attr_name}"
                attr_node = DataNode(
                    node_id=f"{node_id}_attr_{i}",
                    kind=DataNodeKind.XML_ATTRIBUTE,
                    path=attr_path,
                    name=attr_name,
                    namespace=attr_namespace,
                    value=DataValue(
                        scalar_type=ScalarType.STRING,
                        value=attr.value,
                        lexical_value=attr.value
                    )
                )
                element_node.attributes.append(attr_node)
        
        # Handle namespace declarations
        if node.hasAttribute("xmlns"):
            xmlns_value = node.getAttribute("xmlns")
            if xmlns_value:
                element_node.metadata["xmlns"] = {"": xmlns_value}
        
        # Handle children
        child_counter = node_counter
        for child in node.childNodes:
            child_name = child.nodeName if hasattr(child, 'nodeName') and child.nodeName else f"child_{len(element_node.children)}"
            child_path = f"{path}.{child_name}"
            
            child_node = self._dom_to_dsdm(
                child, 
                child_path, 
                options, 
                child_counter
            )
            
            if child_node is not None:
                element_node.children.append(child_node)
                child_counter += 1
        
        return element_node
    
    def _handle_text_node(self, node: Text, path: str, node_id: str) -> Optional[DataNode]:
        """Handle XML text node."""
        text = node.data.strip()
        if not text:  # Skip empty text nodes
            return None
        
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_TEXT,
            path=path,
            name="#text",
            value=DataValue(
                scalar_type=ScalarType.STRING,
                value=text,
                lexical_value=text
            )
        )
    
    def _handle_comment_node(
        self, 
        node: Comment, 
        path: str, 
        node_id: str,
        options: Dict[str, Any]
    ) -> Optional[DataNode]:
        """Handle XML comment node."""
        if not options.get('preserve_comments', True):
            return None
        
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_COMMENT,
            path=path,
            name="#comment",
            value=DataValue(
                scalar_type=ScalarType.STRING,
                value=node.data,
                lexical_value=node.data
            )
        )
    
    def _handle_pi_node(
        self, 
        node: ProcessingInstruction, 
        path: str, 
        node_id: str,
        options: Dict[str, Any]
    ) -> Optional[DataNode]:
        """Handle XML processing instruction node."""
        if not options.get('preserve_pis', True):
            return None
        
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_PROCESSING_INSTRUCTION,
            path=path,
            name=node.target,
            value=DataValue(
                scalar_type=ScalarType.STRING,
                value=node.data,
                lexical_value=node.data
            )
        )
    
    def _handle_cdata_node(
        self, 
        node: CDATASection, 
        path: str, 
        node_id: str,
        options: Dict[str, Any]
    ) -> Optional[DataNode]:
        """Handle XML CDATA node."""
        if not options.get('preserve_cdata', True):
            # Treat as text node
            return self._handle_text_node(node, path, node_id)
        
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_CDATA,
            path=path,
            name="#cdata",
            value=DataValue(
                scalar_type=ScalarType.STRING,
                value=node.data,
                lexical_value=node.data
            )
        )
    
    def _handle_doctype_node(self, node: DocumentType, path: str, node_id: str) -> DataNode:
        """Handle XML DOCTYPE node."""
        doctype_str = node.name or ""
        if node.publicId:
            doctype_str += f" PUBLIC \"{node.publicId}\""
        if node.systemId:
            if not node.publicId:
                doctype_str += f" SYSTEM"
            doctype_str += f" \"{node.systemId}\""
        
        return DataNode(
            node_id=node_id,
            kind=DataNodeKind.XML_DOCTYPE,
            path=path,
            name="#doctype",
            value=DataValue(
                scalar_type=ScalarType.STRING,
                value=doctype_str.strip(),
                lexical_value=doctype_str.strip()
            )
        )
    
    def get_supported_media_types(self) -> list[str]:
        """Get list of supported media types."""
        return self._supported_media_types
    
    def get_supported_extensions(self) -> list[str]:
        """Get list of supported file extensions."""
        return self._supported_extensions
