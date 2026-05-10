# engines/document/parsers/docx_parser/docx_table_parser.py
"""
DOCX Table Parser
Extracts and parses tables from DOCX documents into intermediate models.
"""
import xml.etree.ElementTree as ET

from .docx_models import (
    DOCXTable,
)
from .docx_utils import DocxUtils
from .docx_utils import safe_findall


class DocxTableParser:
    """Parser for DOCX tables."""

    def __init__(self, docx_utils: DocxUtils | None = None):
        self.docx_utils = docx_utils or DocxUtils()

    def parse_table(self, tbl_elem: ET.Element) -> DOCXTable | None:
        """Parse a table from tbl element."""
        # Delegate to DOCXExtractor's table parsing
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        return extractor._parse_table(tbl_elem)

    def parse_all_tables(self, body_elem: ET.Element) -> list[DOCXTable]:
        """Parse all tables from a body element."""
        tables = []
        for tbl_elem in safe_findall(body_elem, './/w:tbl'):
            table = self.parse_table(tbl_elem)
            if table:
                tables.append(table)
        return tables
