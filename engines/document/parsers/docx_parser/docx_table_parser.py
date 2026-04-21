# engines/document/parsers/docx_parser/docx_table_parser.py
"""
DOCX Table Parser
Extracts and parses tables from DOCX documents into intermediate models.
"""

from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

from .docx_utils import NS, safe_find, safe_findall, get_attribute, parse_dxa_to_points, DocxUtils
from .docx_models import (
    DOCXTable,
    DOCXTableProperties,
    DOCXTableGrid,
    DOCXTableRow,
    DOCXTableCell,
    DOCXTableCellProperties,
    DOCXParagraph,
    ParagraphAlignment,
    VerticalAlignment,
)


class DocxTableParser:
    """Parser for DOCX tables."""
    
    def __init__(self, docx_utils: Optional[DocxUtils] = None):
        self.docx_utils = docx_utils or DocxUtils()
    
    def parse_table(self, tbl_elem: ET.Element) -> Optional[DOCXTable]:
        """Parse a table from tbl element."""
        # Delegate to DOCXExtractor's table parsing
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        return extractor._parse_table(tbl_elem)
    
    def parse_all_tables(self, body_elem: ET.Element) -> List[DOCXTable]:
        """Parse all tables from a body element."""
        tables = []
        for tbl_elem in safe_findall(body_elem, './/w:tbl'):
            table = self.parse_table(tbl_elem)
            if table:
                tables.append(table)
        return tables