"""Mixin for DOCX section and break-related utility methods"""

# mypy: disable-error-code="attr-defined"
import xml.etree.ElementTree as ET
from typing import Any

from .docx_utils_base import OOXML_NAMESPACES


class DocxSection:
    """Mixin providing DOCX section, break, and tab extraction methods"""

    @staticmethod
    def extract_header_footer_info(part_xml: ET.Element) -> dict[str, Any]:
        from .docx_utils import DocxUtils

        header_footer_info = {
            'type': 'unknown',
            'id': None,
            'content': '',
            'paragraphs': 0,
            'images': 0,
            'tables': 0,
            'fields': 0
        }

        try:
            root_tag = part_xml.tag
            if 'header' in root_tag:
                header_footer_info['type'] = 'header'
            elif 'footer' in root_tag:
                header_footer_info['type'] = 'footer'

            content = DocxUtils.extract_text_from_element(part_xml)
            if content:
                header_footer_info['content'] = content

            paragraphs = part_xml.findall('.//w:p', OOXML_NAMESPACES)
            if paragraphs:
                header_footer_info['paragraphs'] = len(paragraphs)

            drawings = part_xml.findall('.//w:drawing', OOXML_NAMESPACES)
            if drawings:
                header_footer_info['images'] = len(drawings)

            tables = part_xml.findall('.//w:tbl', OOXML_NAMESPACES)
            if tables:
                header_footer_info['tables'] = len(tables)

            fields = part_xml.findall('.//w:fldChar', OOXML_NAMESPACES)
            if fields:
                header_footer_info['fields'] = len(fields)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting header/footer information: {str(e)}")

        return header_footer_info

    @staticmethod
    def extract_section_properties(sectPr_elem: ET.Element) -> dict[str, Any]:
        from .docx_utils import DocxUtils

        section_info: dict[str, Any] = {
            'page_size': {'width': 0.0, 'height': 0.0},
            'page_margins': {
                'top': 0.0, 'right': 0.0, 'bottom': 0.0, 'left': 0.0,
                'header': 0.0, 'footer': 0.0, 'gutter': 0.0
            },
            'page_orientation': 'portrait',
            'page_numbering': None,
            'columns': {'count': 1, 'spacing': 0.0, 'equal_width': True},
            'header_references': [],
            'footer_references': [],
            'line_numbers': None,
            'text_direction': 'lrTb'
        }

        try:
            pgSz_elem = sectPr_elem.find('.//w:pgSz', OOXML_NAMESPACES)
            if pgSz_elem is not None:
                width = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                height = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}h')
                orient = pgSz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}orient')

                if width:
                    section_info['page_size']['width'] = DocxUtils.convert_twips_to_points(width)
                if height:
                    section_info['page_size']['height'] = DocxUtils.convert_twips_to_points(height)
                if orient:
                    section_info['page_orientation'] = orient

            pgMar_elem = sectPr_elem.find('.//w:pgMar', OOXML_NAMESPACES)
            if pgMar_elem is not None:
                top = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}top')
                right = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right')
                bottom = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}bottom')
                left = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left')
                header = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}header')
                footer = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footer')
                gutter = pgMar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}gutter')

                if top:
                    section_info['page_margins']['top'] = DocxUtils.convert_twips_to_points(top)
                if right:
                    section_info['page_margins']['right'] = DocxUtils.convert_twips_to_points(right)
                if bottom:
                    section_info['page_margins']['bottom'] = DocxUtils.convert_twips_to_points(bottom)
                if left:
                    section_info['page_margins']['left'] = DocxUtils.convert_twips_to_points(left)
                if header:
                    section_info['page_margins']['header'] = DocxUtils.convert_twips_to_points(header)
                if footer:
                    section_info['page_margins']['footer'] = DocxUtils.convert_twips_to_points(footer)
                if gutter:
                    section_info['page_margins']['gutter'] = DocxUtils.convert_twips_to_points(gutter)

            cols_elem = sectPr_elem.find('.//w:cols', OOXML_NAMESPACES)
            if cols_elem is not None:
                count = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}num')
                spacing = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}space')
                equal_width = cols_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}equalWidth')

                if count:
                    section_info['columns']['count'] = int(count)
                if spacing:
                    section_info['columns']['spacing'] = DocxUtils.convert_twips_to_points(spacing)
                if equal_width:
                    section_info['columns']['equal_width'] = equal_width == '1' or equal_width == 'true'

            header_refs = sectPr_elem.findall('.//w:headerReference', OOXML_NAMESPACES)
            for ref in header_refs:
                ref_type = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                ref_id = ref.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                if ref_type and ref_id:
                    section_info['header_references'].append({
                        'type': ref_type,
                        'id': ref_id
                    })

            footer_refs = sectPr_elem.findall('.//w:footerReference', OOXML_NAMESPACES)
            for ref in footer_refs:
                ref_type = ref.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                ref_id = ref.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                if ref_type and ref_id:
                    section_info['footer_references'].append({
                        'type': ref_type,
                        'id': ref_id
                    })

            pgNumType_elem = sectPr_elem.find('.//w:pgNumType', OOXML_NAMESPACES)
            if pgNumType_elem is not None:
                page_numbering: dict[str, Any] = {}
                fmt = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fmt')
                if fmt:
                    page_numbering['format'] = fmt
                start = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}start')
                if start:
                    page_numbering['start'] = int(start)
                chapSep = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}chapSep')
                if chapSep:
                    page_numbering['chapter_separator'] = chapSep
                chapStyle = pgNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}chapStyle')
                if chapStyle:
                    page_numbering['chapter_style'] = chapStyle
                if page_numbering:
                    section_info['page_numbering'] = page_numbering

            lnNumType_elem = sectPr_elem.find('.//w:lnNumType', OOXML_NAMESPACES)
            if lnNumType_elem is not None:
                line_numbers: dict[str, Any] = {}
                start = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}start')
                if start:
                    line_numbers['start'] = int(start)
                countBy = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}countBy')
                if countBy:
                    line_numbers['count_by'] = int(countBy)
                distance = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}distance')
                if distance:
                    line_numbers['distance'] = DocxUtils.convert_twips_to_points(distance)
                restart = lnNumType_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}restart')
                if restart:
                    line_numbers['restart'] = restart
                if line_numbers:
                    section_info['line_numbers'] = line_numbers

            textDirection_elem = sectPr_elem.find('.//w:textDirection', OOXML_NAMESPACES)
            if textDirection_elem is not None:
                direction = textDirection_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if direction:
                    section_info['text_direction'] = direction

            paperSrc_elem = sectPr_elem.find('.//w:paperSrc', OOXML_NAMESPACES)
            if paperSrc_elem is not None:
                paper_info = {}
                first = paperSrc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}first')
                if first:
                    paper_info['first'] = first
                other = paperSrc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}other')
                if other:
                    paper_info['other'] = other
                if paper_info:
                    section_info['paper_source'] = paper_info

            pgBorders_elem = sectPr_elem.find('.//w:pgBorders', OOXML_NAMESPACES)
            if pgBorders_elem is not None:
                page_borders: dict[str, Any] = {}
                offsetFrom = pgBorders_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}offsetFrom')
                if offsetFrom:
                    page_borders['offset_from'] = offsetFrom
                borders: dict[str, Any] = {}
                for border_type in ['top', 'left', 'bottom', 'right']:
                    border_elem = pgBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info: dict[str, Any] = {}
                        color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(color)
                        space = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}space')
                        if space:
                            border_info['space'] = int(space)
                        sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if sz:
                            border_info['size'] = int(sz)
                        val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if val:
                            border_info['type'] = val
                        borders[border_type] = border_info
                if borders:
                    page_borders['borders'] = borders
                if page_borders:
                    section_info['page_borders'] = page_borders

            formProt_elem = sectPr_elem.find('.//w:formProt', OOXML_NAMESPACES)
            if formProt_elem is not None:
                form_prot = formProt_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if form_prot:
                    section_info['form_protection'] = form_prot == 'true' or form_prot == '1'

            vAlign_elem = sectPr_elem.find('.//w:vAlign', OOXML_NAMESPACES)
            if vAlign_elem is not None:
                v_align = vAlign_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if v_align:
                    section_info['vertical_alignment'] = v_align

            noEndnote_elem = sectPr_elem.find('.//w:noEndnote', OOXML_NAMESPACES)
            if noEndnote_elem is not None:
                section_info['no_endnote'] = True

            titlePg_elem = sectPr_elem.find('.//w:titlePg', OOXML_NAMESPACES)
            if titlePg_elem is not None:
                section_info['title_page'] = True

            textboxTightWrap_elem = sectPr_elem.find('.//w:textboxTightWrap', OOXML_NAMESPACES)
            if textboxTightWrap_elem is not None:
                tight_wrap = textboxTightWrap_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if tight_wrap:
                    section_info['textbox_tight_wrap'] = tight_wrap

            docGrid_elem = sectPr_elem.find('.//w:docGrid', OOXML_NAMESPACES)
            if docGrid_elem is not None:
                doc_grid: dict[str, Any] = {}
                grid_type = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                if grid_type:
                    doc_grid['type'] = grid_type
                line_pitch = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}linePitch')
                if line_pitch:
                    doc_grid['line_pitch'] = int(line_pitch)
                char_space = docGrid_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}charSpace')
                if char_space:
                    doc_grid['char_space'] = int(char_space)
                if doc_grid:
                    section_info['doc_grid'] = doc_grid

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting section properties: {str(e)}")

        return section_info

    @staticmethod
    def extract_page_break_info(br_elem: ET.Element) -> dict[str, Any]:
        page_break_info = {
            'type': 'textWrapping',
            'clear': None,
            'location': 'after'
        }

        try:
            br_type = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
            if br_type:
                if br_type == 'page':
                    page_break_info['type'] = 'page'
                elif br_type == 'column':
                    page_break_info['type'] = 'column'
                elif br_type == 'textWrapping':
                    page_break_info['type'] = 'textWrapping'

            if page_break_info['type'] == 'textWrapping':
                clear = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}clear')
                if clear:
                    page_break_info['clear'] = clear

            parent = br_elem.getparent()
            if parent is not None:
                if parent.tag.endswith('p'):
                    index = list(parent).index(br_elem)
                    if index == 0:
                        page_break_info['location'] = 'before'
                    else:
                        page_break_info['location'] = 'after'

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error extracting page break information: {str(e)}")

        return page_break_info

    @staticmethod
    def extract_column_break_info(br_elem: ET.Element) -> dict[str, Any]:
        column_break_info = {
            'type': 'column',
            'location': 'after'
        }

        try:
            parent = br_elem.getparent()
            if parent is not None:
                if parent.tag.endswith('p'):
                    index = list(parent).index(br_elem)
                    if index == 0:
                        column_break_info['location'] = 'before'
                    else:
                        column_break_info['location'] = 'after'

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error extracting column break information: {str(e)}")

        return column_break_info

    @staticmethod
    def extract_line_break_info(br_elem: ET.Element) -> dict[str, Any]:
        line_break_info = {
            'type': 'textWrapping',
            'clear': 'none',
            'location': 'after'
        }

        try:
            clear = br_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}clear')
            if clear:
                line_break_info['clear'] = clear

            parent = br_elem.getparent()
            if parent is not None:
                if parent.tag.endswith('p'):
                    index = list(parent).index(br_elem)
                    if index == 0:
                        line_break_info['location'] = 'before'
                    else:
                        line_break_info['location'] = 'after'

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error extracting line break information: {str(e)}")

        return line_break_info

    @staticmethod
    def extract_tab_info(tab_elem: ET.Element) -> dict[str, Any]:
        from .docx_utils import DocxUtils

        tab_info: dict[str, Any] = {
            'type': 'left',
            'leader': None,
            'position': 0.0
        }

        try:
            parent = tab_elem.getparent()
            if parent is not None and parent.tag.endswith('tabs'):
                for tab_stop in parent.findall('.//w:tab', OOXML_NAMESPACES):
                    pos = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pos')
                    if pos:
                        tab_info['position'] = DocxUtils.convert_twips_to_points(pos)

                    tab_type = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if tab_type:
                        tab_info['type'] = tab_type

                    leader = tab_stop.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}leader')
                    if leader:
                        tab_info['leader'] = leader
                    break

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error extracting tab information: {str(e)}")

        return tab_info

    @staticmethod
    def extract_soft_hyphen_info(hyphen_elem: ET.Element) -> dict[str, Any]:
        hyphen_info = {
            'type': 'softHyphen',
            'char': '\u00ad'
        }

        try:
            if hyphen_elem.tag.endswith('noBreakHyphen'):
                hyphen_info['type'] = 'noBreakHyphen'
                hyphen_info['char'] = '\u2011'

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"Error extracting soft hyphen information: {str(e)}")

        return hyphen_info
