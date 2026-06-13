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


class DOCXExtractorStructural:
    """Mixin providing DOCX extractor structural methods."""

    def _extract_headers(self) -> dict[str, DOCXHeaderFooter]:
        """Extract all headers from the document."""
        headers: dict[str, DOCXHeaderFooter] = {}

        # Get header relationships from document relationships
        doc_rels = self._relationships.get('document', {})

        for rel_id, target in doc_rels.items():
            if 'header' in target.lower():
                header_path = f'word/{target}'
                header_xml = self._get_xml_document(header_path)

                if header_xml is not None:
                    header_type = self._get_header_footer_type(rel_id)
                    header = self._parse_header_footer(header_xml, rel_id, header_type)
                    headers[rel_id] = header

                    # Also load relationships for this header
                    header_rels = self._get_relationships_for_part(header_path)
                    header.relationships = header_rels

        return headers


    def _extract_footers(self) -> dict[str, DOCXHeaderFooter]:
        """Extract all footers from the document."""
        footers: dict[str, DOCXHeaderFooter] = {}

        doc_rels = self._relationships.get('document', {})

        for rel_id, target in doc_rels.items():
            if 'footer' in target.lower():
                footer_path = f'word/{target}'
                footer_xml = self._get_xml_document(footer_path)

                if footer_xml is not None:
                    footer_type = self._get_header_footer_type(rel_id)
                    footer = self._parse_header_footer(footer_xml, rel_id, footer_type)
                    footers[rel_id] = footer

                    # Load relationships
                    footer_rels = self._get_relationships_for_part(footer_path)
                    footer.relationships = footer_rels

        return footers


    def _get_header_footer_type(self, rel_id: str) -> Literal['default', 'first', 'even']:
        """Determine header/footer type from relationship ID."""
        if 'first' in rel_id.lower():
            return 'first'
        elif 'even' in rel_id.lower():
            return 'even'
        else:
            return 'default'


    def _parse_header_footer(
        self,
        elem: ET.Element,
        hf_id: str,
        hf_type: Literal['default', 'first', 'even']
    ) -> DOCXHeaderFooter:
        hf = DOCXHeaderFooter(
            header_footer_id=hf_id,
            header_footer_type=hf_type
        )

        content = self._parse_block_elements(elem)
        hf.content = [item for item in content if isinstance(item, (DOCXParagraph, DOCXTable))]

        return hf

    def _extract_comments(self) -> dict[str, DOCXComment]:
        """Extract comments from comments.xml."""
        comments_xml = self._get_xml_document('word/comments.xml')
        if comments_xml is None:
            return {}

        comments: dict[str, DOCXComment] = {}

        {'w': NS['w']}

        for comment_elem in safe_findall(comments_xml, './/w:comment'):
            comment_id = comment_elem.get(f'{{{NS["w"]}}}id')
            if not comment_id:
                continue

            author = comment_elem.get(f'{{{NS["w"]}}}author', '')
            date = comment_elem.get(f'{{{NS["w"]}}}date', '')
            initials = comment_elem.get(f'{{{NS["w"]}}}initials')

            comment = DOCXComment(
                comment_id=comment_id,
                author=author,
                date=date,
                initials=initials
            )

            # Parse comment content (paragraphs)
            for para_elem in safe_findall(comment_elem, './/w:p'):
                para = self._parse_paragraph(para_elem)
                comment.content.append(para)

            comments[comment_id] = comment

        self._comments = comments
        return comments


    def _extract_footnotes(self) -> dict[str, DOCXFootnoteEndnote]:
        """Extract footnotes from footnotes.xml."""
        return self._extract_notes('word/footnotes.xml', 'footnote')


    def _extract_endnotes(self) -> dict[str, DOCXFootnoteEndnote]:
        """Extract endnotes from endnotes.xml."""
        return self._extract_notes('word/endnotes.xml', 'endnote')


    def _extract_notes(self, path: str, note_type: Literal['footnote', 'endnote']) -> dict[str, DOCXFootnoteEndnote]:
        """Extract footnotes or endnotes."""
        notes_xml = self._get_xml_document(path)
        if notes_xml is None:
            return {}

        notes: dict[str, DOCXFootnoteEndnote] = {}

        for note_elem in safe_findall(notes_xml, './/w:footnote') + safe_findall(notes_xml, './/w:endnote'):
            note_id = note_elem.get(f'{{{NS["w"]}}}id')
            if not note_id:
                continue

            note = DOCXFootnoteEndnote(
                note_id=note_id,
                note_type=note_type
            )

            # Parse note content
            for para_elem in safe_findall(note_elem, './/w:p'):
                para = self._parse_paragraph(para_elem)
                note.content.append(para)

            notes[note_id] = note

        return notes


    def _extract_rtl_properties(self, doc: DOCXDocument):
        """Extract RTL properties at document, section, and paragraph levels."""
        rtl = DOCXRTLProperties()

        for section in doc.sections:
            if section.text_direction == TextDirection.RTL:
                rtl.section_rtl = True
            if section.bidi_enabled:
                rtl.section_rtl = True

        doc.rtl_properties = rtl


    def _extract_sections(self) -> list[DOCXSection]:
        """Extract all sections from the document."""
        sections: list[DOCXSection] = []

        doc_xml = self._get_xml_document('word/document.xml')
        if doc_xml is None:
            return sections

        body_elem = safe_find(doc_xml, './/w:body')
        if body_elem is None:
            return sections

        # Find all section properties
        for sect_pr_elem in safe_findall(body_elem, './/w:sectPr'):
            section = self._parse_section_properties(sect_pr_elem)
            sections.append(section)

        return sections


    def _parse_section_properties(self, elem: ET.Element) -> DOCXSection:
        """Parse section properties."""
        section = DOCXSection()

        # Section type (break type)
        type_elem = safe_find(elem, './/w:type')
        if type_elem is not None:
            val = type_elem.get(f'{{{NS["w"]}}}val', 'nextPage')
            if val == 'continuous':
                section.break_type = SectionType.CONTINUOUS
            elif val == 'nextPage':
                section.break_type = SectionType.NEXT_PAGE
            elif val == 'evenPage':
                section.break_type = SectionType.EVEN_PAGE
            elif val == 'oddPage':
                section.break_type = SectionType.ODD_PAGE

        # Page size
        pg_sz_elem = safe_find(elem, './/w:pgSz')
        if pg_sz_elem is not None:
            width = parse_dxa_to_points(pg_sz_elem.get(f'{{{NS["w"]}}}w')) or 12240
            height = parse_dxa_to_points(pg_sz_elem.get(f'{{{NS["w"]}}}h')) or 15840
            orient = cast(Literal['portrait', 'landscape'],pg_sz_elem.get(f'{{{NS["w"]}}}orient', 'portrait'))
            section.page_size = DOCXPageSize(
                width=width,
                height=height,
                orientation=orient
            )

        # Page margins
        pg_mar_elem = safe_find(elem, './/w:pgMar')
        if pg_mar_elem is not None:
            section.margins = DOCXPageMargins(
                top=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}top')) or 1440,
                bottom=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}bottom')) or 1440,
                left=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}left')) or 1440,
                right=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}right')) or 1440,
                header=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}header')),
                footer=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}footer')),
                gutter=parse_dxa_to_points(pg_mar_elem.get(f'{{{NS["w"]}}}gutter'))
            )

        # Columns
        cols_elem = safe_find(elem, './/w:cols')
        if cols_elem is not None:
            count = self._parse_int(cols_elem.get(f'{{{NS["w"]}}}num')) or 1
            equal_width = cols_elem.get(f'{{{NS["w"]}}}equalWidth', '1') != '0'
            space = parse_dxa_to_points(cols_elem.get(f'{{{NS["w"]}}}space'))
            separator = cols_elem.get(f'{{{NS["w"]}}}sep', '0') == '1'

            section.columns = DOCXColumns(
                count=count,
                equal_width=equal_width,
                space_between=space,
                separator=separator
            )

            # Individual column widths
            if not equal_width:
                for col_elem in safe_findall(cols_elem, './/w:col'):
                    width1 = parse_dxa_to_points(col_elem.get(f'{{{NS["w"]}}}w'))
                    if width1:
                        section.columns.widths.append(width1)

# engines/document/parsers/docx_parser/docx_extractor.py (continued from _parse_section_properties)

        # Header/footer references
        for ref_elem in safe_findall(elem, './/w:headerReference'):
            ref_type = ref_elem.get(f'{{{NS["w"]}}}type', 'default')
            ref_id = ref_elem.get(f'{{{NS["r"]}}}id')
            if ref_id:
                if ref_type == 'first':
                    section.header_first_id = ref_id
                elif ref_type == 'even':
                    section.header_even_id = ref_id
                else:
                    section.header_default_id = ref_id

        for ref_elem in safe_findall(elem, './/w:footerReference'):
            ref_type = ref_elem.get(f'{{{NS["w"]}}}type', 'default')
            ref_id = ref_elem.get(f'{{{NS["r"]}}}id')
            if ref_id:
                if ref_type == 'first':
                    section.footer_first_id = ref_id
                elif ref_type == 'even':
                    section.footer_even_id = ref_id
                else:
                    section.footer_default_id = ref_id

        # Page numbering
        pg_num_elem = safe_find(elem, './/w:pgNumType')
        if pg_num_elem is not None:
            section.page_number_start = self._parse_int(pg_num_elem.get(f'{{{NS["w"]}}}start'))
            section.page_number_format = pg_num_elem.get(f'{{{NS["w"]}}}fmt')

        # Line numbering
        ln_num_elem = safe_find(elem, './/w:lnNumType')
        if ln_num_elem is not None:
            section.line_numbering = {
                'count_by': self._parse_int(ln_num_elem.get(f'{{{NS["w"]}}}countBy')),
                'start': self._parse_int(ln_num_elem.get(f'{{{NS["w"]}}}start')),
                'distance': parse_dxa_to_points(ln_num_elem.get(f'{{{NS["w"]}}}distance')),
                'restart': ln_num_elem.get(f'{{{NS["w"]}}}restart', 'newPage')
            }

        return section


