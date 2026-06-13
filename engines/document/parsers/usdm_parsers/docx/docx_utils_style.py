"""Mixin for DOCX style-related utility methods"""

# mypy: disable-error-code="attr-defined"
import re
import xml.etree.ElementTree as ET
from typing import Any

from .docx_utils_base import DocxStyleInfo, OOXML_NAMESPACES


class DocxStyle:
    """Mixin providing DOCX style extraction methods"""

    @staticmethod
    def extract_text_style(rPr_elem: ET.Element | None) -> dict[str, Any]:
        style_info: dict[str, Any] = {
            'bold': False,
            'italic': False,
            'underline': False,
            'strikethrough': False,
            'font_family': None,
            'font_size': None,
            'color': None,
            'background_color': None,
            'is_code': False,
            'superscript': False,
            'subscript': False,
            'highlight_color': None,
            'language': None,
            'style_id': None,
            'style_name': None
        }

        if rPr_elem is None:
            return style_info

        try:
            b_elem = rPr_elem.find('.//w:b', OOXML_NAMESPACES)
            if b_elem is not None:
                val_attr = b_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['bold'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']

            i_elem = rPr_elem.find('.//w:i', OOXML_NAMESPACES)
            if i_elem is not None:
                val_attr = i_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['italic'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']

            u_elem = rPr_elem.find('.//w:u', OOXML_NAMESPACES)
            if u_elem is not None:
                val_attr = u_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr and val_attr.lower() != 'none':
                    style_info['underline'] = True
                    style_info['underline_type'] = val_attr
                elif val_attr is None:
                    style_info['underline'] = True

            strike_elem = rPr_elem.find('.//w:strike', OOXML_NAMESPACES)
            if strike_elem is not None:
                val_attr = strike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['strikethrough'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']

            dstrike_elem = rPr_elem.find('.//w:dstrike', OOXML_NAMESPACES)
            if dstrike_elem is not None:
                val_attr = dstrike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr is None or val_attr.lower() not in ['false', '0', 'off']:
                    style_info['strikethrough'] = True
                    style_info['double_strikethrough'] = True

            vert_align_elem = rPr_elem.find('.//w:vertAlign', OOXML_NAMESPACES)
            if vert_align_elem is not None:
                val_attr = vert_align_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr == 'superscript':
                    style_info['superscript'] = True
                elif val_attr == 'subscript':
                    style_info['subscript'] = True

            rFonts_elem = rPr_elem.find('.//w:rFonts', OOXML_NAMESPACES)
            if rFonts_elem is not None:
                ascii_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii')
                h_ansi_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi')
                cs_attr = rFonts_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs')

                font_family = ascii_attr or h_ansi_attr or cs_attr
                if font_family:
                    style_info['font_family'] = font_family

                    monospace_fonts = ['consolas', 'courier', 'monospace', 'monaco', 'source code pro',
                                      'fira code', 'cascadia code', 'jetbrains mono']
                    if any(mf in font_family.lower() for mf in monospace_fonts):
                        style_info['is_code'] = True

            sz_elem = rPr_elem.find('.//w:sz', OOXML_NAMESPACES)
            if sz_elem is not None:
                sz_val = sz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if sz_val:
                    try:
                        size_pts = int(sz_val) / 2
                        style_info['font_size'] = f"{size_pts}pt"
                    except ValueError:
                        style_info['font_size'] = sz_val

            szCs_elem = rPr_elem.find('.//w:szCs', OOXML_NAMESPACES)
            if szCs_elem is not None and not style_info['font_size']:
                sz_val = szCs_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if sz_val:
                    try:
                        size_pts = int(sz_val) / 2
                        style_info['font_size'] = f"{size_pts}pt"
                    except ValueError:
                        style_info['font_size'] = sz_val

            color_elem = rPr_elem.find('.//w:color', OOXML_NAMESPACES)
            if color_elem is not None:
                color_val = color_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if color_val and color_val.lower() != 'auto':
                    style_info['color'] = f"#{color_val}"

            highlight_elem = rPr_elem.find('.//w:highlight', OOXML_NAMESPACES)
            if highlight_elem is not None:
                highlight_val = highlight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if highlight_val:
                    style_info['highlight_color'] = highlight_val

            shd_elem = rPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr and fill_attr.lower() != 'auto':
                    style_info['background_color'] = f"#{fill_attr}"

            lang_elem = rPr_elem.find('.//w:lang', OOXML_NAMESPACES)
            if lang_elem is not None:
                lang_val = lang_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if lang_val:
                    style_info['language'] = lang_val

            rStyle_elem = rPr_elem.find('.//w:rStyle', OOXML_NAMESPACES)
            if rStyle_elem is not None:
                style_id = rStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    style_info['style_id'] = style_id

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting text style: {str(e)}")

        return style_info

    @staticmethod
    def extract_paragraph_style(pPr_elem: ET.Element | None, styles_dict: dict[str, DocxStyleInfo]) -> dict[str, Any]:
        style_info: dict[str, Any] = {
            'is_heading': False,
            'heading_level': 1,
            'is_list': False,
            'is_quote': False,
            'is_code_block': False,
            'alignment': 'left',
            'indentation': {},
            'spacing': {},
            'style_id': None,
            'style_name': None,
            'list_info': None,
            'keep_lines': False,
            'keep_next': False,
            'page_break_before': False,
            'widow_control': True,
            'orphan_control': True,
            'outline_level': None
        }

        if pPr_elem is None:
            return style_info

        try:
            pStyle_elem = pPr_elem.find('.//w:pStyle', OOXML_NAMESPACES)
            if pStyle_elem is not None:
                style_id = pStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    style_info['style_id'] = style_id

                    if style_id in styles_dict:
                        style_obj = styles_dict[style_id]
                        style_info['style_name'] = style_obj.style_name

                        if style_obj.style_name:
                            style_name_lower = style_obj.style_name.lower()

                            if 'heading' in style_name_lower:
                                style_info['is_heading'] = True
                                for i in range(1, 10):
                                    if f'heading {i}' in style_name_lower or f'heading{i}' in style_name_lower:
                                        style_info['heading_level'] = i
                                        break
                                if style_info['heading_level'] == 1 and 'outline_level' in style_obj.properties:
                                    outline_level = style_obj.properties.get('outline_level')
                                    if outline_level and 1 <= outline_level <= 9:
                                        style_info['heading_level'] = outline_level

                            elif any(list_term in style_name_lower for list_term in ['list', 'bullet', 'numbering']):
                                style_info['is_list'] = True

                            elif any(quote_term in style_name_lower for quote_term in ['quote', 'blockquote', 'quotation']):
                                style_info['is_quote'] = True

                            elif any(code_term in style_name_lower for code_term in ['code', 'preformatted', 'monospace']):
                                style_info['is_code_block'] = True

            outline_lvl_elem = pPr_elem.find('.//w:outlineLvl', OOXML_NAMESPACES)
            if outline_lvl_elem is not None:
                outline_val = outline_lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if outline_val:
                    try:
                        outline_lvl_int = int(outline_val)
                        style_info['outline_level'] = outline_lvl_int
                        if not style_info['is_heading']:
                            style_info['is_heading'] = True
                            style_info['heading_level'] = min(outline_lvl_int + 1, 9)
                    except ValueError:
                        pass

            jc_elem = pPr_elem.find('.//w:jc', OOXML_NAMESPACES)
            if jc_elem is not None:
                alignment = jc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if alignment:
                    alignment_map = {
                        'left': 'left',
                        'right': 'right',
                        'center': 'center',
                        'both': 'justify',
                        'distribute': 'justify',
                        'start': 'left',
                        'end': 'right'
                    }
                    style_info['alignment'] = alignment_map.get(alignment.lower(), 'left')

            ind_elem = pPr_elem.find('.//w:ind', OOXML_NAMESPACES)
            if ind_elem is not None:
                indentation = {}
                left_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}left')
                if left_attr:
                    try:
                        left_twips = int(left_attr)
                        left_pts = left_twips / 20
                        indentation['left'] = f"{left_pts}pt"
                    except ValueError:
                        indentation['left'] = left_attr

                right_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}right')
                if right_attr:
                    try:
                        right_twips = int(right_attr)
                        right_pts = right_twips / 20
                        indentation['right'] = f"{right_pts}pt"
                    except ValueError:
                        indentation['right'] = right_attr

                first_line_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}firstLine')
                if first_line_attr:
                    try:
                        first_line_twips = int(first_line_attr)
                        first_line_pts = first_line_twips / 20
                        indentation['first_line'] = f"{first_line_pts}pt"
                    except ValueError:
                        indentation['first_line'] = first_line_attr

                hanging_attr = ind_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hanging')
                if hanging_attr:
                    try:
                        hanging_twips = int(hanging_attr)
                        hanging_pts = hanging_twips / 20
                        indentation['hanging'] = f"{hanging_pts}pt"
                    except ValueError:
                        indentation['hanging'] = hanging_attr

                if indentation:
                    style_info['indentation'] = indentation

            spacing_elem = pPr_elem.find('.//w:spacing', OOXML_NAMESPACES)
            if spacing_elem is not None:
                spacing = {}
                before_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before')
                if before_attr:
                    try:
                        before_twips = int(before_attr)
                        before_pts = before_twips / 20
                        spacing['before'] = f"{before_pts}pt"
                    except ValueError:
                        spacing['before'] = before_attr

                after_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}after')
                if after_attr:
                    try:
                        after_twips = int(after_attr)
                        after_pts = after_twips / 20
                        spacing['after'] = f"{after_pts}pt"
                    except ValueError:
                        spacing['after'] = after_attr

                line_attr = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line')
                if line_attr:
                    try:
                        line_val = int(line_attr)
                        if line_attr.endswith('auto'):
                            spacing['line'] = 'auto'
                        else:
                            line_rule = spacing_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule', 'atLeast')
                            if line_rule == 'exact':
                                spacing['line'] = f"{line_val / 240}pt"
                            else:
                                spacing['line'] = f"{line_val / 240}pt"
                    except ValueError:
                        spacing['line'] = line_attr

                if spacing:
                    style_info['spacing'] = spacing

            numPr_elem = pPr_elem.find('.//w:numPr', OOXML_NAMESPACES)
            if numPr_elem is not None:
                style_info['is_list'] = True
                list_info: dict[str, Any] = {}
                numId_elem = numPr_elem.find('.//w:numId', OOXML_NAMESPACES)
                if numId_elem is not None:
                    num_id = numId_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if num_id:
                        list_info['num_id'] = num_id

                ilvl_elem = numPr_elem.find('.//w:ilvl', OOXML_NAMESPACES)
                if ilvl_elem is not None:
                    ilvl_val = ilvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if ilvl_val:
                        try:
                            list_info['level'] = int(ilvl_val)
                        except ValueError:
                            list_info['level'] = 0

                style_info['list_info'] = list_info

            keepLines_elem = pPr_elem.find('.//w:keepLines', OOXML_NAMESPACES)
            if keepLines_elem is not None:
                style_info['keep_lines'] = True

            keepNext_elem = pPr_elem.find('.//w:keepNext', OOXML_NAMESPACES)
            if keepNext_elem is not None:
                style_info['keep_next'] = True

            pageBreakBefore_elem = pPr_elem.find('.//w:pageBreakBefore', OOXML_NAMESPACES)
            if pageBreakBefore_elem is not None:
                style_info['page_break_before'] = True

            widowControl_elem = pPr_elem.find('.//w:widowControl', OOXML_NAMESPACES)
            if widowControl_elem is not None:
                val_attr = widowControl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['widow_control'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']

            orphanControl_elem = pPr_elem.find('.//w:orphanControl', OOXML_NAMESPACES)
            if orphanControl_elem is not None:
                val_attr = orphanControl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                style_info['orphan_control'] = val_attr is None or val_attr.lower() not in ['false', '0', 'off']

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting paragraph style: {str(e)}")

        return style_info

    @staticmethod
    def extract_style_properties(style_elem: ET.Element) -> dict[str, Any]:
        properties: dict[str, Any] = {}

        try:
            pPr_elem = style_elem.find('.//w:pPr', OOXML_NAMESPACES)
            if pPr_elem is not None:
                outline_lvl_elem = pPr_elem.find('.//w:outlineLvl', OOXML_NAMESPACES)
                if outline_lvl_elem is not None:
                    outline_val = outline_lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if outline_val:
                        try:
                            properties['outline_level'] = int(outline_val)
                        except ValueError:
                            properties['outline_level'] = outline_val

                jc_elem = pPr_elem.find('.//w:jc', OOXML_NAMESPACES)
                if jc_elem is not None:
                    jc_val = jc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if jc_val:
                        properties['justification'] = jc_val

                ind_elem = pPr_elem.find('.//w:ind', OOXML_NAMESPACES)
                if ind_elem is not None:
                    ind_props = {}
                    for attr_name in ['left', 'right', 'firstLine', 'hanging']:
                        attr_val = ind_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            ind_props[attr_name] = attr_val
                    if ind_props:
                        properties['indentation'] = ind_props

                spacing_elem = pPr_elem.find('.//w:spacing', OOXML_NAMESPACES)
                if spacing_elem is not None:
                    spacing_props = {}
                    for attr_name in ['before', 'after', 'line', 'lineRule']:
                        attr_val = spacing_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            spacing_props[attr_name] = attr_val
                    if spacing_props:
                        properties['spacing'] = spacing_props

            rPr_elem = style_elem.find('.//w:rPr', OOXML_NAMESPACES)
            if rPr_elem is not None:
                rFonts_elem = rPr_elem.find('.//w:rFonts', OOXML_NAMESPACES)
                if rFonts_elem is not None:
                    font_props = {}
                    for attr_name in ['ascii', 'hAnsi', 'cs', 'eastAsia']:
                        attr_val = rFonts_elem.get(f'{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{attr_name}')
                        if attr_val:
                            font_props[attr_name] = attr_val
                    if font_props:
                        properties['font'] = font_props

                sz_elem = rPr_elem.find('.//w:sz', OOXML_NAMESPACES)
                if sz_elem is not None:
                    sz_val = sz_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if sz_val:
                        properties['font_size'] = sz_val

                szCs_elem = rPr_elem.find('.//w:szCs', OOXML_NAMESPACES)
                if szCs_elem is not None and 'font_size' not in properties:
                    sz_val = szCs_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if sz_val:
                        properties['font_size'] = sz_val

                color_elem = rPr_elem.find('.//w:color', OOXML_NAMESPACES)
                if color_elem is not None:
                    color_val = color_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if color_val:
                        properties['color'] = color_val

                b_elem = rPr_elem.find('.//w:b', OOXML_NAMESPACES)
                if b_elem is not None:
                    b_val = b_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['bold'] = b_val is None or b_val.lower() not in ['false', '0', 'off']

                i_elem = rPr_elem.find('.//w:i', OOXML_NAMESPACES)
                if i_elem is not None:
                    i_val = i_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['italic'] = i_val is None or i_val.lower() not in ['false', '0', 'off']

                u_elem = rPr_elem.find('.//w:u', OOXML_NAMESPACES)
                if u_elem is not None:
                    u_val = u_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    if u_val:
                        properties['underline'] = u_val

                strike_elem = rPr_elem.find('.//w:strike', OOXML_NAMESPACES)
                if strike_elem is not None:
                    strike_val = strike_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    properties['strikethrough'] = strike_val is None or strike_val.lower() not in ['false', '0', 'off']

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting style properties: {str(e)}")

        return properties

    @staticmethod
    def convert_color_from_ooxml(color_value: str) -> str:
        if not color_value:
            return "#000000"

        color_value = color_value.lower().strip()

        if re.match(r'^[0-9a-f]{6}$', color_value):
            return f"#{color_value}"

        if color_value in ['auto', 'none']:
            return "#000000"

        color_map = {
            'black': '#000000',
            'white': '#FFFFFF',
            'red': '#FF0000',
            'green': '#00FF00',
            'blue': '#0000FF',
            'yellow': '#FFFF00',
            'cyan': '#00FFFF',
            'magenta': '#FF00FF',
            'gray': '#808080',
            'grey': '#808080',
            'darkred': '#8B0000',
            'darkgreen': '#006400',
            'darkblue': '#00008B',
            'darkyellow': '#CCCC00',
            'darkcyan': '#008B8B',
            'darkmagenta': '#8B008B',
            'lightgray': '#D3D3D3',
            'lightgrey': '#D3D3D3',
        }

        if color_value in color_map:
            return color_map[color_value]

        if re.match(r'^[0-9a-f]{6}$', color_value):
            return f"#{color_value}"

        if re.match(r'^[0-9a-f]{8}$', color_value):
            return f"#{color_value[2:]}"

        return "#000000"
