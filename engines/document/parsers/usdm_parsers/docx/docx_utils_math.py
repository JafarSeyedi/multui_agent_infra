"""Mixin for DOCX math-related utility methods"""

# mypy: disable-error-code="attr-defined"
import xml.etree.ElementTree as ET
from typing import Any

from .docx_utils_base import OOXML_NAMESPACES


class DocxMath:
    """Mixin providing DOCX math extraction methods"""

    @staticmethod
    def convert_omml_to_latex(omml_elem: ET.Element) -> str | None:
        from .docx_utils import DocxUtils

        try:
            latex_parts = []

            for elem in omml_elem.iter():
                if elem.tag.endswith('oMath'):
                    continue
                elif elem.tag.endswith('acc'):
                    acc_elem = elem.find('.//m:accPr', OOXML_NAMESPACES)
                    if acc_elem is not None:
                        chr_elem = acc_elem.find('.//m:chr', OOXML_NAMESPACES)
                        if chr_elem is not None:
                            chr_val = chr_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                            if chr_val:
                                base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                                if base_elem is not None:
                                    base_text = DocxUtils.extract_text_from_element(base_elem)
                                    if chr_val == '\u0302':
                                        latex_parts.append(f"\\hat{{{base_text}}}")
                                    elif chr_val == '\u0304':
                                        latex_parts.append(f"\\bar{{{base_text}}}")
                                    elif chr_val == '\u20d7':
                                        latex_parts.append(f"\\vec{{{base_text}}}")
                                    else:
                                        latex_parts.append(f"{base_text}")
                elif elem.tag.endswith('rad'):
                    deg_elem = elem.find('.//m:deg', OOXML_NAMESPACES)
                    rad_elem = elem.find('.//m:e', OOXML_NAMESPACES)

                    if rad_elem is not None:
                        rad_text = DocxUtils.extract_text_from_element(rad_elem)
                        if deg_elem is not None:
                            deg_text = DocxUtils.extract_text_from_element(deg_elem)
                            latex_parts.append(f"\\sqrt[{deg_text}]{{{rad_text}}}")
                        else:
                            latex_parts.append(f"\\sqrt{{{rad_text}}}")
                elif elem.tag.endswith('frac'):
                    num_elem = elem.find('.//m:num', OOXML_NAMESPACES)
                    den_elem = elem.find('.//m:den', OOXML_NAMESPACES)

                    if num_elem is not None and den_elem is not None:
                        num_text = DocxUtils.extract_text_from_element(num_elem)
                        den_text = DocxUtils.extract_text_from_element(den_elem)
                        latex_parts.append(f"\\frac{{{num_text}}}{{{den_text}}}")
                elif elem.tag.endswith('sup'):
                    base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                    sup_elem = elem.find('.//m:sup', OOXML_NAMESPACES)

                    if base_elem is not None and sup_elem is not None:
                        base_text = DocxUtils.extract_text_from_element(base_elem)
                        sup_text = DocxUtils.extract_text_from_element(sup_elem)
                        latex_parts.append(f"{{{base_text}}}^{{{sup_text}}}")
                elif elem.tag.endswith('sub'):
                    base_elem = elem.find('.//m:e', OOXML_NAMESPACES)
                    sub_elem = elem.find('.//m:sub', OOXML_NAMESPACES)

                    if base_elem is not None and sub_elem is not None:
                        base_text = DocxUtils.extract_text_from_element(base_elem)
                        sub_text = DocxUtils.extract_text_from_element(sub_elem)
                        latex_parts.append(f"{{{base_text}}}_{{{sub_text}}}")
                elif elem.tag.endswith('r'):
                    text = DocxUtils.extract_text_from_element(elem)
                    if text:
                        latex_parts.append(text)

            if latex_parts:
                return ' '.join(latex_parts)

            simple_text = DocxUtils.extract_text_from_element(omml_elem)
            if simple_text:
                return f"${simple_text}$"

            return None

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error converting OMML to LaTeX: {str(e)}")
            return None

    @staticmethod
    def extract_math_info(math_elem: ET.Element) -> dict[str, Any]:
        math_info: dict[str, Any] = {
            'type': 'inline',
            'latex': None,
            'omml_xml': None,
            'properties': {}
        }

        try:
            if math_elem.tag.endswith('oMathPara'):
                math_info['type'] = 'paragraph'

            import xml.etree.ElementTree as ET
            math_info['omml_xml'] = ET.tostring(math_elem, encoding='unicode')

            try:
                latex = DocxMath.convert_omml_to_latex(math_elem)
                if latex:
                    math_info['latex'] = latex
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"Error converting OMML to LaTeX: {str(e)}")

            mathPr_elem = math_elem.find('.//m:mathPr', OOXML_NAMESPACES)
            if mathPr_elem is not None:
                justify_elem = mathPr_elem.find('.//m:jc', OOXML_NAMESPACES)
                if justify_elem is not None:
                    justify_val = justify_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if justify_val:
                        math_info['properties']['justify'] = justify_val

                breakBin_elem = mathPr_elem.find('.//m:brkBin', OOXML_NAMESPACES)
                if breakBin_elem is not None:
                    breakBin_val = breakBin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if breakBin_val:
                        math_info['properties']['break_bin'] = breakBin_val

                breakBinSub_elem = mathPr_elem.find('.//m:brkBinSub', OOXML_NAMESPACES)
                if breakBinSub_elem is not None:
                    breakBinSub_val = breakBinSub_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if breakBinSub_val:
                        math_info['properties']['break_bin_sub'] = breakBinSub_val

                smallFrac_elem = mathPr_elem.find('.//m:smallFrac', OOXML_NAMESPACES)
                if smallFrac_elem is not None:
                    smallFrac_val = smallFrac_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if smallFrac_val:
                        math_info['properties']['small_frac'] = smallFrac_val == 'on'

                dispDef_elem = mathPr_elem.find('.//m:dispDef', OOXML_NAMESPACES)
                if dispDef_elem is not None:
                    dispDef_val = dispDef_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if dispDef_val:
                        math_info['properties']['disp_def'] = dispDef_val == 'on'

                lMargin_elem = mathPr_elem.find('.//m:lMargin', OOXML_NAMESPACES)
                if lMargin_elem is not None:
                    lMargin_val = lMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if lMargin_val:
                        math_info['properties']['left_margin'] = int(lMargin_val)

                rMargin_elem = mathPr_elem.find('.//m:rMargin', OOXML_NAMESPACES)
                if rMargin_elem is not None:
                    rMargin_val = rMargin_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if rMargin_val:
                        math_info['properties']['right_margin'] = int(rMargin_val)

                defJc_elem = mathPr_elem.find('.//m:defJc', OOXML_NAMESPACES)
                if defJc_elem is not None:
                    defJc_val = defJc_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if defJc_val:
                        math_info['properties']['default_justify'] = defJc_val

                preSp_elem = mathPr_elem.find('.//m:preSp', OOXML_NAMESPACES)
                if preSp_elem is not None:
                    preSp_val = preSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if preSp_val:
                        math_info['properties']['pre_spacing'] = int(preSp_val)

                postSp_elem = mathPr_elem.find('.//m:postSp', OOXML_NAMESPACES)
                if postSp_elem is not None:
                    postSp_val = postSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if postSp_val:
                        math_info['properties']['post_spacing'] = int(postSp_val)

                interSp_elem = mathPr_elem.find('.//m:interSp', OOXML_NAMESPACES)
                if interSp_elem is not None:
                    interSp_val = interSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if interSp_val:
                        math_info['properties']['inter_spacing'] = int(interSp_val)

                intraSp_elem = mathPr_elem.find('.//m:intraSp', OOXML_NAMESPACES)
                if intraSp_elem is not None:
                    intraSp_val = intraSp_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if intraSp_val:
                        math_info['properties']['intra_spacing'] = int(intraSp_val)

                wrapIndent_elem = mathPr_elem.find('.//m:wrapIndent', OOXML_NAMESPACES)
                if wrapIndent_elem is not None:
                    wrapIndent_val = wrapIndent_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapIndent_val:
                        math_info['properties']['wrap_indent'] = int(wrapIndent_val)

                wrapRight_elem = mathPr_elem.find('.//m:wrapRight', OOXML_NAMESPACES)
                if wrapRight_elem is not None:
                    wrapRight_val = wrapRight_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if wrapRight_val:
                        math_info['properties']['wrap_right'] = wrapRight_val == 'on'

                mathFont_elem = mathPr_elem.find('.//m:mathFont', OOXML_NAMESPACES)
                if mathFont_elem is not None:
                    mathFont_val = mathFont_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/math}val')
                    if mathFont_val:
                        math_info['properties']['math_font'] = mathFont_val

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error extracting math information: {str(e)}")

        return math_info
