# engines/document/writers/spreadsheet_writer/xlsx/styles_writer.py
"""
Styles writer for XLSX.
Generates styles.xml from fonts, fills, borders, number formats, and cell formats.
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..base import ESDMBaseWriter

from .const import XML_NAMESPACES


class StylesWriter:
    """Writes styles.xml using the parent writer's style caches."""

    def __init__(self, parent_writer: ESDMBaseWriter):
        self._parent = parent_writer

    def write(self) -> str:
        """
        Generate styles.xml content.
        Returns the XML as a string with proper declaration and namespace.
        """
        root = ET.Element('styleSheet', {'xmlns': XML_NAMESPACES['']})

        # Number formats
        self._write_number_formats(root)

        # Fonts
        self._write_fonts(root)

        # Fills
        self._write_fills(root)

        # Borders
        self._write_borders(root)

        # Cell style XFs (cellStyleXfs) – typically a default style
        self._write_cell_style_xfs(root)

        # Cell XFs (cellXfs) – the actual formats used by cells
        self._write_cell_xfs(root)

        # Cell styles (named styles, optional)
        self._write_cell_styles(root)

        # Differential formats (used by conditional formatting)
        self._write_differential_formats(root)

        # Table styles (optional)
        self._write_table_styles(root)

        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def _write_number_formats(self, root: ET.Element):
        """Add <numFmts> element if there are custom number formats."""
        if not self._parent._numfmts:
            return
        num_fmts = ET.SubElement(root, 'numFmts', {'count': str(len(self._parent._numfmts))})
        for nf in self._parent._numfmts:
            ET.SubElement(num_fmts, 'numFmt', {
                'numFmtId': str(nf.id),
                'formatCode': nf.format_code
            })
    
    def _write_fonts(self, root: ET.Element):
        """Add <fonts> element."""
        fonts_elem = ET.SubElement(root, 'fonts', {'count': str(len(self._parent._fonts))})
        for font in self._parent._fonts:
            font_elem = ET.SubElement(fonts_elem, 'font')
            # Name
            ET.SubElement(font_elem, 'name', {'val': font.name})
            # Size
            ET.SubElement(font_elem, 'sz', {'val': str(font.size or '')})
            # Bold
            if font.bold:
                ET.SubElement(font_elem, 'b')
            # Italic
            if font.italic:
                ET.SubElement(font_elem, 'i')
            # Underline
            if font.underline.value != 'none':
                ET.SubElement(font_elem, 'u', {'val': font.underline.value})
            # Strikethrough
            if font.strike:
                ET.SubElement(font_elem, 'strike')
            # Color
            if font.color:
                n_color = self._normalize_color(font.color)
                if n_color:
                    color_attr = {'rgb': n_color}
                    ET.SubElement(font_elem, 'color', color_attr)
            # Charset / Family / Scheme (optional)
            if font.charset is not None:
                ET.SubElement(font_elem, 'charset', {'val': str(font.charset)})
            if font.family is not None:
                ET.SubElement(font_elem, 'family', {'val': str(font.family)})
            if font.scheme:
                ET.SubElement(font_elem, 'scheme', {'val': font.scheme or ''})

    def _write_fills(self, root: ET.Element):
        """Add <fills> element."""
        fills_elem = ET.SubElement(root, 'fills', {'count': str(len(self._parent._fills))})
        for fill in self._parent._fills:
            fill_elem = ET.SubElement(fills_elem, 'fill')
            if fill.pattern:
                pattern = ET.SubElement(fill_elem, 'patternFill', {'patternType': fill.pattern.pattern_type.value})
                if fill.pattern.fg_color:
                    n_color = self._normalize_color(fill.pattern.fg_color)
                    if n_color:
                        ET.SubElement(pattern, 'fgColor', {'rgb': n_color} )
                if fill.pattern.bg_color:
                    n_color = self._normalize_color(fill.pattern.bg_color)
                    if n_color:
                        ET.SubElement(pattern, 'bgColor', {'rgb': n_color})
            elif fill.gradient:
                grad = ET.SubElement(fill_elem, 'gradientFill')
                if fill.gradient.degree is not None:
                    grad.set('degree', str(fill.gradient.degree))
                for stop in fill.gradient.stops:
                    stop_elem = ET.SubElement(grad, 'stop', {'position': str(stop.position)})
                    n_color = self._normalize_color(stop.color)
                    if n_color:
                        ET.SubElement(stop_elem, 'color', {'rgb': n_color})

    def _write_borders(self, root: ET.Element):
        """Add <borders> element."""
        borders_elem = ET.SubElement(root, 'borders', {'count': str(len(self._parent._borders))})
        for border in self._parent._borders:
            border_elem = ET.SubElement(borders_elem, 'border')
            for side_name in ('left', 'right', 'top', 'bottom', 'diagonal'):
                side = getattr(border, side_name)
                if side.style.value != 'none':
                    attrs = {'style': side.style.value}
                    if side.color:
                        n_color = self._normalize_color(side.color)
                        if n_color:
                            attrs['color'] = n_color
                    ET.SubElement(border_elem, side_name, attrs)
            # Diagonal up/down flags
            if border.diagonal_up:
                border_elem.set('diagonalUp', '1')
            if border.diagonal_down:
                border_elem.set('diagonalDown', '1')

    def _write_cell_style_xfs(self, root: ET.Element):
        """
        Add <cellStyleXfs> element.
        Usually contains a single default format (numFmtId=0, fontId=0, fillId=0, borderId=0).
        """
        # Excel requires at least one cell style XF
        cell_style_xfs = ET.SubElement(root, 'cellStyleXfs', {'count': '1'})
        xf = ET.SubElement(cell_style_xfs, 'xf', {
            'numFmtId': '0',
            'fontId': '0',
            'fillId': '0',
            'borderId': '0',
            'xfId': '0'
        })
        # Optionally, if we have custom cell styles, we could add more

    def _write_cell_xfs(self, root: ET.Element):
        """Add <cellXfs> element for all registered cell formats."""
        cell_xfs = ET.SubElement(root, 'cellXfs', {'count': str(len(self._parent._cell_formats))})
        for xf in self._parent._cell_formats:
            attrs = {
                'numFmtId': str(xf.number_format_id or 0),
                'fontId': str(xf.font_id or 0),
                'fillId': str(xf.fill_id or 0),
                'borderId': str(xf.border_id or 0),
                'xfId': '0'  # refers to cellStyleXfs index (0)
            }
            if xf.alignment:
                attrs['applyAlignment'] = '1'
            if xf.protection:
                attrs['applyProtection'] = '1'
            xf_elem = ET.SubElement(cell_xfs, 'xf', attrs)
            if xf.alignment:
                align_attrs = {
                    'horizontal': xf.alignment.horizontal.value,
                    'vertical': xf.alignment.vertical.value,
                    'wrapText': '1' if xf.alignment.wrap_text else '0',
                    'shrinkToFit': '1' if xf.alignment.shrink_to_fit else '0',
                    'indent': str(xf.alignment.indent),
                    'textRotation': str(xf.alignment.text_rotation)
                }
                ET.SubElement(xf_elem, 'alignment', align_attrs)
            if xf.protection:
                ET.SubElement(xf_elem, 'protection', {
                    'locked': '1' if xf.protection.locked else '0',
                    'hidden': '1' if xf.protection.hidden else '0'
                })

    def _write_cell_styles(self, root: ET.Element):
        """
        Add <cellStyles> element if there are named cell styles.
        """
        if not hasattr(self._parent, '_cell_styles') or not self._parent._cell_styles:
            return
        cell_styles = ET.SubElement(root, 'cellStyles', {'count': str(len(self._parent._cell_styles))})
        for cs in self._parent._cell_styles:
            attrs = {
                'name': cs.name,
                'xfId': str(cs.xf_id),
                'builtinId': str(cs.builtin_id) if cs.builtin_id is not None else '0'
            }
            ET.SubElement(cell_styles, 'cellStyle', attrs)

    def _write_differential_formats(self, root: ET.Element):
        """
        Add <dxfs> element for differential formatting (used by conditional formatting).
        """
        if not hasattr(self._parent, '_dxfs') or not self._parent._dxfs:
            # Excel requires at least an empty dxfs element when used
            # Usually we add an empty one if any conditional formatting exists.
            # For simplicity, we add an empty <dxfs> count="0" if no dxfs.
            ET.SubElement(root, 'dxfs', {'count': '0'})
            return
        dxfs = ET.SubElement(root, 'dxfs', {'count': str(len(self._parent._dxfs))})
        for dxf in self._parent._dxfs:
            dxf_elem = ET.SubElement(dxfs, 'dxf')
            # Write font, fill, border, alignment, numberFormat if present
            if dxf.font:
                font_elem = ET.SubElement(dxf_elem, 'font')
                if dxf.font.bold:
                    ET.SubElement(font_elem, 'b')
                if dxf.font.italic:
                    ET.SubElement(font_elem, 'i')
                if dxf.font.color:
                    n_color = self._normalize_color(dxf.font.color)
                    if n_color:
                        ET.SubElement(font_elem, 'color', {'rgb': n_color})
            if dxf.fill:
                fill_elem = ET.SubElement(dxf_elem, 'fill')
                if dxf.fill.pattern:
                    pattern = ET.SubElement(fill_elem, 'patternFill', {'patternType': dxf.fill.pattern.pattern_type.value})
                    if dxf.fill.pattern.fg_color:
                        n_color = self._normalize_color(dxf.fill.pattern.fg_color)
                        if n_color:
                            ET.SubElement(pattern, 'fgColor', {'rgb': n_color})
            if dxf.border:
                border_elem = ET.SubElement(dxf_elem, 'border')
                # Simplified border writing
            if dxf.alignment:
                align = dxf.alignment
                align_attrs = {
                    'horizontal': align.horizontal.value,
                    'vertical': align.vertical.value,
                    'wrapText': '1' if align.wrap_text else '0'
                }
                ET.SubElement(dxf_elem, 'alignment', align_attrs)
            if dxf.number_format:
                ET.SubElement(dxf_elem, 'numFmt', {'numFmtId': str(dxf.number_format.id), 'formatCode': dxf.number_format.format_code})

    def _write_table_styles(self, root: ET.Element):
        """
        Add <tableStyles> element (required by Excel).
        """
        # Minimal tableStyles element
        ET.SubElement(root, 'tableStyles', {
            'count': '0',
            'defaultTableStyle': 'TableStyleMedium9',
            'defaultPivotStyle': 'PivotStyleLight16'
        })

    def _normalize_color(self, color: Optional[str]) -> Optional[str]:
        """Convert color to RRGGBB (no leading #) or None."""
        if color is None:
            return None
        color = color.lstrip('#').upper()
        if len(color) == 3:
            color = ''.join([c*2 for c in color])
        return color if len(color) == 6 else None