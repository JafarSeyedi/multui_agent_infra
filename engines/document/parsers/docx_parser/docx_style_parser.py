# engines/document/parsers/docx_parser/docx_style_parser.py
"""
DOCX Style Parser
Extracts and parses styles from DOCX documents into intermediate models.
"""

from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

from .docx_utils import NS, safe_find, safe_findall, get_attribute, DocxUtils
from .docx_models import (
    DOCXStyle,
    DOCXStyleRunProperties,
    DOCXStyleParagraphProperties,
    DOCXStyleTableProperties,
    DOCXRunProperties,
    DOCXParagraphProperties,
    DOCXTableProperties,
    ParagraphAlignment,
)


class DocxStyleParser:
    """Parser for DOCX styles."""
    
    def __init__(self, docx_utils: Optional[DocxUtils] = None):
        self.docx_utils = docx_utils or DocxUtils()
    
    def parse_styles(self, styles_xml: ET.Element) -> Dict[str, DOCXStyle]:
        """Parse styles from styles.xml element."""
        styles = {}
        
        for style_elem in safe_findall(styles_xml, './/w:style'):
            style = self._parse_style(style_elem)
            if style:
                styles[style.style_id] = style
        
        return styles
    
    def _parse_style(self, style_elem: ET.Element) -> Optional[DOCXStyle]:
        """Parse a single style element."""
        style_id = get_attribute(style_elem, 'styleId', 'w')
        if not style_id:
            return None
        
        # Determine style type
        style_type_elem = safe_find(style_elem, './/w:type')
        style_type = get_attribute(style_type_elem, 'val', 'w') or 'paragraph'
        
        # Get style name
        name_elem = safe_find(style_elem, './/w:name')
        name = get_attribute(name_elem, 'val', 'w') or style_id
        
        # Get based on style
        based_on_elem = safe_find(style_elem, './/w:basedOn')
        based_on = get_attribute(based_on_elem, 'val', 'w')
        
        # Get next style
        next_elem = safe_find(style_elem, './/w:next')
        next_style = get_attribute(next_elem, 'val', 'w')
        
        # Parse run properties
        run_props = None
        rpr_elem = safe_find(style_elem, './/w:rPr')
        if rpr_elem is not None:
            run_props = DOCXStyleRunProperties(
                properties=self._parse_run_properties(rpr_elem),
                based_on=based_on,
                next_style=next_style
            )
        
        # Parse paragraph properties
        para_props = None
        ppr_elem = safe_find(style_elem, './/w:pPr')
        if ppr_elem is not None:
            para_props = DOCXStyleParagraphProperties(
                properties=self._parse_paragraph_properties(ppr_elem)
            )
        
        # Parse table properties
        table_props = None
        tbl_pr_elem = safe_find(style_elem, './/w:tblPr')
        if tbl_pr_elem is not None:
            table_props = DOCXStyleTableProperties(
                properties=self._parse_table_properties(tbl_pr_elem)
            )
        
        return DOCXStyle(
            style_id=style_id,
            name=name,
            style_type=style_type,
            based_on=based_on,
            next_style=next_style,
            run_properties=run_props,
            paragraph_properties=para_props,
            table_properties=table_props
        )
    
    def _parse_run_properties(self, rpr_elem: ET.Element) -> DOCXRunProperties:
        """Parse run properties from rPr element."""
        # Implementation similar to DOCXExtractor._parse_run_properties
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        return extractor._parse_run_properties(rpr_elem)
    
    def _parse_paragraph_properties(self, ppr_elem: ET.Element) -> DOCXParagraphProperties:
        """Parse paragraph properties from pPr element."""
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        return extractor._parse_paragraph_properties(ppr_elem)
    
    def _parse_table_properties(self, tbl_pr_elem: ET.Element) -> DOCXTableProperties:
        """Parse table properties from tblPr element."""
        from .docx_extractor import DOCXExtractor
        extractor = DOCXExtractor()
        return extractor._parse_table_properties(tbl_pr_elem)
    

