# mypy: disable-error-code="attr-defined"

from __future__ import annotations

import os
import re
from datetime import datetime
from io import BytesIO
from typing import Any
from typing import BinaryIO
from typing import cast
from typing import Literal
from xml.etree import ElementTree as ET
from zipfile import ZipFile
from zipfile import BadZipFile

from ....models.base import BinaryEncoding
from .docx_chart_extractor import parse_docx_chart
from .docx_diagram_extractor import parse_diagram
from .docx_image_extractor import DOCXImageExtractor
from .docx_math_parser import OMMLParser
from .docx_models import (
    DOCXBreak, DOCXChartData, DOCXColumns, DOCXComment, DOCXComplexField,
    DOCXCoreProperties, DOCXCustomProperties, DOCXDocument, DOCXDrawing,
    DOCXExtendedProperties, DOCXField, DOCXFootnoteEndnote, DOCXHeaderFooter,
    DOCXNumberingDefinition, DOCXNumberingInstance, DOCXNumberingLevel,
    DOCXPageMargins, DOCXPageSize, DOCXParagraph, DOCXParagraphProperties,
    DOCXRTLProperties, DOCXRunContent, DOCXRunProperties, DOCXSection,
    DOCXStyle, DOCXSymbol, DOCXTab, DOCXTable, DOCXTableCell,
    DOCXTableCellProperties, DOCXTableGrid, DOCXTableProperties, DOCXTableRow,
    DOCXTextRun, DOCXTOCField, DOCXWatermark, NumberingLevelSuffix,
    ParagraphAlignment, SectionType, TextDirection, VerticalAlignment,
)
from .docx_style_parser import DocxStyleParser
from .docx_table_parser import DocxTableParser
from .docx_utils import get_element_text, NS, parse_border_element
from .docx_utils import parse_dxa_to_points, parse_shading_element
from .docx_utils import safe_find, safe_findall


class DOCXExtractorXML:
    """Mixin providing DOCX extractor xml methods."""

    def extract_document_xml(self) -> ET.Element | None:
        """Extract the main document.xml as an ElementTree Element."""
        return self._get_xml_document('word/document.xml')


    def extract_styles_xml(self) -> ET.Element | None:
        """Extract styles.xml as an ElementTree Element."""
        return self._get_xml_document('word/styles.xml')


    def extract_numbering_xml(self) -> ET.Element | None:
        """Extract numbering.xml as an ElementTree Element."""
        return self._get_xml_document('word/numbering.xml')


    def get_relationship_target(self, rel_id: str, rel_type: str = 'document') -> str | None:
        """
        Get the target path for a relationship ID.
        
        Args:
            rel_id: Relationship ID (e.g., 'rId4')
            rel_type: Relationship type ('document', 'header', 'footer', etc.)
            
        Returns:
            Target path or None
        """
        rels = self._relationships.get(rel_type, {})
        return rels.get(rel_id)


    def _get_xml_document(self, path: str) -> ET.Element | None:
        """
        Get an XML document from the ZIP archive.
        
        Args:
            path: Path inside the ZIP archive
            
        Returns:
            ElementTree Element or None
        """
        if path in self._xml_cache:
            return self._xml_cache[path]

        assert self.zip_file is not None, "ZIP file not opened"
        try:
            xml_content = self.zip_file.read(path)
            root = ET.fromstring(xml_content)
            self._xml_cache[path] = root
            return root
        except (KeyError, ET.ParseError):
            return None


    def _extract_all_relationships(self):
        """Extract all relationship files from the DOCX."""
        # Main document relationships
        self._relationships['document'] = self._extract_relationships('word/_rels/document.xml.rels')

        # Other parts (headers, footers, etc. will be extracted on demand)


    def _extract_relationships(self, rels_path: str) -> dict[str, str]:
        """
        Extract relationships from a .rels file.
        
        Args:
            rels_path: Path to the .rels file in ZIP
            
        Returns:
            Dictionary mapping rel_id to target path
        """
        relationships: dict[str, str] = {}

        rels_xml = self._get_xml_document(rels_path)
        if rels_xml is None:
            return relationships

        ns_map = {
            'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
        }

        for rel_elem in safe_findall(rels_xml, './/rel:Relationship', ns_map):
            rel_id = rel_elem.get('Id')
            target = rel_elem.get('Target')
            rel_elem.get('Type', '')

            if rel_id and target:
                relationships[rel_id] = target

        return relationships


    def _get_relationships_for_part(self, part_path: str) -> dict[str, str]:
        """
        Get relationships for a specific document part.
        
        Args:
            part_path: Path to the part (e.g., 'word/document.xml')
            
        Returns:
            Relationship dictionary
        """
        # Convert part path to rels path
        dir_name = os.path.dirname(part_path)
        base_name = os.path.basename(part_path)
        rels_path = f"{dir_name}/_rels/{base_name}.rels"

        if rels_path not in self._relationships:
            self._relationships[rels_path] = self._extract_relationships(rels_path)

        return self._relationships.get(rels_path, {})


    def _get_typed_relationships(self, rel_type: str, target_type: str):
        """Get relationships filtered by type."""
        rels = self._relationships.get(rel_type, {})
        results = []
        for rel_id, target in rels.items():
            rels_path = 'word/_rels/document.xml.rels'
            rels_xml = self._get_xml_document(rels_path)
            if rels_xml is not None:
                ns_map = {'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                for rel_elem in rels_xml.findall('.//rel:Relationship', ns_map):
                    if (rel_elem.get('Id') == rel_id
                            and target_type in (rel_elem.get('Type', ''))):
                        results.append((rel_id, (target, rel_elem.get('Type', ''))))
                        break
        return results


    def _extract_binary_parts(self) -> dict[str, bytes]:
        """Extract all binary parts (images, embedded objects)."""
        binary_parts: dict[str, bytes] = {}

        if self.image_extractor is None:
            return binary_parts

        # Extract all images
        image_payloads = self.image_extractor.extract_all_images()

        # Convert payloads to bytes and store by relationship ID
        for rel_id, payload in image_payloads.items():
            if payload.bytes_content:
                binary_parts[rel_id] = payload.bytes_content
            elif payload.data:
                import base64
                binary_parts[rel_id] = base64.b64decode(payload.data)

        # Extract embedded objects (OLE objects, etc.)
        doc_rels = self._relationships.get('document', {})
        for rel_id, target in doc_rels.items():
            if target.startswith('embeddings/') or target.endswith('.bin') or target.endswith('.ole'):
                try:
                    obj_path = f'word/{target}'
                    assert self.zip_file is not None, "ZIP file not opened"
                    obj_data = self.zip_file.read(obj_path)
                    binary_parts[rel_id] = obj_data
                except (KeyError, BadZipFile):
                    pass

        return binary_parts


