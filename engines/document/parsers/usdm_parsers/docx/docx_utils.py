"""
Helper tools for DOCX parser
Includes helper functions for processing styles, text, math, and managing DOCX files
"""
# mypy: ignore-errors
import xml.etree.ElementTree as ET
from typing import Any

from .docx_utils_math import DocxMath
from .docx_utils_section import DocxSection
from .docx_utils_style import DocxStyle
from .docx_utils_base import DocxNumberingInfo, DocxStyleInfo, NS, OOXML_NAMESPACES, parse_dxa_to_points, parse_emu_to_pixels


class DocxUtils(DocxStyle, DocxSection, DocxMath):
    """DOCX utility class"""







    @staticmethod
    def extract_numbering_definition(abstract_num_elem: ET.Element) -> dict[str, Any]:
        """
        Extract numbering definition from abstractNum element
        
        Args:
            abstract_num_elem: abstractNum element
            
        Returns:
            Dict[str, Any]: numbering information
        """
        numbering_info = {
            'levels': {},
            'multi_level': False,
            'restart_numbering': True
        }

        try:
            # Extract restart numbering
            restart_elem = abstract_num_elem.find('.//w:lvlRestart', OOXML_NAMESPACES)
            if restart_elem is not None:
                restart_val = restart_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if restart_val:
                    numbering_info['restart_numbering'] = restart_val.lower() not in ['false', '0', 'off']

            # Extract levels
            for lvl_elem in abstract_num_elem.findall('.//w:lvl', OOXML_NAMESPACES):
                ilvl_attr = lvl_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ilvl')
                if ilvl_attr is None:
                    continue

                try:
                    level = int(ilvl_attr)
                    level_info = {}

                    # Extract start
                    start_elem = lvl_elem.find('.//w:start', OOXML_NAMESPACES)
                    if start_elem is not None:
                        start_val = start_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if start_val:
                            try:
                                level_info['start'] = int(start_val)
                            except ValueError:
                                level_info['start'] = 1

                    # Extract format
                    numFmt_elem = lvl_elem.find('.//w:numFmt', OOXML_NAMESPACES)
                    if numFmt_elem is not None:
                        num_fmt = numFmt_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if num_fmt:
                            format_map = {
                                'decimal': 'decimal',
                                'lowerLetter': 'lowerLetter',
                                'upperLetter': 'upperLetter',
                                'lowerRoman': 'lowerRoman',
                                'upperRoman': 'upperRoman',
                                'bullet': 'bullet',
                                'none': 'none'
                            }
                            level_info['format'] = format_map.get(num_fmt, num_fmt)

                    # Extract text
                    lvlText_elem = lvl_elem.find('.//w:lvlText', OOXML_NAMESPACES)
                    if lvlText_elem is not None:
                        lvl_text = lvlText_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if lvl_text:
                            level_info['text'] = lvl_text

                    # Extract justification
                    lvlJc_elem = lvl_elem.find('.//w:lvlJc', OOXML_NAMESPACES)
                    if lvlJc_elem is not None:
                        lvl_jc = lvlJc_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if lvl_jc:
                            level_info['justification'] = lvl_jc

                    numbering_info['levels'][level] = level_info

                except ValueError:
                    continue

            # Check multi-level
            if len(numbering_info['levels']) > 1:
                numbering_info['multi_level'] = True

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting numbering definition: {str(e)}")

        return numbering_info

    @staticmethod
    def extract_text_from_element(elem: ET.Element | None, include_children: bool = True) -> str:
        """
        Extract text from an XML element and its children
        
        Args:
            elem: XML element
            include_children: whether to extract children's text too
            
        Returns:
            str: extracted text
        """
        if elem is None:
            return ""

        text_parts = []

        try:
            # If element has its own text
            if elem.text and elem.text.strip():
                text_parts.append(elem.text.strip())

            # Process children
            if include_children:
                for child in elem:
                    # Extract text from w:t elements
                    if child.tag.endswith('t'):
                        if child.text and child.text.strip():
                            text_parts.append(child.text.strip())
                    # Recursive processing for other elements
                    else:
                        child_text = DocxUtils.extract_text_from_element(child, include_children)
                        if child_text:
                            text_parts.append(child_text)

                    # Add tail
                    if child.tail and child.tail.strip():
                        text_parts.append(child.tail.strip())

            # Add main element tail
            if elem.tail and elem.tail.strip():
                text_parts.append(elem.tail.strip())

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting text from element: {str(e)}")

        return ' '.join(text_parts).strip()





    @staticmethod
    def get_namespace_tag(tag_name: str, namespace: str = 'w') -> str:
        """
        Build tag with namespace
        
        Args:
            tag_name: tag name
            namespace: namespace (default: 'w')
            
        Returns:
            str: full tag with namespace
        """
        return f"{{{OOXML_NAMESPACES.get(namespace, namespace)}}}{tag_name}"

    @staticmethod
    def find_element_with_ns(elem: ET.Element, tag_name: str, namespace: str = 'w') -> ET.Element | None:
        """
        Find element with namespace
        
        Args:
            elem: parent element
            tag_name: tag name
            namespace: namespace (default: 'w')
            
        Returns:
            Optional[ET.Element]: found element or None
        """
        if elem is None:
            return None

        ns_tag = DocxUtils.get_namespace_tag(tag_name, namespace)
        return elem.find(f'.//{ns_tag}', OOXML_NAMESPACES)

    @staticmethod
    def find_all_elements_with_ns(elem: ET.Element, tag_name: str, namespace: str = 'w') -> list[ET.Element]:
        """
        Find all elements with namespace
        
        Args:
            elem: parent element
            tag_name: tag name
            namespace: namespace (default: 'w')
            
        Returns:
            List[ET.Element]: list of found elements
        """
        if elem is None:
            return []

        ns_tag = DocxUtils.get_namespace_tag(tag_name, namespace)
        return elem.findall(f'.//{ns_tag}', OOXML_NAMESPACES)

    @staticmethod
    def extract_hyperlink_info(hyperlink_elem: ET.Element) -> dict[str, Any]:
        """
        Extract hyperlink information from hyperlink element
        
        Args:
            hyperlink_elem: hyperlink element
            
        Returns:
            Dict[str, Any]: hyperlink information
        """
        hyperlink_info = {
            'url': None,
            'anchor': None,
            'tooltip': None,
            'display_text': ''
        }

        try:
            # Extract relationship
            r_id = hyperlink_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
            if r_id:
                hyperlink_info['relationship_id'] = r_id

            # Extract anchor
            anchor = hyperlink_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}anchor')
            if anchor:
                hyperlink_info['anchor'] = anchor

            # Extract tooltip
            tooltip = hyperlink_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tooltip')
            if tooltip:
                hyperlink_info['tooltip'] = tooltip

            # Extract display text
            runs = hyperlink_elem.findall('.//w:r', OOXML_NAMESPACES)
            text_parts = []
            for run in runs:
                text_elem = run.find('.//w:t', OOXML_NAMESPACES)
                if text_elem is not None and text_elem.text:
                    text_parts.append(text_elem.text.strip())

            if text_parts:
                hyperlink_info['display_text'] = ' '.join(text_parts)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting hyperlink information: {str(e)}")

        return hyperlink_info

    @staticmethod
    def extract_image_info(drawing_elem: ET.Element) -> dict[str, Any]:
        """
        Extract image information from drawing element
        
        Args:
            drawing_elem: drawing element
            
        Returns:
            Dict[str, Any]: image information
        """
        image_info = {
            'relationship_id': None,
            'filename': None,
            'width': None,
            'height': None,
            'title': None,
            'description': None,
            'content_type': None
        }

        try:
            # Find blip element (image)
            blip_elem = drawing_elem.find('.//a:blip', OOXML_NAMESPACES)
            if blip_elem is not None:
                r_embed = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                r_link = blip_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link')

                if r_embed:
                    image_info['relationship_id'] = r_embed
                    image_info['embed_type'] = 'embedded'
                elif r_link:
                    image_info['relationship_id'] = r_link
                    image_info['embed_type'] = 'linked'

            # Find pic element (image)
            pic_elem = drawing_elem.find('.//pic:pic', OOXML_NAMESPACES)
            if pic_elem is not None:
                # Extract dimensions
                ext_elem = pic_elem.find('.//a:ext', OOXML_NAMESPACES)
                if ext_elem is not None:
                    cx_attr = ext_elem.get('cx')
                    cy_attr = ext_elem.get('cy')

                    if cx_attr and cy_attr:
                        try:
                            # Convert from EMU to pixels (1 EMU = 1/914400 inch)
                            # Assume: 96 DPI
                            width_emu = int(cx_attr)
                            height_emu = int(cy_attr)

                            # Convert to pixels
                            width_px = width_emu / 914400 * 96
                            height_px = height_emu / 914400 * 96

                            image_info['width'] = round(width_px)
                            image_info['height'] = round(height_px)
                            image_info['width_emu'] = width_emu
                            image_info['height_emu'] = height_emu
                        except ValueError:
                            pass

                # Extract title and description
                nvPicPr_elem = pic_elem.find('.//pic:nvPicPr', OOXML_NAMESPACES)
                if nvPicPr_elem is not None:
                    cNvPr_elem = nvPicPr_elem.find('.//a:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        title = cNvPr_elem.get('title')
                        desc = cNvPr_elem.get('descr')

                        if title:
                            image_info['title'] = title
                        if desc:
                            image_info['description'] = desc

            # Find content type information
            blipFill_elem = drawing_elem.find('.//a:blipFill', OOXML_NAMESPACES)
            if blipFill_elem is not None:
                srcRect_elem = blipFill_elem.find('.//a:srcRect', OOXML_NAMESPACES)
                if srcRect_elem is not None:
                    # Extract crop information
                    for attr in ['l', 't', 'r', 'b']:
                        val = srcRect_elem.get(attr)
                        if val:
                            image_info[f'crop_{attr}'] = val

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting image information: {str(e)}")

        return image_info

    @staticmethod
    def extract_table_properties(tblPr_elem: ET.Element | None) -> dict[str, Any]:
        """
        Extract table properties from tblPr element
        
        Args:
            tblPr_elem: tblPr element (table properties)
            
        Returns:
            Dict[str, Any]: table properties
        """
        table_props = {
            'style_id': None,
            'style_name': None,
            'alignment': 'left',
            'width': None,
            'borders': {},
            'shading': None,
            'layout': 'autofit',
            'indentation': None
        }

        if tblPr_elem is None:
            return table_props

        try:
            # Extract table style
            tblStyle_elem = tblPr_elem.find('.//w:tblStyle', OOXML_NAMESPACES)
            if tblStyle_elem is not None:
                style_id = tblStyle_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if style_id:
                    table_props['style_id'] = style_id

            # Extract table alignment
            jc_elem = tblPr_elem.find('.//w:jc', OOXML_NAMESPACES)
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
                    table_props['alignment'] = alignment_map.get(alignment.lower(), 'left')

            # Extract table width
            tblW_elem = tblPr_elem.find('.//w:tblW', OOXML_NAMESPACES)
            if tblW_elem is not None:
                width_type = tblW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'auto')
                width_val = tblW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')

                if width_val and width_type != 'auto':
                    try:
                        # Convert از twips به points
                        width_twips = int(width_val)
                        width_pts = width_twips / 20
                        table_props['width'] = f"{width_pts}pt"
                        table_props['width_type'] = width_type
                    except ValueError:
                        table_props['width'] = width_val

            # Extract table borders
            tblBorders_elem = tblPr_elem.find('.//w:tblBorders', OOXML_NAMESPACES)
            if tblBorders_elem is not None:
                borders = {}
                for border_type in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                    border_elem = tblBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info = {}

                        # Extract border type
                        border_val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if border_val:
                            border_info['type'] = border_val

                        # Extract size
                        border_sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if border_sz:
                            try:
                                # Convert از 1/8 point به point
                                sz_val = int(border_sz)
                                border_info['size'] = f"{sz_val / 8}pt"
                            except ValueError:
                                border_info['size'] = border_sz

                        # Extract color
                        border_color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if border_color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(border_color)

                        if border_info:
                            borders[border_type] = border_info

                if borders:
                    table_props['borders'] = borders

            # Extract shading
            shd_elem = tblPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                shading = {}

                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr:
                    shading['fill'] = DocxUtils.convert_color_from_ooxml(fill_attr)

                val_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr:
                    shading['type'] = val_attr

                color_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                if color_attr:
                    shading['color'] = DocxUtils.convert_color_from_ooxml(color_attr)

                if shading:
                    table_props['shading'] = shading

            # Extract layout
            tblLayout_elem = tblPr_elem.find('.//w:tblLayout', OOXML_NAMESPACES)
            if tblLayout_elem is not None:
                layout_type = tblLayout_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')
                if layout_type:
                    table_props['layout'] = 'fixed' if layout_type == 'fixed' else 'autofit'

            # Extract indentation
            tblInd_elem = tblPr_elem.find('.//w:tblInd', OOXML_NAMESPACES)
            if tblInd_elem is not None:
                ind_type = tblInd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                ind_val = tblInd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')

                if ind_val:
                    try:
                        if ind_type == 'dxa':  # twips
                            ind_twips = int(ind_val)
                            ind_pts = ind_twips / 20
                            table_props['indentation'] = f"{ind_pts}pt"
                        else:
                            table_props['indentation'] = ind_val
                    except ValueError:
                        table_props['indentation'] = ind_val

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting table properties: {str(e)}")

        return table_props

    @staticmethod
    def extract_cell_properties(tcPr_elem: ET.Element | None) -> dict[str, Any]:
        """
        Extract table cell properties from tcPr element
        
        Args:
            tcPr_elem: tcPr element (table cell properties)
            
        Returns:
            Dict[str, Any]: Cell properties
        """
        cell_props = {
            'width': None,
            'vertical_align': 'top',
            'grid_span': 1,
            'v_merge': None,
            'shading': None,
            'borders': {},
            'margins': {}
        }

        if tcPr_elem is None:
            return cell_props

        try:
            # Extract cell width
            tcW_elem = tcPr_elem.find('.//w:tcW', OOXML_NAMESPACES)
            if tcW_elem is not None:
                width_type = tcW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')
                width_val = tcW_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')

                if width_val:
                    try:
                        if width_type == 'dxa':  # twips
                            width_twips = int(width_val)
                            width_pts = width_twips / 20
                            cell_props['width'] = f"{width_pts}pt"
                        elif width_type == 'pct':  # Percent
                            cell_props['width'] = f"{width_val}%"
                        else:
                            cell_props['width'] = width_val
                        cell_props['width_type'] = width_type
                    except ValueError:
                        cell_props['width'] = width_val

            # Extract vertical alignment
            vAlign_elem = tcPr_elem.find('.//w:vAlign', OOXML_NAMESPACES)
            if vAlign_elem is not None:
                align_val = vAlign_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if align_val:
                    align_map = {
                        'top': 'top',
                        'center': 'center',
                        'bottom': 'bottom',
                        'both': 'center'
                    }
                    cell_props['vertical_align'] = align_map.get(align_val.lower(), 'top')

            # Extract grid span (column merge)
            gridSpan_elem = tcPr_elem.find('.//w:gridSpan', OOXML_NAMESPACES)
            if gridSpan_elem is not None:
                span_val = gridSpan_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if span_val:
                    try:
                        cell_props['grid_span'] = int(span_val)
                    except ValueError:
                        cell_props['grid_span'] = 1

            # Extract vMerge (row merge)
            vMerge_elem = tcPr_elem.find('.//w:vMerge', OOXML_NAMESPACES)
            if vMerge_elem is not None:
                merge_val = vMerge_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if merge_val:
                    cell_props['v_merge'] = merge_val  # 'restart' یا 'continue'

            # Extract cell shading
            shd_elem = tcPr_elem.find('.//w:shd', OOXML_NAMESPACES)
            if shd_elem is not None:
                shading = {}

                fill_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fill')
                if fill_attr:
                    shading['fill'] = DocxUtils.convert_color_from_ooxml(fill_attr)

                val_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                if val_attr:
                    shading['type'] = val_attr

                color_attr = shd_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                if color_attr:
                    shading['color'] = DocxUtils.convert_color_from_ooxml(color_attr)

                if shading:
                    cell_props['shading'] = shading

            # Extract cell borders
            tcBorders_elem = tcPr_elem.find('.//w:tcBorders', OOXML_NAMESPACES)
            if tcBorders_elem is not None:
                borders = {}
                for border_type in ['top', 'left', 'bottom', 'right', 'tl2br', 'tr2bl']:
                    border_elem = tcBorders_elem.find(f'.//w:{border_type}', OOXML_NAMESPACES)
                    if border_elem is not None:
                        border_info = {}

                        border_val = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                        if border_val:
                            border_info['type'] = border_val

                        border_sz = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sz')
                        if border_sz:
                            try:
                                sz_val = int(border_sz)
                                border_info['size'] = f"{sz_val / 8}pt"
                            except ValueError:
                                border_info['size'] = border_sz

                        border_color = border_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}color')
                        if border_color:
                            border_info['color'] = DocxUtils.convert_color_from_ooxml(border_color)

                        if border_info:
                            borders[border_type] = border_info

                if borders:
                    cell_props['borders'] = borders

            # Extract cell inner borders
            tcMar_elem = tcPr_elem.find('.//w:tcMar', OOXML_NAMESPACES)
            if tcMar_elem is not None:
                margins = {}
                for margin_type in ['top', 'left', 'bottom', 'right']:
                    margin_elem = tcMar_elem.find(f'.//w:{margin_type}', OOXML_NAMESPACES)
                    if margin_elem is not None:
                        margin_w = margin_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}w')
                        margin_type_attr = margin_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type', 'dxa')

                        if margin_w:
                            try:
                                if margin_type_attr == 'dxa':  # twips
                                    margin_twips = int(margin_w)
                                    margin_pts = margin_twips / 20
                                    margins[margin_type] = f"{margin_pts}pt"
                                else:
                                    margins[margin_type] = margin_w
                            except ValueError:
                                margins[margin_type] = margin_w

                if margins:
                    cell_props['margins'] = margins

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های سلول: {str(e)}")

        return cell_props

    @staticmethod
    def extract_row_properties(trPr_elem: ET.Element | None) -> dict[str, Any]:
        """
        Extract table row properties from trPr element
        
        Args:
            trPr_elem: trPr element (table row properties)
            
        Returns:
            Dict[str, Any]: Row properties
        """
        row_props = {
            'height': None,
            'height_rule': 'auto',
            'cant_split': False,
            'header': False,
            'hidden': False
        }

        if trPr_elem is None:
            return row_props

        try:
            # Extract row height
            trHeight_elem = trPr_elem.find('.//w:trHeight', OOXML_NAMESPACES)
            if trHeight_elem is not None:
                height_val = trHeight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                height_rule = trHeight_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hRule', 'auto')

                if height_val:
                    try:
                        # Convert از twips به points
                        height_twips = int(height_val)
                        height_pts = height_twips / 20
                        row_props['height'] = f"{height_pts}pt"
                        row_props['height_rule'] = height_rule
                    except ValueError:
                        row_props['height'] = height_val

            # Check no row break
            cantSplit_elem = trPr_elem.find('.//w:cantSplit', OOXML_NAMESPACES)
            if cantSplit_elem is not None:
                row_props['cant_split'] = True

            # Check header row
            tblHeader_elem = trPr_elem.find('.//w:tblHeader', OOXML_NAMESPACES)
            if tblHeader_elem is not None:
                row_props['header'] = True

            # Check hidden row
            hidden_elem = trPr_elem.find('.//w:hidden', OOXML_NAMESPACES)
            if hidden_elem is not None:
                row_props['hidden'] = True

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج ویژگی‌های Row: {str(e)}")

        return row_props

    @staticmethod
    def extract_footnote_info(footnote_elem: ET.Element) -> dict[str, Any]:
        """
        Extract footnote information from footnote element
        
        Args:
            footnote_elem: footnote element
            
        Returns:
            Dict[str, Any]: Footnote information
        """
        footnote_info = {
            'id': None,
            'type': 'normal',  # 'normal', 'separator', 'continuationSeparator', 'continuationNotice'
            'content': '',
            'reference_mark': None
        }

        try:
            # Extract ID and type
            footnote_id = footnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            footnote_type = footnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')

            if footnote_id:
                footnote_info['id'] = footnote_id

            if footnote_type:
                type_map = {
                    'normal': 'normal',
                    'separator': 'separator',
                    'continuationSeparator': 'continuationSeparator',
                    'continuationNotice': 'continuationNotice'
                }
                footnote_info['type'] = type_map.get(footnote_type, 'normal')

            # Extract content
            paragraphs = footnote_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []

            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)

            if content_parts:
                footnote_info['content'] = '\n'.join(content_parts)

            # Extract reference mark
            ref_elem = footnote_elem.find('.//w:r/w:footnoteRef', OOXML_NAMESPACES)
            if ref_elem is not None:
                footnote_info['reference_mark'] = True

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات پاورقی: {str(e)}")

        return footnote_info

    @staticmethod
    def extract_endnote_info(endnote_elem: ET.Element) -> dict[str, Any]:
        """
        Extract endnote information from endnote element
        
        Args:
            endnote_elem: endnote element
            
        Returns:
            Dict[str, Any]: Endnote information
        """
        endnote_info = {
            'id': None,
            'type': 'normal',
            'content': '',
            'reference_mark': None
        }

        try:
            # Extract ID and type
            endnote_id = endnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            endnote_type = endnote_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type')

            if endnote_id:
                endnote_info['id'] = endnote_id

            if endnote_type:
                type_map = {
                    'normal': 'normal',
                    'separator': 'separator',
                    'continuationSeparator': 'continuationSeparator',
                    'continuationNotice': 'continuationNotice'
                }
                endnote_info['type'] = type_map.get(endnote_type, 'normal')

            # Extract content
            paragraphs = endnote_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []

            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)

            if content_parts:
                endnote_info['content'] = '\n'.join(content_parts)

            # Extract reference mark
            ref_elem = endnote_elem.find('.//w:r/w:endnoteRef', OOXML_NAMESPACES)
            if ref_elem is not None:
                endnote_info['reference_mark'] = True

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات یادداشت پایانی: {str(e)}")

        return endnote_info

    @staticmethod
    def extract_bookmark_info(bookmark_elem: ET.Element) -> dict[str, Any]:
        """
        Extract bookmark information from bookmarkStart or bookmarkEnd element
        
        Args:
            bookmark_elem: bookmarkStart or bookmarkEnd element
            
        Returns:
            Dict[str, Any]: Bookmark information
        """
        bookmark_info = {
            'id': None,
            'name': None,
            'type': None,  # 'start' یا 'end'
            'col_first': None,
            'col_last': None
        }

        try:
            # Determine bookmark type
            if bookmark_elem.tag.endswith('bookmarkStart'):
                bookmark_info['type'] = 'start'
            elif bookmark_elem.tag.endswith('bookmarkEnd'):
                bookmark_info['type'] = 'end'

            # Extract ID
            bookmark_id = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if bookmark_id:
                bookmark_info['id'] = bookmark_id

            # Extract name (only for bookmarkStart)
            if bookmark_info['type'] == 'start':
                bookmark_name = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name')
                if bookmark_name:
                    bookmark_info['name'] = bookmark_name

            # Extract column range (for tables)
            col_first = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}colFirst')
            col_last = bookmark_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}colLast')

            if col_first:
                try:
                    bookmark_info['col_first'] = int(col_first)
                except ValueError:
                    bookmark_info['col_first'] = col_first

            if col_last:
                try:
                    bookmark_info['col_last'] = int(col_last)
                except ValueError:
                    bookmark_info['col_last'] = col_last

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات بوکمارک: {str(e)}")

        return bookmark_info

    @staticmethod
    def extract_comment_info(comment_elem: ET.Element) -> dict[str, Any]:
        """
        Extract comment information from comment element
        
        Args:
            comment_elem: comment element
            
        Returns:
            Dict[str, Any]: Comment information
        """
        comment_info = {
            'id': None,
            'author': None,
            'date': None,
            'initials': None,
            'content': '',
            'parent_id': None
        }

        try:
            # Extract ID
            comment_id = comment_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if comment_id:
                comment_info['id'] = comment_id

            # Extract author
            author_elem = comment_elem.find('.//w:author', OOXML_NAMESPACES)
            if author_elem is not None and author_elem.text:
                comment_info['author'] = author_elem.text.strip()

            # Extract date
            date_elem = comment_elem.find('.//w:date', OOXML_NAMESPACES)
            if date_elem is not None and date_elem.text:
                comment_info['date'] = date_elem.text.strip()

            # Extract initials
            initials_elem = comment_elem.find('.//w:initials', OOXML_NAMESPACES)
            if initials_elem is not None and initials_elem.text:
                comment_info['initials'] = initials_elem.text.strip()

            # Extract parent comment ID
            parent_id = comment_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}parentId')
            if parent_id:
                comment_info['parent_id'] = parent_id

            # Extract content
            paragraphs = comment_elem.findall('.//w:p', OOXML_NAMESPACES)
            content_parts = []

            for para in paragraphs:
                para_text = DocxUtils.extract_text_from_element(para)
                if para_text:
                    content_parts.append(para_text)

            if content_parts:
                comment_info['content'] = '\n'.join(content_parts)

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات کامنت: {str(e)}")

        return comment_info

    @staticmethod
    def extract_field_info(fldChar_elem: ET.Element) -> dict[str, Any]:
        """
        Extract field information from fldChar element
        
        Args:
            fldChar_elem: fldChar element
            
        Returns:
            Dict[str, Any]: Field information
        """
        field_info = {
            'type': None,  # 'begin', 'separate', 'end', 'unknown'
            'field_type': None,  # 'PAGE', 'NUMPAGES', 'DATE', 'TIME', 'TOC', 'HYPERLINK', etc.
            'instructions': '',
            'result': ''
        }

        try:
            # Extract field type
            fld_char_type = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldCharType')
            if fld_char_type:
                type_map = {
                    'begin': 'begin',
                    'separate': 'separate',
                    'end': 'end'
                }
                field_info['type'] = type_map.get(fld_char_type, 'unknown')

            # Extract field instructions (from adjacent run elements)
            parent = fldChar_elem.getparent()
            if parent is not None:
                # Search for run elements around
                runs = parent.findall('.//w:r', OOXML_NAMESPACES)
                for run in runs:
                    # Check instrText element (field instructions)
                    instr_elem = run.find('.//w:instrText', OOXML_NAMESPACES)
                    if instr_elem is not None and instr_elem.text:
                        instructions = instr_elem.text.strip()
                        field_info['instructions'] = instructions

                        # Detect field type from instructions
                        if 'PAGE' in instructions:
                            field_info['field_type'] = 'PAGE'
                        elif 'NUMPAGES' in instructions:
                            field_info['field_type'] = 'NUMPAGES'
                        elif 'DATE' in instructions:
                            field_info['field_type'] = 'DATE'
                        elif 'TIME' in instructions:
                            field_info['field_type'] = 'TIME'
                        elif 'TOC' in instructions:
                            field_info['field_type'] = 'TOC'
                        elif 'HYPERLINK' in instructions:
                            field_info['field_type'] = 'HYPERLINK'
                        elif 'REF' in instructions:
                            field_info['field_type'] = 'REF'
                        elif 'SEQ' in instructions:
                            field_info['field_type'] = 'SEQ'

                    # Check t element (field result)
                    text_elem = run.find('.//w:t', OOXML_NAMESPACES)
                    if text_elem is not None and text_elem.text:
                        result_text = text_elem.text.strip()
                        if result_text:
                            field_info['result'] = result_text

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات فیلد: {str(e)}")

        return field_info

    @staticmethod
    def extract_smart_tag_info(smartTag_elem: ET.Element) -> dict[str, Any]:
        """
        Extract Smart Tag information from smartTag element
        
        Args:
            smartTag_elem: smartTag element
            
        Returns:
            Dict[str, Any]: Smart Tag information
        """
        smart_tag_info = {
            'uri': None,
            'element': None,
            'content': ''
        }

        try:
            # Extract URI و element
            uri_attr = smartTag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}uri')
            element_attr = smartTag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}element')

            if uri_attr:
                smart_tag_info['uri'] = uri_attr
            if element_attr:
                smart_tag_info['element'] = element_attr

            # Extract content
            content = DocxUtils.extract_text_from_element(smartTag_elem)
            if content:
                smart_tag_info['content'] = content

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات Smart Tag: {str(e)}")

        return smart_tag_info

    @staticmethod
    def extract_sdt_info(sdt_elem: ET.Element) -> dict[str, Any]:
        """
        Extract Structured Document Tag information (form controls)
        
        Args:
            sdt_elem: w:sdt element
            
        Returns:
            Dict[str, Any]: SDT information including:
                - type: نوع SDT (text, richText, comboBox, dropDownList, date, etc.)
                - tag: نام تگ
                - alias: نام نمایشی
                - lock: وضعیت قفل
                - placeholder: متن placeholder
                - content: محتوای فعلی
                - list_items: آیتم‌های لیست (برای comboBox و dropDownList)
                - date_format: فرمت تاریخ (for date picker)
                - formatting: فرمت‌های اضافی
        """
        sdt_info = {
            'type': 'unknown',
            'tag': None,
            'alias': None,
            'lock': None,
            'placeholder': None,
            'content': None,
            'list_items': None,
            'date_format': None,
            'formatting': {}
        }

        try:
            # Extract SDT properties
            sdtPr_elem = sdt_elem.find('.//w:sdtPr', OOXML_NAMESPACES)
            if sdtPr_elem is not None:
                # Determine SDT type
                sdt_type = None

                # Check different SDT types
                if sdtPr_elem.find('.//w:text', OOXML_NAMESPACES) is not None:
                    sdt_type = 'text'
                elif sdtPr_elem.find('.//w:richText', OOXML_NAMESPACES) is not None:
                    sdt_type = 'richText'
                elif sdtPr_elem.find('.//w:comboBox', OOXML_NAMESPACES) is not None:
                    sdt_type = 'comboBox'
                elif sdtPr_elem.find('.//w:dropDownList', OOXML_NAMESPACES) is not None:
                    sdt_type = 'dropDownList'
                elif sdtPr_elem.find('.//w:date', OOXML_NAMESPACES) is not None:
                    sdt_type = 'date'
                elif sdtPr_elem.find('.//w:checkBox', OOXML_NAMESPACES) is not None:
                    sdt_type = 'checkBox'
                elif sdtPr_elem.find('.//w:picture', OOXML_NAMESPACES) is not None:
                    sdt_type = 'picture'
                elif sdtPr_elem.find('.//w:group', OOXML_NAMESPACES) is not None:
                    sdt_type = 'group'
                elif sdtPr_elem.find('.//w:repeatingSection', OOXML_NAMESPACES) is not None:
                    sdt_type = 'repeatingSection'
                elif sdtPr_elem.find('.//w:repeatingSectionItem', OOXML_NAMESPACES) is not None:
                    sdt_type = 'repeatingSectionItem'
                elif sdtPr_elem.find('.//w:equation', OOXML_NAMESPACES) is not None:
                    sdt_type = 'equation'
                elif sdtPr_elem.find('.//w:bibliography', OOXML_NAMESPACES) is not None:
                    sdt_type = 'bibliography'
                elif sdtPr_elem.find('.//w:citation', OOXML_NAMESPACES) is not None:
                    sdt_type = 'citation'
                elif sdtPr_elem.find('.//w:docPartObj', OOXML_NAMESPACES) is not None:
                    sdt_type = 'docPartObj'

                if sdt_type:
                    sdt_info['type'] = sdt_type

                # Extract تگ
                tag_elem = sdtPr_elem.find('.//w:tag', OOXML_NAMESPACES)
                if tag_elem is not None:
                    sdt_info['tag'] = tag_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

                # Extract alias
                alias_elem = sdtPr_elem.find('.//w:alias', OOXML_NAMESPACES)
                if alias_elem is not None:
                    sdt_info['alias'] = alias_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')

                # Extract lock status
                lock_elem = sdtPr_elem.find('.//w:lock', OOXML_NAMESPACES)
                if lock_elem is not None:
                    lock_val = lock_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                    sdt_info['lock'] = lock_val if lock_val else 'sdtLocked'

                # Extract placeholder
                placeholder_elem = sdtPr_elem.find('.//w:placeholder', OOXML_NAMESPACES)
                if placeholder_elem is not None:
                    docPart_elem = placeholder_elem.find('.//w:docPart', OOXML_NAMESPACES)
                    if docPart_elem is not None:
                        val_elem = docPart_elem.find('.//w:val', OOXML_NAMESPACES)
                        if val_elem is not None:
                            sdt_info['placeholder'] = val_elem.text

                # Extract date format (for date picker)
                if sdt_info['type'] == 'date':
                    date_elem = sdtPr_elem.find('.//w:date', OOXML_NAMESPACES)
                    if date_elem is not None:
                        # Extract date format
                        date_format = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fullDate')
                        if date_format:
                            sdt_info['date_format'] = date_format

                        # Extract display format
                        display_format = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}dateFormat')
                        if display_format:
                            sdt_info['formatting']['display_format'] = display_format

                        # Extract language
                        lang = date_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lid')
                        if lang:
                            sdt_info['formatting']['language'] = lang

                # Extract additional formats for text and richText
                if sdt_info['type'] in ['text', 'richText']:
                    text_elem = sdtPr_elem.find('.//w:text', OOXML_NAMESPACES)
                    if text_elem is not None:
                        # Extract multiline format
                        multi_line = text_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}multiLine')
                        if multi_line:
                            sdt_info['formatting']['multi_line'] = multi_line == 'true' or multi_line == '1'

                        # Extract maxLength format
                        max_length = text_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}maxLength')
                        if max_length:
                            sdt_info['formatting']['max_length'] = int(max_length)

                # Extract checkbox status
                if sdt_info['type'] == 'checkBox':
                    checkBox_elem = sdtPr_elem.find('.//w:checkBox', OOXML_NAMESPACES)
                    if checkBox_elem is not None:
                        # Extract checked status
                        checked_elem = checkBox_elem.find('.//w:checked', OOXML_NAMESPACES)
                        if checked_elem is not None:
                            checked_val = checked_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            sdt_info['formatting']['checked'] = checked_val == 'true' or checked_val == '1' or checked_val == 'on'

                        # Extract size
                        size_elem = checkBox_elem.find('.//w:size', OOXML_NAMESPACES)
                        if size_elem is not None:
                            size_val = size_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            if size_val:
                                sdt_info['formatting']['size'] = int(size_val)

            # Extract content
            sdtContent_elem = sdt_elem.find('.//w:sdtContent', OOXML_NAMESPACES)
            if sdtContent_elem is not None:
                # Extract text from content
                content = DocxUtils.extract_text_from_element(sdtContent_elem)
                if content:
                    sdt_info['content'] = content

                # For comboBox and dropDownList, extract items
                if sdt_info['type'] in ['comboBox', 'dropDownList']:
                    if sdtPr_elem is not None:
                        list_items = []
                        # Find list items
                        for listItem in sdtPr_elem.findall('.//w:listItem', OOXML_NAMESPACES):
                            item_display = listItem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}displayText')
                            item_value = listItem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}value')
                            if item_display or item_value:
                                list_items.append({
                                    'display': item_display,
                                    'value': item_value
                                })
                        if list_items:
                            sdt_info['list_items'] = list_items

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات SDT: {str(e)}")

        return sdt_info



    @staticmethod
    def extract_drawing_info(drawing_elem: ET.Element) -> dict[str, Any]:
        """
        Extract Drawing information (including images, shapes, charts)
        
        Args:
            drawing_elem: w:drawing element
            
        Returns:
            Dict[str, Any]: Drawing information شامل:
                - type: نوع (picture, shape, chart, diagram, etc.)
                - id: شناسه
                - name: نام
                - description: توضیحات
                - size: ابعاد (width, height)
                - position: موقعیت
                - properties: خصوصیات اضافی
        """
        drawing_info = {
            'type': 'unknown',
            'id': None,
            'name': None,
            'description': None,
            'size': {'width': 0, 'height': 0},
            'position': {'x': 0, 'y': 0},
            'properties': {}
        }

        try:
            # Check type Drawing
            # Check images
            pic_elem = drawing_elem.find('.//pic:pic', OOXML_NAMESPACES)
            if pic_elem is not None:
                drawing_info['type'] = 'picture'

                # Extract image information
                nvPicPr_elem = pic_elem.find('.//pic:nvPicPr', OOXML_NAMESPACES)
                if nvPicPr_elem is not None:
                    cNvPr_elem = nvPicPr_elem.find('.//pic:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        drawing_info['id'] = cNvPr_elem.get('id')
                        drawing_info['name'] = cNvPr_elem.get('name')
                        drawing_info['description'] = cNvPr_elem.get('descr')

                # Extract dimensions
                xfrm_elem = pic_elem.find('.//a:xfrm', OOXML_NAMESPACES)
                if xfrm_elem is not None:
                    ext_elem = xfrm_elem.find('.//a:ext', OOXML_NAMESPACES)
                    if ext_elem is not None:
                        width = ext_elem.get('cx')
                        height = ext_elem.get('cy')
                        if width:
                            drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                        if height:
                            drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)

            # Check shape
            elif drawing_elem.find('.//wps:wsp', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'shape'

                # Extract shape information
                wsp_elem = drawing_elem.find('.//wps:wsp', OOXML_NAMESPACES)
                if wsp_elem is not None:
                    cNvPr_elem = wsp_elem.find('.//wp:cNvPr', OOXML_NAMESPACES)
                    if cNvPr_elem is not None:
                        drawing_info['id'] = cNvPr_elem.get('id')
                        drawing_info['name'] = cNvPr_elem.get('name')
                        drawing_info['description'] = cNvPr_elem.get('descr')

            # Check chart
            elif drawing_elem.find('.//c:chart', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'chart'

                # Extract chart information
                chart_elem = drawing_elem.find('.//c:chart', OOXML_NAMESPACES)
                if chart_elem is not None:
                    drawing_info['id'] = chart_elem.get('{http://schemas.openxmlformats.org/drawingml/2006/chart}id')

            # Check diagram
            elif drawing_elem.find('.//dgm:relIds', OOXML_NAMESPACES) is not None:
                drawing_info['type'] = 'diagram'

            # Extract position
            inline_elem = drawing_elem.find('.//wp:inline', OOXML_NAMESPACES)
            if inline_elem is not None:
                # Extract position
                extent_elem = inline_elem.find('.//wp:extent', OOXML_NAMESPACES)
                if extent_elem is not None:
                    width = extent_elem.get('cx')
                    height = extent_elem.get('cy')
                    if width and not drawing_info['size']['width']:
                        drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                    if height and not drawing_info['size']['height']:
                        drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)

                # Extract relative position
                docPr_elem = inline_elem.find('.//wp:docPr', OOXML_NAMESPACES)
                if docPr_elem is not None:
                    drawing_info['id'] = docPr_elem.get('id')
                    drawing_info['name'] = docPr_elem.get('name')
                    drawing_info['description'] = docPr_elem.get('descr')

            # Extract anchor position
            anchor_elem = drawing_elem.find('.//wp:anchor', OOXML_NAMESPACES)
            if anchor_elem is not None:
                # Extract position
                simplePos_elem = anchor_elem.find('.//wp:simplePos', OOXML_NAMESPACES)
                if simplePos_elem is not None:
                    x = simplePos_elem.get('x')
                    y = simplePos_elem.get('y')
                    if x:
                        drawing_info['position']['x'] = DocxUtils.convert_emu_to_pixels(x)
                    if y:
                        drawing_info['position']['y'] = DocxUtils.convert_emu_to_pixels(y)

                # Extract relative position
                positionH_elem = anchor_elem.find('.//wp:positionH', OOXML_NAMESPACES)
                if positionH_elem is not None:
                    posOffset = positionH_elem.find('.//wp:posOffset', OOXML_NAMESPACES)
                    if posOffset is not None and posOffset.text:
                        drawing_info['position']['x'] = DocxUtils.convert_emu_to_pixels(posOffset.text)

                positionV_elem = anchor_elem.find('.//wp:positionV', OOXML_NAMESPACES)
                if positionV_elem is not None:
                    posOffset = positionV_elem.find('.//wp:posOffset', OOXML_NAMESPACES)
                    if posOffset is not None and posOffset.text:
                        drawing_info['position']['y'] = DocxUtils.convert_emu_to_pixels(posOffset.text)

                # Extract dimensions
                extent_elem = anchor_elem.find('.//wp:extent', OOXML_NAMESPACES)
                if extent_elem is not None:
                    width = extent_elem.get('cx')
                    height = extent_elem.get('cy')
                    if width and not drawing_info['size']['width']:
                        drawing_info['size']['width'] = DocxUtils.convert_emu_to_pixels(width)
                    if height and not drawing_info['size']['height']:
                        drawing_info['size']['height'] = DocxUtils.convert_emu_to_pixels(height)

                # Extract docPr information
                docPr_elem = anchor_elem.find('.//wp:docPr', OOXML_NAMESPACES)
                if docPr_elem is not None:
                    if not drawing_info['id']:
                        drawing_info['id'] = docPr_elem.get('id')
                    if not drawing_info['name']:
                        drawing_info['name'] = docPr_elem.get('name')
                    if not drawing_info['description']:
                        drawing_info['description'] = docPr_elem.get('descr')

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"خطا در استخراج اطلاعات Drawing: {str(e)}")

        return drawing_info



    @staticmethod
    def extract_sym_info(sym_elem: ET.Element) -> dict[str, Any]:
        """
        Extract symbol information
        
        Args:
            sym_elem: w:sym element
            
        Returns:
            Dict[str, Any]: Symbol information including:
                - font: فونت نماد
                - char: کاراکتر نماد (کد یونیکد)
                - unicode: نمایش یونیکد
        """
        sym_info = {
            'font': None,
            'char': None,
            'unicode': None
        }

        try:
            # Extract font
            font = sym_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}font')
            if font:
                sym_info['font'] = font

            # Extract character
            char = sym_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}char')
            if char:
                sym_info['char'] = char
                # Convert to unicode
                try:
                    # Character is hexadecimal
                    if char.startswith('0x') or char.startswith('0X'):
                        char_code = int(char, 16)
                    else:
                        char_code = int(char)
                    sym_info['unicode'] = chr(char_code)
                except (ValueError, OverflowError):
                    sym_info['unicode'] = char

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات نماد: {str(e)}")

        return sym_info

    @staticmethod
    def extract_fld_char_info(fldChar_elem: ET.Element) -> dict[str, Any]:
        """
        Extract field character information
        
        Args:
            fldChar_elem: w:fldChar element
            
        Returns:
            Dict[str, Any]: Field character information including:
                - type: نوع (begin, separate, end)
                - dirty: وضعیت dirty
                - fldLock: وضعیت قفل
                - instrText: متن دستور فیلد
        """
        fld_char_info = {
            'type': None,
            'dirty': False,
            'fldLock': False,
            'instrText': None
        }

        try:
            # Extract type
            fld_char_type = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldCharType')
            if fld_char_type:
                fld_char_info['type'] = fld_char_type

            # Extract dirty
            dirty = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}dirty')
            if dirty:
                fld_char_info['dirty'] = dirty == 'true' or dirty == '1'

            # Extract fldLock
            fld_lock = fldChar_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}fldLock')
            if fld_lock:
                fld_char_info['fldLock'] = fld_lock == 'true' or fld_lock == '1'

            # Extract instruction text (from adjacent elements)
            parent = fldChar_elem.getparent()
            if parent is not None:
                # Search for w:instrText element at the same level
                for sibling in parent:
                    if sibling.tag.endswith('instrText'):
                        fld_char_info['instrText'] = sibling.text
                        break

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در Extract field character information: {str(e)}")

        return fld_char_info



    @staticmethod
    def extract_year_short_info(year_short_elem: ET.Element) -> dict[str, Any]:
        """
        Extract year short information
        
        Args:
            year_short_elem: w:yearShort element
            
        Returns:
            Dict[str, Any]: Year short information including:
                - type: همیشه 'yearShort'
                - format: فرمت نمایش
                - value: مقدار سال
        """
        year_short_info = {
            'type': 'yearShort',
            'format': 'yy',
            'value': None
        }

        try:
            # Extract properties from element
            # In DOCX, yearShort is usually plain text
            # But may have formatting properties
            parent = year_short_elem.getparent()
            if parent is not None:
                # Check related elements for format
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # If field is DATE
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # Extract format from field instruction
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # Extract format
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'yyyy' in format_part:
                                    year_short_info['format'] = 'yyyy'
                                elif 'yy' in format_part:
                                    year_short_info['format'] = 'yy'
                            break

            # Year value (from element text)
            if year_short_elem.text:
                year_short_info['value'] = year_short_elem.text

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات سال کوتاه: {str(e)}")

        return year_short_info

    @staticmethod
    def extract_month_short_info(month_short_elem: ET.Element) -> dict[str, Any]:
        """
        Extract month short information
        
        Args:
            month_short_elem: w:monthShort element
            
        Returns:
            Dict[str, Any]: Month short information including:
                - type: همیشه 'monthShort'
                - format: فرمت نمایش
                - value: مقدار ماه
        """
        month_short_info = {
            'type': 'monthShort',
            'format': 'M',
            'value': None
        }

        try:
            # Extract properties from element
            parent = month_short_elem.getparent()
            if parent is not None:
                # Check related elements for format
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # If field is DATE
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # Extract format from field instruction
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # Extract format
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'MMMM' in format_part:
                                    month_short_info['format'] = 'MMMM'  # Name کامل ماه
                                elif 'MMM' in format_part:
                                    month_short_info['format'] = 'MMM'  # Name کوتاه ماه
                                elif 'MM' in format_part:
                                    month_short_info['format'] = 'MM'  # ماه دو رقمی
                                elif 'M' in format_part:
                                    month_short_info['format'] = 'M'  # ماه یک یا دو رقمی
                            break

            # Month value (from element text)
            if month_short_elem.text:
                month_short_info['value'] = month_short_elem.text

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات ماه کوتاه: {str(e)}")

        return month_short_info

    @staticmethod
    def extract_day_short_info(day_short_elem: ET.Element) -> dict[str, Any]:
        """
        Extract day short information
        
        Args:
            day_short_elem: w:dayShort element
            
        Returns:
            Dict[str, Any]: Day short information including:
                - type: همیشه 'dayShort'
                - format: فرمت نمایش
                - value: مقدار روز
        """
        day_short_info = {
            'type': 'dayShort',
            'format': 'd',
            'value': None
        }

        try:
            # Extract properties from element
            parent = day_short_elem.getparent()
            if parent is not None:
                # Check related elements for format
                for sibling in parent:
                    if sibling.tag.endswith('fldChar'):
                        # If field is DATE
                        fld_char_info = DocxUtils.extract_fld_char_info(sibling)
                        if fld_char_info.get('instrText') and 'DATE' in fld_char_info['instrText']:
                            # Extract format from field instruction
                            instr_text = fld_char_info['instrText']
                            if '\\@' in instr_text:
                                # Extract format
                                format_part = instr_text.split('\\@')[1].strip().strip('"\'')
                                if 'dddd' in format_part:
                                    day_short_info['format'] = 'dddd'  # Name کامل روز
                                elif 'ddd' in format_part:
                                    day_short_info['format'] = 'ddd'  # Name کوتاه روز
                                elif 'dd' in format_part:
                                    day_short_info['format'] = 'dd'  # روز دو رقمی
                                elif 'd' in format_part:
                                    day_short_info['format'] = 'd'  # روز یک یا دو رقمی
                            break

            # Day value (from element text)
            if day_short_elem.text:
                day_short_info['value'] = day_short_elem.text

        except Exception as e:
            import logging
            logging.getLogger(__name__).debug(f"خطا در استخراج اطلاعات روز کوتاه: {str(e)}")

        return day_short_info

    @staticmethod
    def convert_twips_to_points(value: str | int | float | None) -> float | None:
        return parse_dxa_to_points(value)

    @staticmethod
    def convert_emu_to_pixels(value: str | int | float | None, dpi: int = 96) -> float | None:
        return parse_emu_to_pixels(value, dpi)


def safe_find(element: ET.Element | None, tag: str, namespaces: dict[str, str] | None = None) -> ET.Element | None:
    """
    Safely find a single child element.
    
    Args:
        element: Parent element or None
        tag: Tag to search for (can include namespace prefix like 'w:p')
        namespaces: Optional namespace mapping dictionary
        
    Returns:
        Found element or None
    """
    if element is None:
        return None

    if namespaces:
        # Handle tag with namespace prefix
        if ':' in tag:
            prefix, local_name = tag.split(':', 1)
            ns_uri = namespaces.get(prefix, '')
            if ns_uri:
                tag = f'{{{ns_uri}}}{local_name}'

        return element.find(tag, namespaces)
    else:
        return element.find(tag)


def safe_findall(element: ET.Element | None, tag: str, namespaces: dict[str, str] | None = None) -> list[ET.Element]:
    """
    Safely find all child elements matching tag.
    
    Args:
        element: Parent element or None
        tag: Tag to search for (can include namespace prefix like 'w:p')
        namespaces: Optional namespace mapping dictionary
        
    Returns:
        List of found elements (empty list if none found or element is None)
    """
    if element is None:
        return []

    if namespaces:
        # Handle tag with namespace prefix
        if ':' in tag:
            prefix, local_name = tag.split(':', 1)
            ns_uri = namespaces.get(prefix, '')
            if ns_uri:
                tag = f'{{{ns_uri}}}{local_name}'

        return element.findall(tag, namespaces)
    else:
        return element.findall(tag)


def get_element_text(element: ET.Element | None, tag: str | None = None, namespaces: dict[str, str] | None = None) -> str | None:
    """
    Get text content from an element or its child.
    
    Args:
        element: Parent element or None
        tag: Optional child tag to find first
        namespaces: Optional namespace mapping
        
    Returns:
        Text content or None
    """
    if element is None:
        return None

    target = element
    if tag:
        target = safe_find(element, tag, namespaces)

    if target is None:
        return None

    if target.text:
        return target.text.strip()

    return None


def xml_to_text(element: ET.Element, include_tail: bool = True) -> str:
    """
    Extract all text from an XML element recursively.
    
    Args:
        element: XML element
        include_tail: Whether to include tail text of children
        
    Returns:
        Concatenated text content
    """
    if element is None:
        return ""

    texts = []

    if element.text:
        texts.append(element.text)

    for child in element:
        texts.append(xml_to_text(child, include_tail))
        if include_tail and child.tail:
            texts.append(child.tail)

    if not include_tail and element.tail:
        texts.append(element.tail)

    return ''.join(texts)


def parse_border_element(border_elem: ET.Element) -> dict[str, Any]:
    """
    Parse a Word border element (w:top, w:bottom, etc.).
    
    Args:
        border_elem: Border XML element
        
    Returns:
        Dictionary with border properties
    """
    border_info = {}

    if border_elem is None:
        return border_info

    # Border style
    val = border_elem.get(f'{{{NS["w"]}}}val')
    if val:
        border_info['style'] = val

    # Border color
    color = border_elem.get(f'{{{NS["w"]}}}color')
    if color:
        border_info['color'] = f"#{color}" if not color.startswith('#') else color

    # Border width (in eighths of a point)
    sz = border_elem.get(f'{{{NS["w"]}}}sz')
    if sz:
        try:
            border_info['width'] = float(sz) / 8.0  # Convert to points
        except ValueError:
            border_info['width'] = sz

    # Space between border and content
    space = border_elem.get(f'{{{NS["w"]}}}space')
    if space:
        try:
            border_info['space'] = float(space)
        except ValueError:
            border_info['space'] = space

    # Theme color
    theme_color = border_elem.get(f'{{{NS["w"]}}}themeColor')
    if theme_color:
        border_info['theme_color'] = theme_color

    # Theme tint/shade
    theme_tint = border_elem.get(f'{{{NS["w"]}}}themeTint')
    if theme_tint:
        border_info['theme_tint'] = theme_tint

    theme_shade = border_elem.get(f'{{{NS["w"]}}}themeShade')
    if theme_shade:
        border_info['theme_shade'] = theme_shade

    return border_info


def parse_shading_element(shading_elem: ET.Element) -> dict[str, Any]:
    """
    Parse a Word shading element (w:shd).
    
    Args:
        shading_elem: Shading XML element
        
    Returns:
        Dictionary with shading properties
    """
    shading_info = {}

    if shading_elem is None:
        return shading_info

    # Fill color
    fill = shading_elem.get(f'{{{NS["w"]}}}fill')
    if fill:
        shading_info['fill'] = f"#{fill}" if not fill.startswith('#') else fill

    # Pattern type
    val = shading_elem.get(f'{{{NS["w"]}}}val')
    if val:
        shading_info['pattern'] = val

    # Pattern color
    color = shading_elem.get(f'{{{NS["w"]}}}color')
    if color:
        shading_info['color'] = f"#{color}" if not color.startswith('#') else color

    # Theme fill
    theme_fill = shading_elem.get(f'{{{NS["w"]}}}themeFill')
    if theme_fill:
        shading_info['theme_fill'] = theme_fill

    # Theme fill tint/shade
    theme_fill_tint = shading_elem.get(f'{{{NS["w"]}}}themeFillTint')
    if theme_fill_tint:
        shading_info['theme_fill_tint'] = theme_fill_tint

    theme_fill_shade = shading_elem.get(f'{{{NS["w"]}}}themeFillShade')
    if theme_fill_shade:
        shading_info['theme_fill_shade'] = theme_fill_shade

    # Theme color
    theme_color = shading_elem.get(f'{{{NS["w"]}}}themeColor')
    if theme_color:
        shading_info['theme_color'] = theme_color

    # Theme tint/shade
    theme_tint = shading_elem.get(f'{{{NS["w"]}}}themeTint')
    if theme_tint:
        shading_info['theme_tint'] = theme_tint

    theme_shade = shading_elem.get(f'{{{NS["w"]}}}themeShade')
    if theme_shade:
        shading_info['theme_shade'] = theme_shade

    return shading_info


def get_attribute(element: ET.Element, attr_name: str, namespace: str = 'w') -> str | None:
    """
    Safely get an attribute value from an element with namespace.
    
    Args:
        element: XML element
        attr_name: Attribute name
        namespace: Namespace prefix (default 'w')
        
    Returns:
        Attribute value or None
    """
    if element is None:
        return None

    ns_uri = NS.get(namespace, '')
    if ns_uri:
        return element.get(f'{{{ns_uri}}}{attr_name}')
    else:
        return element.get(attr_name)


def extract_text_from_run(run_elem: ET.Element) -> str:
    """
    Extract text from a Word run element (w:r).
    
    Args:
        run_elem: Run XML element
        
    Returns:
        Extracted text
    """
    if run_elem is None:
        return ""

    texts = []

    for t_elem in safe_findall(run_elem, './/w:t'):
        if t_elem.text:
            texts.append(t_elem.text)

    # Handle special characters
    for cr_elem in safe_findall(run_elem, './/w:cr'):
        texts.append('\n')

    for br_elem in safe_findall(run_elem, './/w:br'):
        texts.append('\n')

    for tab_elem in safe_findall(run_elem, './/w:tab'):
        texts.append('\t')

    return ''.join(texts)
