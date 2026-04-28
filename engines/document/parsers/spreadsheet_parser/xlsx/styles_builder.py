# engines/document/parsers/spreadsheet_parser/xlsx/styles_builder.py
"""
Parses xl/styles.xml into a complete SpreadsheetStyleSheet model.
Handles:
- Number formats (built-in and custom)
- Fonts
- Fills (pattern / gradient)
- Borders
- Cell formats (xf) – both cellStyleXfs and cellXfs
- Named cell styles
- Differential formatting (dxf)
- Table styles
"""

from xml.etree.ElementTree import Element
from typing import List, Dict, Optional, Sequence

from engines.document.models.esdm_models import (
    SpreadsheetStyleSheet,
    NumberFormatCollection,
    NumberFormat,
    FontCollection,
    Font,
    FontUnderline,
    FillCollection,
    Fill,
    PatternFill,
    PatternType,
    GradientFill,
    GradientStop,
    BorderCollection,
    Border,
    BorderSide,
    BorderStyle,
    CellFormatCollection,
    CellFormat,
    Alignment,
    HorizontalAlign,
    VerticalAlign,
    Protection,
    CellStyle,
    DifferentialFormat,
    ExcelTableStyle,
    TableStyleElement,
)

from .namespaces import MAIN
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_int, xml_float, xml_bool,
    color_hex_from_xml,
)
from .constants import (
    BUILTIN_NUMBER_FORMATS,
    OPENPYXL_UNDERLINE_TO_ESDM,
    OPENPYXL_FILL_PATTERN_TO_ESDM,
    OPENPYXL_BORDER_STYLE_TO_ESDM,
    OPENPYXL_HORIZONTAL_TO_ESDM,
    OPENPYXL_VERTICAL_TO_ESDM,
)

NS = {"": MAIN}

# ══════════════════════════════════════════════
# Public entry point
# ══════════════════════════════════════════════

def build_stylesheet(styles_xml: Element) -> SpreadsheetStyleSheet:
    """Convert the root <styleSheet> element into a full SpreadsheetStyleSheet."""
    ss = SpreadsheetStyleSheet()

    # 1. Number formats
    num_fmts = xml_find(styles_xml, "numFmts", NS)
    ss.number_formats = _build_number_formats(num_fmts)

    # 2. Fonts
    fonts_elem = xml_find(styles_xml, "fonts", NS)
    ss.excel_fonts = _build_fonts(fonts_elem)

    # 3. Fills
    fills_elem = xml_find(styles_xml, "fills", NS)
    ss.fills = _build_fills(fills_elem)

    # 4. Borders
    borders_elem = xml_find(styles_xml, "borders", NS)
    ss.borders = _build_borders(borders_elem)

    # 5. CellStyleXfs (format records for named styles) – we store them as CellFormat
    #    But we also need them to resolve cell style xfIds.
    cell_style_xfs = xml_find(styles_xml, "cellStyleXfs", NS)
    style_xf_records = _build_cell_formats(cell_style_xfs) if cell_style_xfs is not None else []

    # 6. CellXfs (format records for cells) – the main collection
    cell_xfs = xml_find(styles_xml, "cellXfs", NS)
    cell_xf_records = _build_cell_formats(cell_xfs) if cell_xfs is not None else []

    # Merge both into a single CellFormatCollection (keeping order)
    ss.cell_formats = CellFormatCollection()
    # We register all xf records: first from cellStyleXfs then cellXfs
    for xf in style_xf_records:
        ss.cell_formats.register(xf)
    cell_xf_offset = len(style_xf_records)
    for xf in cell_xf_records:
        ss.cell_formats.register(xf)

    # 7. Cell styles (named styles)
    cell_styles_elem = xml_find(styles_xml, "cellStyles", NS)
    ss.cell_styles = _build_cell_styles(cell_styles_elem, style_xf_records) if cell_styles_elem is not None else {}

    # 8. Differential formats
    dxfs_elem = xml_find(styles_xml, "dxfs", NS)
    ss.dxfs = _build_dxfs(dxfs_elem) if dxfs_elem is not None else []

    # 9. Table styles
    table_styles_elem = xml_find(styles_xml, "tableStyles", NS)
    ss.excel_table_styles = _build_table_styles(table_styles_elem) if table_styles_elem is not None else {}

    return ss


# ══════════════════════════════════════════════
# Internal builders
# ══════════════════════════════════════════════

def _build_number_formats(num_fmts: Optional[Element]) -> NumberFormatCollection:
    """Parse <numFmts> into NumberFormatCollection."""
    coll = NumberFormatCollection(builtin_formats=BUILTIN_NUMBER_FORMATS)
    if num_fmts is None:
        return coll
    for fmt_elem in xml_findall(num_fmts, "numFmt", NS):
        fmt_id = xml_int(fmt_elem, "numFmtId")
        code = xml_attr(fmt_elem, "formatCode", "")
        coll.custom_formats[fmt_id] = NumberFormat(id=fmt_id, format_code=code)
    return coll


def _build_fonts(fonts_elem: Optional[Element]) -> FontCollection:
    """Parse <fonts> into FontCollection (indexed list)."""
    coll = FontCollection()
    if fonts_elem is None:
        return coll
    for font_el in xml_findall(fonts_elem, "font", NS):
        font = Font()
        # Name
        name_el = xml_find(font_el, "name", NS)
        if name_el is not None:
            font.name = xml_attr(name_el, "val", font.name)
        # Size
        sz_el = xml_find(font_el, "sz", NS)
        if sz_el is not None:
            font.size = xml_float(sz_el, "val", font.size)
        # Bold
        b_el = xml_find(font_el, "b", NS)
        font.bold = b_el is not None and xml_bool(b_el, "val", True)
        # Italic
        i_el = xml_find(font_el, "i", NS)
        font.italic = i_el is not None and xml_bool(i_el, "val", True)
        # Underline
        u_el = xml_find(font_el, "u", NS)
        if u_el is not None:
            ul_val = xml_attr(u_el, "val")
            font.underline = OPENPYXL_UNDERLINE_TO_ESDM.get(ul_val, FontUnderline.NONE)
        # Strike
        strike_el = xml_find(font_el, "strike", NS)
        font.strike = strike_el is not None and xml_bool(strike_el, "val", True)
        # Color
        color_el = xml_find(font_el, "color", NS)
        font.color = color_hex_from_xml(color_el, NS) if color_el is not None else None
        # Charset, family, scheme (rarely used)
        charset_el = xml_find(font_el, "charset", NS)
        if charset_el is not None:
            font.charset = xml_int(charset_el, "val", None) or None
        family_el = xml_find(font_el, "family", NS)
        if family_el is not None:
            font.family = xml_int(family_el, "val", None) or None
        scheme_el = xml_find(font_el, "scheme", NS)
        if scheme_el is not None:
            font.scheme = xml_attr(scheme_el, "val")

        coll.register(font)
    return coll


def _build_fills(fills_elem: Optional[Element]) -> FillCollection:
    """Parse <fills> into FillCollection (indexed list)."""
    coll = FillCollection()
    if fills_elem is None:
        return coll
    for fill_el in xml_findall(fills_elem, "fill", NS):
        f = Fill()
        # Pattern fill
        pattern_el = xml_find(fill_el, "patternFill", NS)
        if pattern_el is not None:
            pt_str = xml_attr(pattern_el, "patternType")
            pt = OPENPYXL_FILL_PATTERN_TO_ESDM.get(pt_str, PatternType.NONE)
            fg_el = xml_find(pattern_el, "fgColor", NS)
            bg_el = xml_find(pattern_el, "bgColor", NS)
            f.pattern = PatternFill(
                pattern_type=pt,
                fg_color=color_hex_from_xml(fg_el, NS) if fg_el is not None else None,
                bg_color=color_hex_from_xml(bg_el, NS) if bg_el is not None else None,
            )
        # Gradient fill
        grad_el = xml_find(fill_el, "gradientFill", NS)
        if grad_el is not None:
            gradient = GradientFill(
                degree=xml_float(grad_el, "degree", None) or None,
                left=xml_float(grad_el, "left", None) or None,
                right=xml_float(grad_el, "right", None) or None,
                top=xml_float(grad_el, "top", None) or None,
                bottom=xml_float(grad_el, "bottom", None) or None,
            )
            for stop_el in xml_findall(grad_el, "stop", NS):
                pos = xml_float(stop_el, "position", 0.0)
                col_el = xml_find(stop_el, "color", NS)
                col = color_hex_from_xml(col_el, NS) if col_el is not None else ""
                gradient.stops.append(GradientStop(position=pos, color=col))
            f.gradient = gradient
        coll.register(f)
    return coll


def _build_borders(borders_elem: Optional[Element]) -> BorderCollection:
    """Parse <borders> into BorderCollection."""
    coll = BorderCollection()
    if borders_elem is None:
        return coll
    for border_el in xml_findall(borders_elem, "border", NS):
        b = Border()
        # Left, right, top, bottom, diagonal
        for side_tag, attr in [("left", "left"), ("right", "right"), ("top", "top"),
                               ("bottom", "bottom"), ("diagonal", "diagonal")]:
            side_el = xml_find(border_el, side_tag, NS)
            side = BorderSide()
            if side_el is not None:
                style_str = xml_attr(side_el, "style")
                side.style = OPENPYXL_BORDER_STYLE_TO_ESDM.get(style_str, BorderStyle.NONE)
                col_el = xml_find(side_el, "color", NS)
                side.color = color_hex_from_xml(col_el, NS) if col_el is not None else None
            setattr(b, attr, side)
        # Diagonal direction
        b.diagonal_up = xml_bool(border_el, "diagonalUp")
        b.diagonal_down = xml_bool(border_el, "diagonalDown")
        coll.register(b)
    return coll


def _build_cell_formats(xfs_elem: Element) -> List[CellFormat]:
    """Parse an <cellStyleXfs> or <cellXfs> element into a list of CellFormat."""
    formats: List[CellFormat] = []
    for xf_el in xml_findall(xfs_elem, "xf", NS):
        xf = CellFormat(
            number_format_id=xml_int(xf_el, "numFmtId", None) or None,
            font_id=xml_int(xf_el, "fontId", None) or None,
            fill_id=xml_int(xf_el, "fillId", None) or None,
            border_id=xml_int(xf_el, "borderId", None) or None,
        )
        # Alignment
        al_el = xml_find(xf_el, "alignment", NS)
        if al_el is not None:
            h = xml_attr(al_el, "horizontal", "general")
            v = xml_attr(al_el, "vertical", "bottom")
            xf.alignment = Alignment(
                horizontal=OPENPYXL_HORIZONTAL_TO_ESDM.get(h, HorizontalAlign.GENERAL),
                vertical=OPENPYXL_VERTICAL_TO_ESDM.get(v, VerticalAlign.BOTTOM),
                wrap_text=xml_bool(al_el, "wrapText"),
                shrink_to_fit=xml_bool(al_el, "shrinkToFit"),
                indent=xml_int(al_el, "indent", 0),
                text_rotation=xml_int(al_el, "textRotation", 0),
            )
        # Protection
        prot_el = xml_find(xf_el, "protection", NS)
        if prot_el is not None:
            xf.protection = Protection(
                locked=xml_bool(prot_el, "locked", True),
                hidden=xml_bool(prot_el, "hidden", False),
            )
        formats.append(xf)
    return formats


def _build_cell_styles(cell_styles_elem: Element,
                       style_xf_records: List[CellFormat]) -> Dict[str, CellStyle]:
    """Parse <cellStyles> linking to style xf records. Returns dict name -> CellStyle."""
    cell_styles: Dict[str, CellStyle] = {}
    for cs_el in xml_findall(cell_styles_elem, "cellStyle", NS):
        name = xml_attr(cs_el, "name", "")
        xf_id = xml_int(cs_el, "xfId")
        builtin_id = xml_int(cs_el, "builtinId", None) or None
        # The CellStyle extends USDM's CharacterStyle; we initialize with name.
        cell_styles[name] = CellStyle(
            name=name,
            builtin_id=builtin_id,
            xf_id=xf_id if xf_id < len(style_xf_records) else None,
        )
    return cell_styles


def _build_dxfs(dxfs_elem: Element) -> List[DifferentialFormat]:
    """Parse <dxfs> into list of DifferentialFormat."""
    dxfs: List[DifferentialFormat] = []
    for dxf_el in xml_findall(dxfs_elem, "dxf", NS):
        dxf = DifferentialFormat()
        # Font
        font_el = xml_find(dxf_el, "font", NS)
        if font_el is not None:
            fonts_coll = _build_fonts(font_el)  # reuse font builder (wrap single)
            if len(fonts_coll.fonts) > 0:
                dxf.font = fonts_coll.fonts[0]
        # Fill
        fill_el = xml_find(dxf_el, "fill", NS)
        if fill_el is not None:
            fills_coll = _build_fills(fill_el)
            if len(fills_coll.fills) > 0:
                dxf.fill = fills_coll.fills[0]
        # Border
        border_el = xml_find(dxf_el, "border", NS)
        if border_el is not None:
            borders_coll = _build_borders(border_el)
            if len(borders_coll.borders) > 0:
                dxf.border = borders_coll.borders[0]
        # Alignment
        al_el = xml_find(dxf_el, "alignment", NS)
        if al_el is not None:
            h = xml_attr(al_el, "horizontal", "general")
            v = xml_attr(al_el, "vertical", "bottom")
            dxf.alignment = Alignment(
                horizontal=OPENPYXL_HORIZONTAL_TO_ESDM.get(h, HorizontalAlign.GENERAL),
                vertical=OPENPYXL_VERTICAL_TO_ESDM.get(v, VerticalAlign.BOTTOM),
                wrap_text=xml_bool(al_el, "wrapText"),
                shrink_to_fit=xml_bool(al_el, "shrinkToFit"),
                indent=xml_int(al_el, "indent", 0),
                text_rotation=xml_int(al_el, "textRotation", 0),
            )
        # Number format
        numfmt_el = xml_find(dxf_el, "numFmt", NS)
        if numfmt_el is not None:
            fmt_id = xml_int(numfmt_el, "numFmtId")
            code = xml_attr(numfmt_el, "formatCode", "")
            dxf.number_format = NumberFormat(id=fmt_id, format_code=code)
        dxfs.append(dxf)
    return dxfs


def _build_table_styles(table_styles_elem: Optional[Element]) -> Dict[str, ExcelTableStyle]:
    """Parse <tableStyles> into dict name -> ExcelTableStyle."""
    table_styles: Dict[str, ExcelTableStyle] = {}
    if table_styles_elem is None:
        return table_styles
    # Default attributes
    default_name = xml_attr(table_styles_elem, "defaultTableStyle", "TableStyleMedium9")
    default_pivot = xml_attr(table_styles_elem, "defaultPivotStyle", "PivotStyleLight16")

    for ts_el in xml_findall(table_styles_elem, "tableStyle", NS):
        name = xml_attr(ts_el, "name", "")
        style = ExcelTableStyle(
            name=name,
            show_first_column=xml_bool(ts_el, "showFirstColumn"),
            show_last_column=xml_bool(ts_el, "showLastColumn"),
            show_row_stripes=xml_bool(ts_el, "showRowStripes", True),
            show_column_stripes=xml_bool(ts_el, "showColumnStripes"),
        )
        for elem_el in xml_findall(ts_el, "tableStyleElement", NS):
            type_ = xml_attr(elem_el, "type", "")
            dxf_id = xml_int(elem_el, "dxfId", None) or None
            size = xml_int(elem_el, "size", None) or None
            style.elements.append(TableStyleElement(type=type_, dxf_id=dxf_id, size=size))
        table_styles[name] = style
    return table_styles