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


class DOCXExtractorContent:
    """Mixin providing DOCX extractor content methods."""

    def _extract_document_body(self) -> list[DOCXParagraph | DOCXTable | DOCXSection]:
        """Extract the main document body content."""
        doc_xml = self._get_xml_document('word/document.xml')
        if doc_xml is None:
            return []

        body_elem = safe_find(doc_xml, './/w:body')
        if body_elem is None:
            return []

        return self._parse_block_elements(body_elem)


    def _parse_block_elements(self, parent_elem: ET.Element) -> list[DOCXParagraph | DOCXTable | DOCXSection]:
        """Parse block-level elements (paragraphs, tables, sections)."""
        elements: list[DOCXParagraph | DOCXTable | DOCXSection] = []

        for elem in parent_elem:
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

            if tag == 'p':
                # Paragraph
                para = self._parse_paragraph(elem)
                elements.append(para)

            elif tag == 'tbl':
                # Table
                table = self._parse_table(elem)
                elements.append(table)

            elif tag == 'sectPr':
                # Section properties (section break)
                section = self._parse_section_properties(elem)
                section.break_type = SectionType.CONTINUOUS
                elements.append(section)

        return elements

# engines/document/parsers/docx_parser/docx_extractor.py (continued)


    def _parse_paragraph(self, elem: ET.Element) -> DOCXParagraph:
        """Parse a paragraph element."""
        para = DOCXParagraph()

        # Parse properties
        ppr_elem = safe_find(elem, './/w:pPr')
        if ppr_elem is not None:
            para.properties = self._parse_paragraph_properties(ppr_elem)

        # Parse runs and other content
        run_content = DOCXRunContent()

        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'r':
                # Text run
                text_run = self._parse_run(child)
                run_content.items.append(text_run)

            elif tag == 'drawing':
                # Drawing (image, chart, shape)
                drawing = self._parse_drawing(child)
                if drawing:
                    run_content.items.append(drawing)

            elif tag == 'fldSimple':
                # Simple field
                field = self._parse_simple_field(child)
                if field:
                    run_content.items.append(field)

            elif tag == 'hyperlink':
                # Hyperlink
                hyperlink_content = self._parse_hyperlink(child)
                run_content.items.extend(hyperlink_content.items)

            elif tag == 'oMath' or tag == 'oMathPara':
                # Math equation - store as special field for later conversion
                assert self.math_parser is not None
                math = self.math_parser.parse_math(child, is_display=(tag == 'oMathPara'))
                if math:
                    # Create a field to hold the math
                    math_field = DOCXField(
                        field_type='MATH',
                        result=math
                    )
                    run_content.items.append(math_field)

            elif tag == 'br':
                # Break (line, page, column)
                break_obj = self._parse_break(child)
                if break_obj:
                    run_content.items.append(break_obj)

            elif tag == 'tab':
                # Tab character
                run_content.items.append(DOCXTab())

            elif tag == 'sym':
                # Symbol
                symbol = self._parse_symbol(child)
                if symbol:
                    run_content.items.append(symbol)

        para.content = run_content

        # Check for revision tracking
        ppr_change = safe_find(elem, './/w:pPr/w:ins') or safe_find(elem, './/w:pPr/w:del')
        if ppr_change is not None:
            if ppr_change.tag.endswith('ins'):
                para.is_insertion = True
            else:
                para.is_deletion = True
            para.revision_author = ppr_change.get(f'{{{NS["w"]}}}author')
            para.revision_date = ppr_change.get(f'{{{NS["w"]}}}date')

        return para


    def _parse_paragraph_properties(self, elem: ET.Element) -> DOCXParagraphProperties:
        """Parse paragraph properties."""
        props = DOCXParagraphProperties()

        # Style
        style_elem = safe_find(elem, './/w:pStyle')
        if style_elem is not None:
            props.style_id = style_elem.get(f'{{{NS["w"]}}}val')

        # Alignment
        jc_elem = safe_find(elem, './/w:jc')
        if jc_elem is not None:
            val = jc_elem.get(f'{{{NS["w"]}}}val', 'left')
            try:
                props.alignment = ParagraphAlignment(val)
            except ValueError:
                props.alignment = ParagraphAlignment.LEFT

        # Indentation
        ind_elem = safe_find(elem, './/w:ind')
        if ind_elem is not None:
            props.indent_left = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}left'))
            props.indent_right = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}right'))
            props.indent_first_line = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}firstLine'))
            props.indent_hanging = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}hanging'))

        # Spacing
        spacing_elem = safe_find(elem, './/w:spacing')
        if spacing_elem is not None:
            props.spacing_before = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}before'))
            props.spacing_after = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}after'))
            props.line_spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}line'))

            rule = spacing_elem.get(f'{{{NS["w"]}}}lineRule')
            if rule == 'auto':
                props.line_spacing_rule = 'auto'
            elif rule == 'exact':
                props.line_spacing_rule = 'exact'
            elif rule == 'atLeast':
                props.line_spacing_rule = 'at_least'

        # Pagination
        props.keep_lines_together = safe_find(elem, './/w:keepLines') is not None
        props.keep_with_next = safe_find(elem, './/w:keepNext') is not None
        props.page_break_before = safe_find(elem, './/w:pageBreakBefore') is not None
        props.widow_control = safe_find(elem, './/w:widowControl') is None  # Default is True, so False if element missing

        # Borders
        for border_type in ['top', 'bottom', 'left', 'right']:
            border_elem = safe_find(elem, f'.//w:{border_type[:1]}Bdr')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    setattr(props, f'border_{border_type}', border_info)

        # Shading
        shading_elem = safe_find(elem, './/w:shd')
        if shading_elem is not None:
            shading_info = parse_shading_element(shading_elem)
            props.shading_fill = shading_info.get('fill')
            props.shading_pattern = shading_info.get('pattern')

        # Outline level (heading level)
        outline_elem = safe_find(elem, './/w:outlineLvl')
        if outline_elem is not None:
            props.outline_level = self._parse_int(outline_elem.get(f'{{{NS["w"]}}}val'))

        # Text direction
        text_dir_elem = safe_find(elem, './/w:textDirection')
        if text_dir_elem is not None:
            val = text_dir_elem.get(f'{{{NS["w"]}}}val', 'lrTb')
            if val == 'rl' or val == 'tbRl':
                props.text_direction = TextDirection.RTL

        # Numbering
        num_pr_elem = safe_find(elem, './/w:numPr')
        if num_pr_elem is not None:
            ilvl_elem = safe_find(num_pr_elem, './/w:ilvl')
            if ilvl_elem is not None:
                props.numbering_level = self._parse_int(ilvl_elem.get(f'{{{NS["w"]}}}val'))

            num_id_elem = safe_find(num_pr_elem, './/w:numId')
            if num_id_elem is not None:
                props.numbering_id = num_id_elem.get(f'{{{NS["w"]}}}val')

        # Tabs
        tabs_elem = safe_find(elem, './/w:tabs')
        if tabs_elem is not None:
            for tab_elem in safe_findall(tabs_elem, './/w:tab'):
                tab_info = {
                    'position': parse_dxa_to_points(tab_elem.get(f'{{{NS["w"]}}}pos')),
                    'alignment': tab_elem.get(f'{{{NS["w"]}}}val', 'left'),
                    'leader': tab_elem.get(f'{{{NS["w"]}}}leader', 'none')
                }
                props.tabs.append(tab_info)

        return props


    def _parse_run(self, elem: ET.Element) -> DOCXTextRun:
        """Parse a run element."""
        text_run = DOCXTextRun(text='')

        # Extract text
        text_parts: list[str] = []
        for t_elem in safe_findall(elem, './/w:t'):
            if t_elem.text:
                text_parts.append(t_elem.text)

        # Handle special characters
        for cr_elem in safe_findall(elem, './/w:cr'):
            text_parts.append('\n')
        for br_elem in safe_findall(elem, './/w:br'):
            text_parts.append('\n')
        for tab_elem in safe_findall(elem, './/w:tab'):
            text_parts.append('\t')

        text_run.text = ''.join(text_parts)

        # Parse run properties
        rpr_elem = safe_find(elem, './/w:rPr')
        if rpr_elem is not None:
            text_run.properties = self._parse_run_properties(rpr_elem)

        # Check for revision tracking
        if rpr_elem is not None:
            ins_elem = safe_find(rpr_elem, './/w:ins')
            if ins_elem is not None:
                text_run.is_insertion = True
                text_run.revision_author = ins_elem.get(f'{{{NS["w"]}}}author')
                text_run.revision_date = ins_elem.get(f'{{{NS["w"]}}}date')
                text_run.revision_id = self._parse_int(ins_elem.get(f'{{{NS["w"]}}}id'))

            del_elem = safe_find(rpr_elem, './/w:del')
            if del_elem is not None:
                text_run.is_deletion = True
                text_run.revision_author = del_elem.get(f'{{{NS["w"]}}}author')
                text_run.revision_date = del_elem.get(f'{{{NS["w"]}}}date')
                text_run.revision_id = self._parse_int(del_elem.get(f'{{{NS["w"]}}}id'))

        return text_run


    def _parse_run_properties(self, elem: ET.Element) -> DOCXRunProperties:
        """Parse run properties."""
        props = DOCXRunProperties()

        # Bold
        bold_elem = safe_find(elem, './/w:b')
        if bold_elem is not None:
            props.bold = bold_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Italic
        italic_elem = safe_find(elem, './/w:i')
        if italic_elem is not None:
            props.italic = italic_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Underline
        underline_elem = safe_find(elem, './/w:u')
        if underline_elem is not None:
            props.underline = underline_elem.get(f'{{{NS["w"]}}}val', 'single')

        # Strike through
        strike_elem = safe_find(elem, './/w:strike')
        if strike_elem is not None:
            props.strike = strike_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Double strike
        dstrike_elem = safe_find(elem, './/w:dstrike')
        if dstrike_elem is not None:
            props.double_strike = dstrike_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Superscript / Subscript
        vert_align_elem = safe_find(elem, './/w:vertAlign')
        if vert_align_elem is not None:
            val = vert_align_elem.get(f'{{{NS["w"]}}}val')
            if val == 'superscript':
                props.superscript = True
            elif val == 'subscript':
                props.subscript = True

        # Small caps / All caps
        small_caps_elem = safe_find(elem, './/w:smallCaps')
        if small_caps_elem is not None:
            props.small_caps = small_caps_elem.get(f'{{{NS["w"]}}}val') != 'false'

        caps_elem = safe_find(elem, './/w:caps')
        if caps_elem is not None:
            props.all_caps = caps_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Highlight
        highlight_elem = safe_find(elem, './/w:highlight')
        if highlight_elem is not None:
            props.highlight = highlight_elem.get(f'{{{NS["w"]}}}val')

        # Color
        color_elem = safe_find(elem, './/w:color')
        if color_elem is not None:
            props.color = color_elem.get(f'{{{NS["w"]}}}val')

        # Font name
        font_elem = safe_find(elem, './/w:rFonts')
        if font_elem is not None:
            props.font_name = font_elem.get(f'{{{NS["w"]}}}ascii') or font_elem.get(f'{{{NS["w"]}}}hAnsi')

        # Font size
        sz_elem = safe_find(elem, './/w:sz')
        if sz_elem is not None:
            sz_val = sz_elem.get(f'{{{NS["w"]}}}val')
            if sz_val is not None:
                val_int = self._parse_int(sz_val)
                if val_int is not None:
                    props.font_size = val_int / 2.0

        sz_cs_elem = safe_find(elem, './/w:szCs')
        if sz_cs_elem is not None:
            sz_val = sz_cs_elem.get(f'{{{NS["w"]}}}val')
            if sz_val:
                val_int = self._parse_int(sz_val)
                if val_int is not None:
                    props.font_size_cs = val_int / 2.0

        # Kerning
        kern_elem = safe_find(elem, './/w:kern')
        if kern_elem is not None:
            props.kerning = parse_dxa_to_points(kern_elem.get(f'{{{NS["w"]}}}val'))

        # Spacing
        spacing_elem = safe_find(elem, './/w:spacing')
        if spacing_elem is not None:
            props.spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}val'))

        # Position (raised/lowered text)
        position_elem = safe_find(elem, './/w:position')
        if position_elem is not None:
            props.position = parse_dxa_to_points(position_elem.get(f'{{{NS["w"]}}}val'))

        # Language
        lang_elem = safe_find(elem, './/w:lang')
        if lang_elem is not None:
            props.language = lang_elem.get(f'{{{NS["w"]}}}val')

        # No proof (spell check)
        props.no_proof = safe_find(elem, './/w:noProof') is not None

        # Web hidden
        web_hidden_elem = safe_find(elem, './/w:webHidden')
        if web_hidden_elem is not None:
            props.web_hidden = web_hidden_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Shadow
        shadow_elem = safe_find(elem, './/w:shadow')
        if shadow_elem is not None:
            props.shadow = shadow_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Outline
        outline_elem = safe_find(elem, './/w:outline')
        if outline_elem is not None:
            props.outline = outline_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Emboss
        emboss_elem = safe_find(elem, './/w:emboss')
        if emboss_elem is not None:
            props.emboss = emboss_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Imprint
        imprint_elem = safe_find(elem, './/w:imprint')
        if imprint_elem is not None:
            props.imprint = imprint_elem.get(f'{{{NS["w"]}}}val') != 'false'

        # Vanished (hidden text)
        vanish_elem = safe_find(elem, './/w:vanish')
        if vanish_elem is not None:
            props.vanished = vanish_elem.get(f'{{{NS["w"]}}}val') != 'false'

        return props


    def _parse_drawing(self, elem: ET.Element) -> DOCXDrawing | None:
        """Parse a drawing element (image, chart, shape)."""
        # Look for inline drawing
        inline_elem = safe_find(elem, './/wp:inline', {'wp': NS.get('wp', '')})
        if inline_elem is None:
            inline_elem = safe_find(elem, './/wp:anchor', {'wp': NS.get('wp', '')})

        if inline_elem is None:
            return None

        drawing = DOCXDrawing(relationship_id='')

        # Get relationship ID for image
        blip_elem = safe_find(inline_elem, './/a:blip', {'a': NS.get('a', '')})
        if blip_elem is not None:
            drawing.relationship_id = blip_elem.get(f'{{{NS.get("r", "")}}}embed', '')

        # Get dimensions
        extent_elem = safe_find(inline_elem, './/wp:extent', {'wp': NS.get('wp', '')})
        if extent_elem is not None:
            drawing.width = self._parse_int(extent_elem.get('cx'))
            drawing.height = self._parse_int(extent_elem.get('cy'))

        # Get name and description
        docpr_elem = safe_find(inline_elem, './/wp:docPr', {'wp': NS.get('wp', '')})
        if docpr_elem is not None:
            drawing.name = docpr_elem.get('name')
            drawing.description = docpr_elem.get('descr')

        return drawing

        # Alternative text
        alt_text_elem = safe_find(inline_elem, './/a:extLst/a:ext//a16:altText',
                                {'a': NS.get('a', ''), 'a16': NS.get('a16', '')})
        if alt_text_elem is not None:
            drawing.alt_text = alt_text_elem.get('altText')

        # Determine drawing type and relationship ID
        graphic_elem = safe_find(inline_elem, './/a:graphic', {'a': NS.get('a', '')})
        if graphic_elem is not None:
            graphic_data = safe_find(graphic_elem, './/a:graphicData', {'a': NS.get('a', '')})
            if graphic_data is not None:
                uri = graphic_data.get('uri', '')
                if 'chart' in uri:
                    drawing.drawing_type = 'chart'
                    # Find the chart reference ID
                    chart_el = safe_find(graphic_data, './/c:chart',
                                        {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'})
                    if chart_el is not None:
                        drawing.relationship_id = chart_el.get(f'{{{NS.get("r", "")}}}id', '')
                elif 'diagram' in uri:
                    drawing.drawing_type = 'diagram'
                    # Find the <dgm:relIds r:id="...">
                    rel_ids = safe_find(graphic_data, './/dgm:relIds', {'dgm': NS.get('dgm', '')})
                    if rel_ids is not None:
                        drawing.relationship_id = rel_ids.get(f'{{{NS["r"]}}}id', '')

    def _parse_simple_field(self, elem: ET.Element) -> DOCXField | None:
        """Parse a simple field element."""
        field = DOCXField(field_type='')

        instr = elem.get(f'{{{NS["w"]}}}instr', '')
        if instr:
            # Parse instruction (e.g., "PAGE", "DATE \@ \"MMMM d, yyyy\"")
            parts = instr.split(' ', 1)
            field.field_type = parts[0] if parts else ''
            field.instruction = parts[1] if len(parts) > 1 else None

        # Get field result (computed value)
        result_text: list[str] = []
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'r':
                for t_elem in safe_findall(child, './/w:t'):
                    if t_elem.text:
                        result_text.append(t_elem.text)

        field.result = ''.join(result_text) if result_text else None

        return field


    def _parse_hyperlink(self, elem: ET.Element) -> DOCXRunContent:
        """Parse a hyperlink element."""
        content = DOCXRunContent()

        # Get hyperlink target
        rel_id = elem.get(f'{{{NS.get("r", "")}}}id')
        anchor = elem.get(f'{{{NS["w"]}}}anchor')

        # Parse runs inside hyperlink
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'r':
                text_run = self._parse_run(child)
                # Add hyperlink info to run properties
                if rel_id:
                    text_run.properties.additional_properties['hyperlink_rel_id'] = rel_id
                if anchor:
                    text_run.properties.additional_properties['hyperlink_anchor'] = anchor
                content.items.append(text_run)

        return content


    def _parse_break(self, elem: ET.Element) -> DOCXBreak | None:
        """Parse a break element."""
        break_obj = DOCXBreak(break_type='line')

        break_type = elem.get(f'{{{NS["w"]}}}type')
        if break_type == 'page':
            break_obj.break_type = 'page'
        elif break_type == 'column':
            break_obj.break_type = 'column'
        elif break_type == 'textWrapping':
            break_obj.break_type = 'text_wrapping'

        clear = elem.get(f'{{{NS["w"]}}}clear')
        if clear:
            break_obj.clear = clear

        return break_obj


    def _parse_symbol(self, elem: ET.Element) -> DOCXSymbol | None:
        """Parse a symbol element."""
        char = elem.get(f'{{{NS["w"]}}}char')
        if not char:
            return None

        symbol = DOCXSymbol(char=char)

        font = elem.get(f'{{{NS["w"]}}}font')
        if font:
            symbol.font = font

        return symbol


    def _parse_table(self, elem: ET.Element) -> DOCXTable:
        """Parse a table element."""
        table = DOCXTable()

        # Parse table properties
        tbl_pr_elem = safe_find(elem, './/w:tblPr')
        if tbl_pr_elem is not None:
            table.properties = self._parse_table_properties(tbl_pr_elem)

        # Parse table grid
        tbl_grid_elem = safe_find(elem, './/w:tblGrid')
        if tbl_grid_elem is not None:
            table.grid = self._parse_table_grid(tbl_grid_elem)

        # Parse rows
        row_index = 0
        for tr_elem in safe_findall(elem, './/w:tr'):
            row = self._parse_table_row(tr_elem, row_index)
            table.rows.append(row)
            row_index += 1

        return table


    def _parse_table_properties(self, elem: ET.Element) -> DOCXTableProperties:
        """Parse table properties."""
        props = DOCXTableProperties()

        # Style
        style_elem = safe_find(elem, './/w:tblStyle')
        if style_elem is not None:
            props.style_id = style_elem.get(f'{{{NS["w"]}}}val')

        # Alignment
        jc_elem = safe_find(elem, './/w:tblJc')
        if jc_elem is not None:
            val = jc_elem.get(f'{{{NS["w"]}}}val', 'left')
            try:
                props.alignment = ParagraphAlignment(val)
            except ValueError:
                props.alignment = ParagraphAlignment.LEFT

        # Indent
        ind_elem = safe_find(elem, './/w:tblInd')
        if ind_elem is not None:
            props.indent_left = parse_dxa_to_points(ind_elem.get(f'{{{NS["w"]}}}val'))

        # Borders
        for border_type in ['top', 'bottom', 'left', 'right', 'insideH', 'insideV']:
            border_elem = safe_find(elem, f'.//w:{border_type}')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    attr_name = f'border_{border_type.lower()}'
                    if border_type == 'insideH':
                        attr_name = 'border_inside_horizontal'
                    elif border_type == 'insideV':
                        attr_name = 'border_inside_vertical'
                    setattr(props, attr_name, border_info)

        # Cell margins
        cell_mar_elem = safe_find(elem, './/w:tblCellMar')
        if cell_mar_elem is not None:
            margins: dict[str, float] = {}
            for margin_type in ['top', 'bottom', 'left', 'right']:
                mar_elem = safe_find(cell_mar_elem, f'.//w:{margin_type}')
                if mar_elem is not None:
                    val1 = parse_dxa_to_points(mar_elem.get(f'{{{NS["w"]}}}val'))
                    if val1 is not None:
                        margins[margin_type] = val1 if val1 is not None else 0.0
            if margins:
                props.cell_margin_default = margins

        # Cell spacing
        spacing_elem = safe_find(elem, './/w:tblCellSpacing')
        if spacing_elem is not None:
            props.cell_spacing = parse_dxa_to_points(spacing_elem.get(f'{{{NS["w"]}}}val'))

        # Layout
        layout_elem = safe_find(elem, './/w:tblLayout')
        if layout_elem is not None:
            val = layout_elem.get(f'{{{NS["w"]}}}type', 'auto')
            props.layout_type = 'fixed' if val == 'fixed' else 'auto'

        # Width
        width_elem = safe_find(elem, './/w:tblW')
        if width_elem is not None:
            props.width = parse_dxa_to_points(width_elem.get(f'{{{NS["w"]}}}w'))

        # Header row repeat
        props.header_row_repeat = safe_find(elem, './/w:tblHeader') is not None

        return props


    def _parse_table_grid(self, elem: ET.Element) -> DOCXTableGrid:
        """Parse table grid columns."""
        grid = DOCXTableGrid()

        for col_elem in safe_findall(elem, './/w:gridCol'):
            width = parse_dxa_to_points(col_elem.get(f'{{{NS["w"]}}}w'))
            if width is not None:
                grid.column_widths.append(width)

        return grid


    def _parse_table_row(self, elem: ET.Element, row_index: int) -> DOCXTableRow:
        """Parse a table row."""
        row = DOCXTableRow(row_index=row_index)

        # Row properties
        tr_pr_elem = safe_find(elem, './/w:trPr')
        if tr_pr_elem is not None:
            # Header row
            row.is_header = safe_find(tr_pr_elem, './/w:tblHeader') is not None

            # Height
            height_elem = safe_find(tr_pr_elem, './/w:trHeight')
            if height_elem is not None:
                row.height = parse_dxa_to_points(height_elem.get(f'{{{NS["w"]}}}val'))

        # Parse cells
        for tc_elem in safe_findall(elem, './/w:tc'):
            cell = self._parse_table_cell(tc_elem)
            row.cells.append(cell)

        return row


    def _parse_table_cell(self, elem: ET.Element) -> DOCXTableCell:
        """Parse a table cell."""
        cell = DOCXTableCell()

        # Cell properties
        tc_pr_elem = safe_find(elem, './/w:tcPr')
        if tc_pr_elem is not None:
            cell.properties = self._parse_table_cell_properties(tc_pr_elem)

        # Parse cell content
        for child in elem:
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

            if tag == 'p':
                para = self._parse_paragraph(child)
                cell.content.append(para)
            elif tag == 'tbl':
                table = self._parse_table(child)
                cell.content.append(table)

        return cell


    def _parse_table_cell_properties(self, elem: ET.Element) -> DOCXTableCellProperties:
        """Parse table cell properties."""
        props = DOCXTableCellProperties()

        # Width
        width_elem = safe_find(elem, './/w:tcW')
        if width_elem is not None:
            props.width = parse_dxa_to_points(width_elem.get(f'{{{NS["w"]}}}w'))

        # Vertical alignment
        valign_elem = safe_find(elem, './/w:vAlign')
        if valign_elem is not None:
            val = valign_elem.get(f'{{{NS["w"]}}}val', 'top')
            if val == 'center':
                props.vertical_alignment = VerticalAlignment.CENTER
            elif val == 'bottom':
                props.vertical_alignment = VerticalAlignment.BOTTOM
            else:
                props.vertical_alignment = VerticalAlignment.TOP

        # Grid span (column merge)
        grid_span_elem = safe_find(elem, './/w:gridSpan')
        if grid_span_elem is not None:
            props.grid_span = self._parse_int(grid_span_elem.get(f'{{{NS["w"]}}}val')) or 1

        # Vertical merge
        vmerge_elem = safe_find(elem, './/w:vMerge')
        if vmerge_elem is not None:
            val = vmerge_elem.get(f'{{{NS["w"]}}}val', 'continue')
            if val == 'restart':
                props.is_vertically_merged_restart = True
                props.vertical_span = 1
            else:
                props.is_vertically_merged = True

        # Borders
        for border_type in ['top', 'bottom', 'left', 'right']:
            border_elem = safe_find(elem, f'.//w:{border_type}')
            if border_elem is not None:
                border_info = parse_border_element(border_elem)
                if border_info:
                    setattr(props, f'border_{border_type}', border_info)

        # Shading
        shading_elem = safe_find(elem, './/w:shd')
        if shading_elem is not None:
            shading_info = parse_shading_element(shading_elem)
            props.shading_fill = shading_info.get('fill')

        # Margins
        for margin_type in ['top', 'bottom', 'left', 'right']:
            mar_elem = safe_find(elem, f'.//w:{margin_type}')
            if mar_elem is not None:
                setattr(props, f'margin_{margin_type}', parse_dxa_to_points(mar_elem.get(f'{{{NS["w"]}}}val')))

        # Text direction
        text_dir_elem = safe_find(elem, './/w:textDirection')
        if text_dir_elem is not None:
            val = text_dir_elem.get(f'{{{NS["w"]}}}val', 'lrTb')
            if val == 'rl' or val == 'tbRl':
                props.text_direction = TextDirection.RTL

        return props


