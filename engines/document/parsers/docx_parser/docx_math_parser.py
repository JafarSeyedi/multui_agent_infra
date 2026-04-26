# engines/document/parsers/docx_parser/docx_math_parser.py
"""
Parser for Office Math Markup Language (OMML) in DOCX documents.
Converts OMML XML elements into DOCXMath intermediate models.
"""

import re
from typing import Optional, Dict, Any, List
from xml.etree import ElementTree as ET

from .docx_models import (
    DOCXMath,
    DOCXMathElement,
    DOCXRunProperties
)
from .docx_utils import (
    NS,
    xml_to_text,
    get_element_text,
    safe_find,
    safe_findall
)


class OMMLParser:
    """
    Parser for Office Math Markup Language (OMML).
    
    OMML is the native math format in DOCX files, found in:
    - m:oMath (inline math)
    - m:oMathPara (display math paragraph)
    """
    
    # Namespace mappings for OMML
    M_NS = NS.get('m', 'http://schemas.openxmlformats.org/officeDocument/2006/math')
    W_NS = NS.get('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
    
    def __init__(self):
        self._register_namespaces()
    
    def _register_namespaces(self):
        """Register namespaces for XPath queries."""
        namespaces = {
            'm': self.M_NS,
            'w': self.W_NS,
        }
        for prefix, uri in namespaces.items():
            if uri:
                ET.register_namespace(prefix, uri)
    
    # ============================================================
    # PUBLIC API
    # ============================================================
    
    def parse_math_paragraph(self, math_para_elem: ET.Element) -> Optional[DOCXMath]:
        """
        Parse an m:oMathPara element (display math).
        
        Args:
            math_para_elem: The m:oMathPara XML element
            
        Returns:
            DOCXMath object or None if parsing fails
        """
        if math_para_elem is None:
            return None
        
        # An oMathPara contains one or more oMath elements
        math_elems = safe_findall(math_para_elem, './/m:oMath')
        
        if not math_elems:
            return None
        
        # For now, parse the first equation. 
        # Multiple equations in one paragraph are rare.
        return self.parse_math(math_elems[0], is_display=True)
    
    def parse_math(self, math_elem: ET.Element, is_display: bool = False) -> Optional[DOCXMath]:
        """
        Parse an m:oMath element.
        
        Args:
            math_elem: The m:oMath XML element
            is_display: Whether this is display math (block) or inline
            
        Returns:
            DOCXMath object or None if parsing fails
        """
        if math_elem is None:
            return None
        
        # Parse the root math element recursively
        root_element = self._parse_math_element(math_elem)
        
        if root_element is None:
            return None
        
        return DOCXMath(
            is_display=is_display,
            root=root_element
        )
    
    def parse_math_from_xml(self, xml_string: str, is_display: bool = False) -> Optional[DOCXMath]:
        """
        Parse OMML from an XML string.
        
        Args:
            xml_string: Raw OMML XML string
            is_display: Whether this is display math (block) or inline
            
        Returns:
            DOCXMath object or None if parsing fails
        """
        try:
            root = ET.fromstring(xml_string)
            
            # Handle both oMath and oMathPara
            tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            
            if tag == 'oMathPara':
                return self.parse_math_paragraph(root)
            elif tag == 'oMath':
                return self.parse_math(root, is_display=is_display)
            else:
                # Maybe the root is a math element directly
                return self.parse_math(root, is_display=is_display)
                
        except ET.ParseError:
            return None
    
    # ============================================================
    # CORE PARSING LOGIC
    # ============================================================
    
    def _parse_math_element(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """
        Recursively parse an OMML element into a DOCXMathElement.
        
        OMML elements can be:
        - Run elements (m:r) containing text
        - Structured elements (m:f, m:rad, m:nary, etc.)
        - Control elements (m:ctrlPr)
        """
        tag = self._get_local_tag(elem)
        
        if tag == 'oMath':
            # oMath is a container - parse its children and combine
            return self._parse_math_container(elem)
        
        elif tag == 'r':
            # Run element - contains text
            return self._parse_math_run(elem)
        
        elif tag == 'f':
            # Fraction
            return self._parse_fraction(elem)
        
        elif tag == 'rad':
            # Radical (square root, nth root)
            return self._parse_radical(elem)
        
        elif tag == 'nary':
            # N-ary operator (sum, product, integral, union, etc.)
            return self._parse_nary(elem)
        
        elif tag == 'acc':
            # Accent (hat, bar, dot, etc.)
            return self._parse_accent(elem)
        
        elif tag == 'bar':
            # Bar (overbar, underbar)
            return self._parse_bar(elem)
        
        elif tag == 'box':
            # Box (for grouping)
            return self._parse_box(elem)
        
        elif tag == 'borderBox':
            # Border box
            return self._parse_border_box(elem)
        
        elif tag == 'd':
            # Delimiter (parentheses, brackets, braces)
            return self._parse_delimiter(elem)
        
        elif tag == 'eqArr':
            # Equation array
            return self._parse_equation_array(elem)
        
        elif tag == 'func':
            # Function (sin, cos, log, etc.)
            return self._parse_function(elem)
        
        elif tag == 'groupChr':
            # Group character (overbrace, underbrace)
            return self._parse_group_character(elem)
        
        elif tag == 'limLow':
            # Lower limit
            return self._parse_limit(elem, 'low')
        
        elif tag == 'limUpp':
            # Upper limit
            return self._parse_limit(elem, 'upp')
        
        elif tag == 'm':
            # Matrix
            return self._parse_matrix(elem)
        
        elif tag == 'phant':
            # Phantom (spacing placeholder)
            return self._parse_phantom(elem)
        
        elif tag == 'sPre':
            # Pre-sub-superscript
            return self._parse_pre_sub_sup(elem)
        
        elif tag == 'sSub':
            # Subscript
            return self._parse_sub_sup(elem, 'sub')
        
        elif tag == 'sSup':
            # Superscript
            return self._parse_sub_sup(elem, 'sup')
        
        elif tag == 'sSubSup':
            # Subscript and superscript
            return self._parse_sub_sup(elem, 'subsup')
        
        elif tag == 'ctrlPr':
            # Control properties - skip, handled by parent
            return None
        
        elif tag == 'argPr':
            # Argument properties - skip
            return None
        
        else:
            # Unknown element - try to parse as container
            return self._parse_math_container(elem)
    
    def _get_local_tag(self, elem: ET.Element) -> str:
        """Extract local tag name without namespace."""
        tag = elem.tag
        if '}' in tag:
            return tag.split('}')[-1]
        return tag
    
    def _parse_math_container(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """
        Parse a container element that holds multiple children.
        Returns a single element if only one child, or a row-like element if multiple.
        """
        children = []
        for child in elem:
            parsed = self._parse_math_element(child)
            if parsed is not None:
                children.append(parsed)
        
        if not children:
            return None
        
        if len(children) == 1:
            return children[0]
        
        # Multiple children - return as a 'row' element
        return DOCXMathElement(
            element_type='row',
            children=children
        )
    
    # ============================================================
    # SPECIFIC ELEMENT PARSERS
    # ============================================================
    
    def _parse_math_run(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:r element containing text."""
        # Extract text content
        text_elem = safe_find(elem, './/m:t')
        if text_elem is None:
            return None
        
        text = get_element_text(text_elem) or ''
        
        # Extract run properties
        properties = self._parse_run_properties(elem)
        
        return DOCXMathElement(
            element_type='r',
            text=text,
            text_properties=properties
        )
    
    def _parse_run_properties(self, elem: ET.Element) -> DOCXRunProperties:
        """Parse m:rPr element for run properties."""
        props = DOCXRunProperties()
        
        rpr_elem = safe_find(elem, './/m:rPr')
        if rpr_elem is None:
            return props
        
        # Check for styling elements
        # m:sty - style (b, i, bi)
        sty_elem = safe_find(rpr_elem, './/m:sty')
        if sty_elem is not None:
            val = sty_elem.get('m:val', '')
            props.bold = 'b' in val
            props.italic = 'i' in val
        
        # m:scr - script (roman, sans-serif, script, etc.)
        scr_elem = safe_find(rpr_elem, './/m:scr')
        if scr_elem is not None:
            # Map script style to font
            val = scr_elem.get('m:val', '')
            if val == 'sans-serif':
                props.font_name = 'Arial'
            elif val == 'script':
                props.font_name = 'Script'
            elif val == 'fraktur':
                props.font_name = 'Fraktur'
            elif val == 'double-struck':
                props.font_name = 'DoubleStruck'
            elif val == 'monospace':
                props.font_name = 'Courier New'
        
        return props
    
    def _parse_fraction(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:f element (fraction)."""
        numerator = None
        denominator = None
        
        num_elem = safe_find(elem, './/m:num')
        if num_elem is not None:
            numerator = self._parse_math_container(num_elem)
        
        den_elem = safe_find(elem, './/m:den')
        if den_elem is not None:
            denominator = self._parse_math_container(den_elem)
        
        # Get fraction type (bar or noBar)
        type_elem = safe_find(elem, './/m:type')
        frac_type = 'bar'
        if type_elem is not None:
            val = type_elem.get('m:val', 'bar')
            frac_type = val
        
        return DOCXMathElement(
            element_type='f',
            numerator=numerator,
            denominator=denominator,
            properties={'frac_type': frac_type}
        )
    
    def _parse_radical(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:rad element (square root or nth root)."""
        degree = None
        base = None
        
        deg_elem = safe_find(elem, './/m:deg')
        if deg_elem is not None:
            degree = self._parse_math_container(deg_elem)
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        return DOCXMathElement(
            element_type='rad',
            degree=degree,
            base=base
        )
    
    def _parse_nary(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:nary element (sum, product, integral, etc.)."""
        sub = None
        sup = None
        base = None
        
        sub_elem = safe_find(elem, './/m:sub')
        if sub_elem is not None:
            sub = self._parse_math_container(sub_elem)
        
        sup_elem = safe_find(elem, './/m:sup')
        if sup_elem is not None:
            sup = self._parse_math_container(sup_elem)
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        # Get the operator character
        chr_elem = safe_find(elem, './/m:chr')
        operator_char = '\u2211'  # Default: sum
        if chr_elem is not None:
            val = chr_elem.get('m:val', '')
            if val:
                operator_char = val
        
        # Get properties
        props = {}
        
        # Check for limits location
        lim_loc_elem = safe_find(elem, './/m:limLoc')
        if lim_loc_elem is not None:
            props['lim_loc'] = lim_loc_elem.get('m:val', 'undOvr')
        
        # Check for n-ary type
        type_elem = safe_find(elem, './/m:type')
        if type_elem is not None:
            props['type'] = type_elem.get('m:val', '')
        
        return DOCXMathElement(
            element_type='nary',
            text=operator_char,
            sub=sub,
            sup=sup,
            base=base,
            properties=props
        )
    
    def _parse_accent(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:acc element (accent)."""
        base = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        # Get accent character
        chr_elem = safe_find(elem, './/m:chr')
        accent_char = '\u0302'  # Default: circumflex
        if chr_elem is not None:
            val = chr_elem.get('m:val', '')
            if val:
                accent_char = val
        
        props = {'accent_char': accent_char}
        
        return DOCXMathElement(
            element_type='acc',
            base=base,
            properties=props
        )
    
    def _parse_bar(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:bar element (overbar or underbar)."""
        base = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        # Get position (top or bot)
        pos_elem = safe_find(elem, './/m:pos')
        position = 'top'
        if pos_elem is not None:
            position = pos_elem.get('m:val', 'top')
        
        return DOCXMathElement(
            element_type='bar',
            base=base,
            properties={'position': position}
        )
    
    def _parse_box(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:box element."""
        base_elem = safe_find(elem, './/m:e')
        base = None
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        return DOCXMathElement(
            element_type='box',
            base=base
        )
    
    def _parse_border_box(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:borderBox element."""
        base_elem = safe_find(elem, './/m:e')
        base = None
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        props = {}
        
        # Check which borders are shown
        hide_top = safe_find(elem, './/m:hideTop')
        hide_bottom = safe_find(elem, './/m:hideBot')
        hide_left = safe_find(elem, './/m:hideLeft')
        hide_right = safe_find(elem, './/m:hideRight')
        
        props['hide_top'] = hide_top is not None
        props['hide_bottom'] = hide_bottom is not None
        props['hide_left'] = hide_left is not None
        props['hide_right'] = hide_right is not None
        
        return DOCXMathElement(
            element_type='borderBox',
            base=base,
            properties=props
        )
    
    def _parse_delimiter(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:d element (parentheses, brackets, etc.)."""
        base = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        props: Dict[str, Any] = {}
        
        # Get left delimiter character
        beg_chr_elem = safe_find(elem, './/m:begChr')
        if beg_chr_elem is not None:
            val = beg_chr_elem.get('m:val', '(')
            props['left'] = val
        
        # Get right delimiter character
        end_chr_elem = safe_find(elem, './/m:endChr')
        if end_chr_elem is not None:
            val = end_chr_elem.get('m:val', ')')
            props['right'] = val
        
        # Check if delimiter should grow
        grow_elem = safe_find(elem, './/m:grow')
        if grow_elem is not None:
            props['grow'] = True
        
        return DOCXMathElement(
            element_type='d',
            base=base,
            properties=props
        )
    
    def _parse_equation_array(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:eqArr element."""
        rows = []
        
        for e_elem in safe_findall(elem, './/m:e'):
            row_content = self._parse_math_container(e_elem)
            if row_content is not None:
                rows.append([row_content])
        
        return DOCXMathElement(
            element_type='eqArr',
            rows=rows,
            children=[row[0] for row in rows if row]
        )
    
    def _parse_function(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:func element (sin, cos, log, etc.)."""
        func_name = None
        base = None
        
        fname_elem = safe_find(elem, './/m:fName')
        if fname_elem is not None:
            func_name = self._parse_math_container(fname_elem)
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        return DOCXMathElement(
            element_type='func',
            base=base,
            children=[func_name] if func_name else [],
            properties={'function_name': self._extract_text_from_element(func_name)}
        )
    
    def _parse_group_character(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:groupChr element (overbrace, underbrace)."""
        base = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        props = {}
        
        # Get character
        chr_elem = safe_find(elem, './/m:chr')
        if chr_elem is not None:
            val = chr_elem.get('m:val', '')
            props['char'] = val
        
        # Get position
        pos_elem = safe_find(elem, './/m:pos')
        if pos_elem is not None:
            val = pos_elem.get('m:val', 'top')
            props['position'] = val
        
        return DOCXMathElement(
            element_type='groupChr',
            base=base,
            properties=props
        )
    
    def _parse_limit(self, elem: ET.Element, limit_type: str) -> Optional[DOCXMathElement]:
        """Parse m:limLow or m:limUpp element."""
        base = None
        limit = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        lim_elem = safe_find(elem, './/m:lim')
        if lim_elem is not None:
            limit = self._parse_math_container(lim_elem)
        
        element_type = 'limLow' if limit_type == 'low' else 'limUpp'
        
        result = DOCXMathElement(
            element_type=element_type,
            base=base
        )
        
        if limit_type == 'low':
            result.sub = limit
        else:
            result.sup = limit
        
        return result
    
    def _parse_matrix(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:m element (matrix)."""
        rows = []
        
        for mr_elem in safe_findall(elem, './/m:mr'):
            row_cells = []
            for me_elem in safe_findall(mr_elem, './/m:e'):
                cell_content = self._parse_math_container(me_elem)
                if cell_content is not None:
                    row_cells.append(cell_content)
            
            if row_cells:
                rows.append(row_cells)
        
        props = {}
        
        # Get matrix properties
        mc_pr_elem = safe_find(elem, './/m:mPr')
        if mc_pr_elem is not None:
            # Column spacing
            csp_elem = safe_find(mc_pr_elem, './/m:cSp')
            if csp_elem is not None:
                props['col_spacing'] = csp_elem.get('m:val', '0')
            
            # Row spacing
            rsp_elem = safe_find(mc_pr_elem, './/m:rSp')
            if rsp_elem is not None:
                props['row_spacing'] = rsp_elem.get('m:val', '0')
        
        return DOCXMathElement(
            element_type='m',
            rows=rows,
            properties=props
        )
    
    def _parse_phantom(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:phant element (spacing placeholder)."""
        base = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        props: Dict[str, Any] = {}
        
        # Check what is shown
        show_elem = safe_find(elem, './/m:show')
        if show_elem is not None:
            props['show'] = show_elem.get('m:val', '0')
        
        zero_width = safe_find(elem, './/m:zeroWid')
        if zero_width is not None:
            props['zero_width'] = True
        
        zero_ascent = safe_find(elem, './/m:zeroAsc')
        if zero_ascent is not None:
            props['zero_ascent'] = True
        
        zero_descent = safe_find(elem, './/m:zeroDesc')
        if zero_descent is not None:
            props['zero_descent'] = True
        
        return DOCXMathElement(
            element_type='phant',
            base=base,
            properties=props
        )
    
    def _parse_pre_sub_sup(self, elem: ET.Element) -> Optional[DOCXMathElement]:
        """Parse an m:sPre element (pre-subscript and pre-superscript)."""
        base = None
        sub = None
        sup = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        sub_elem = safe_find(elem, './/m:sub')
        if sub_elem is not None:
            sub = self._parse_math_container(sub_elem)
        
        sup_elem = safe_find(elem, './/m:sup')
        if sup_elem is not None:
            sup = self._parse_math_container(sup_elem)
        
        return DOCXMathElement(
            element_type='sPre',
            base=base,
            sub=sub,
            sup=sup
        )
    
    def _parse_sub_sup(self, elem: ET.Element, ss_type: str) -> Optional[DOCXMathElement]:
        """Parse m:sSub, m:sSup, or m:sSubSup element."""
        base = None
        sub = None
        sup = None
        
        base_elem = safe_find(elem, './/m:e')
        if base_elem is not None:
            base = self._parse_math_container(base_elem)
        
        if ss_type in ('sub', 'subsup'):
            sub_elem = safe_find(elem, './/m:sub')
            if sub_elem is not None:
                sub = self._parse_math_container(sub_elem)
        
        if ss_type in ('sup', 'subsup'):
            sup_elem = safe_find(elem, './/m:sup')
            if sup_elem is not None:
                sup = self._parse_math_container(sup_elem)
        
        return DOCXMathElement(
            element_type=ss_type,
            base=base,
            sub=sub,
            sup=sup
        )
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _extract_text_from_element(self, elem: Optional[DOCXMathElement]) -> str:
        """Extract plain text from a math element for function names, etc."""
        if elem is None:
            return ''
        
        if elem.text:
            return elem.text
        
        if elem.children:
            texts = []
            for child in elem.children:
                text = self._extract_text_from_element(child)
                if text:
                    texts.append(text)
            return ''.join(texts)
        
        return ''
    
    def to_latex(self, math_elem: DOCXMathElement) -> str:
        """
        Convert a DOCXMathElement to LaTeX.
        This is a convenience method for USDM conversion.
        """
        if math_elem is None:
            return ''
        props = math_elem.properties or {}
        if math_elem.element_type == 'r':
            return math_elem.text or ''
        
        elif math_elem.element_type == 'row':
            return ''.join(self.to_latex(child) for child in math_elem.children)
        
        elif math_elem.element_type == 'f':
            num = self.to_latex(math_elem.numerator) if math_elem.numerator else ''
            den = self.to_latex(math_elem.denominator) if math_elem.denominator else ''
            return f'\\frac{{{num}}}{{{den}}}'
        
        elif math_elem.element_type == 'rad':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            degree = self.to_latex(math_elem.degree) if math_elem.degree else ''
            if degree:
                return f'\\sqrt[{degree}]{{{base}}}'
            return f'\\sqrt{{{base}}}'
        
        elif math_elem.element_type == 'nary':
            op_map = {
                '\u2211': '\\sum',
                '\u220f': '\\prod',
                '\u222b': '\\int',
                '\u222c': '\\iint',
                '\u222d': '\\iiint',
                '\u222e': '\\oint',
                '\u22c3': '\\bigcup',
                '\u22c2': '\\bigcap',
                '\u2a01': '\\bigoplus',
                '\u2a02': '\\bigotimes',
                '\u22c0': '\\bigwedge',
                '\u22c1': '\\bigvee',
            }
            op = op_map.get(math_elem.text or '', '')
            
            sub = self.to_latex(math_elem.sub) if math_elem.sub else ''
            sup = self.to_latex(math_elem.sup) if math_elem.sup else ''
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            
            limits = ''
            if sub:
                limits += f'_{{{sub}}}'
            if sup:
                limits += f'^{{{sup}}}'
            
            return f'{op}{limits} {base}'
        
        elif math_elem.element_type == 'acc':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            acc_map = {
                '\u0302': '\\hat',
                '\u0303': '\\tilde',
                '\u0304': '\\bar',
                '\u0305': '\\overline',
                '\u0306': '\\breve',
                '\u0307': '\\dot',
                '\u0308': '\\ddot',
                '\u0309': '\\ovhook',
                '\u030c': '\\check',
                '\u030d': '\\acute',
                '\u030e': '\\grave',
            }
            acc = acc_map.get(props.get('accent_char', ''), '\\hat')
            return f'{acc}{{{base}}}'
        
        elif math_elem.element_type == 'bar':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            pos = props.get('position', 'top')
            if pos == 'top':
                return f'\\overline{{{base}}}'
            else:
                return f'\\underline{{{base}}}'
        
        elif math_elem.element_type == 'd':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            left = props.get('left', '(')
            right = props.get('right', ')')
            
            # Escape special LaTeX characters
            left = left.replace('{', '\\{').replace('}', '\\}').replace('[', '[').replace(']', ']')
            right = right.replace('{', '\\{').replace('}', '\\}').replace('[', '[').replace(']', ']')
            
            if left == '|' or left == '\\|':
                left = '\\lvert'
            if right == '|' or right == '\\|':
                right = '\\rvert'
            
            return f'\\left{left} {base} \\right{right}'
        
        elif math_elem.element_type == 'func':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            fname = props.get('function_name', '')
            return f'\\{fname}{{{base}}}'
        
        elif math_elem.element_type == 'sub':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            sub = self.to_latex(math_elem.sub) if math_elem.sub else ''
            return f'{base}_{{{sub}}}'
        
        elif math_elem.element_type == 'sup':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            sup = self.to_latex(math_elem.sup) if math_elem.sup else ''
            return f'{base}^{{{sup}}}'
        
        elif math_elem.element_type == 'subsup':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            sub = self.to_latex(math_elem.sub) if math_elem.sub else ''
            sup = self.to_latex(math_elem.sup) if math_elem.sup else ''
            return f'{base}_{{{sub}}}^{{{sup}}}'
        
        elif math_elem.element_type == 'm':
            # Matrix
            rows_latex = []
            for row in math_elem.rows:
                cells = [self.to_latex(cell) for cell in row]
                rows_latex.append(' & '.join(cells))
            matrix_content = ' \\\\ '.join(rows_latex)
            return f'\\begin{{pmatrix}}{matrix_content}\\end{{pmatrix}}'
        
        elif math_elem.element_type == 'box':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            return f'{{{base}}}'
        
        elif math_elem.element_type == 'groupChr':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            pos = props.get('position', 'top')
            if pos == 'top':
                return f'\\overbrace{{{base}}}'
            else:
                return f'\\underbrace{{{base}}}'
        
        elif math_elem.element_type == 'limLow':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            sub = self.to_latex(math_elem.sub) if math_elem.sub else ''
            return f'\\lim_{{{sub}}} {base}'
        
        elif math_elem.element_type == 'limUpp':
            base = self.to_latex(math_elem.base) if math_elem.base else ''
            sup = self.to_latex(math_elem.sup) if math_elem.sup else ''
            return f'\\lim^{{{sup}}} {base}'
        
        else:
            # Fallback for unknown types
            if math_elem.children:
                return ''.join(self.to_latex(child) for child in math_elem.children)
            return math_elem.text or ''