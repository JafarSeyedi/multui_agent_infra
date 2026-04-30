# engines/document/parsers/spreadsheet_parser/xlsx/worksheet_builder.py
"""
Builds a complete ESDM Worksheet from a worksheet's XML.
Handles:
- Rows and cells, all data types, formulas, rich text, style references
- Column definitions
- Merged cells
- AutoFilter
- Conditional formatting
- Hyperlinks
- Data validations
- Comments (legacy and threaded)
- Tables (via references to external table XML, passed in)
- Shapes (drawings)
- Page setup and margins
- Sheet properties and protection
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any, Tuple
from xml.etree.ElementTree import Element

from ....models.esdm_models import (
    Worksheet, Row, Cell, Column, MergedCellRange,
    SharedStrings, SpreadsheetStyleSheet,
    AutoFilter, ConditionalFormatting,
    Hyperlink, DataValidation, DataValidationRule,
    DataValidationType, DataValidationOperator,
    Comment, CommentText, CommentTextRun, Author, CommentCollection,
    ThreadedComment,
    SheetProperties, SheetProtection, PageSetup, PageMargins, SheetDimensions, Orientation,
    ShapeContent,
    Table,   # already built by tables_builder
)
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_int, xml_float, xml_bool,
    parse_cell_coordinate, parse_range, color_hex_from_xml,
)
from .namespaces import MAIN, REL
from .tables_builder import build_auto_filter, build_conditional_formatting, build_table
from .formulas_builder import build_cell_formula, build_shared_formulas
from .constants import (
    DATA_VALIDATION_TYPE_MAP, DATA_VALIDATION_OPERATOR_MAP,
    PAGE_ORIENTATION_MAP,
)

NS = {"": MAIN, "r": REL}

def build_worksheet(
    sheet_name: str,
    sheet_xml: Element,
    shared_strings: SharedStrings,
    stylesheet: SpreadsheetStyleSheet,
    comments_xml: Optional[Element] = None,
    threaded_comments_xml: Optional[Element] = None,
    table_xmls: Optional[List[Element]] = None,
    drawing_xml: Optional[Element] = None,
    image_map: Optional[Dict[str, str]] = None,
    chart_map: Dict[str, Element] = None
) -> Worksheet:
    ws = Worksheet(name=sheet_name)  # name set later by caller

    # Sheet properties
    ws.properties = _build_sheet_properties(sheet_xml)

    # Page setup and margins
    ws.page_setup = _build_page_setup(sheet_xml)
    ws.margins = _build_page_margins(sheet_xml)

    # Protection
    ws.protection = _build_sheet_protection(sheet_xml)

    # Column info
    _build_columns(sheet_xml, ws)

    # Merge cells
    _build_merges(sheet_xml, ws)

    # AutoFilter (sheet-level, overridden by table auto filter if present)
    af_elem = xml_find(sheet_xml, "autoFilter", NS)
    if af_elem is not None:
        ws.auto_filter = build_auto_filter(af_elem)

    # Conditional formatting
    ws.conditional_formattings = build_conditional_formatting(sheet_xml)

    # Hyperlinks
    ws.hyperlinks = _build_hyperlinks(sheet_xml)

    # Data validations
    ws.data_validations = _build_data_validations(sheet_xml)

    # Rows and cells
    _build_rows(sheet_xml, ws, shared_strings, stylesheet)

    # Shared formulas (post-process)
    # ws.shared_formulas = build_shared_formulas(sheet_xml)  # optional

    # Tables (from separate XML parts)
    if table_xmls:
        for tbl_xml in table_xmls:
            table = build_table(tbl_xml)
            ws.tables.append(table)

    # Comments (legacy)
    if comments_xml is not None:
        ws.comments = _build_comments(comments_xml)

    # Threaded comments
    if threaded_comments_xml is not None:
        ws.threaded_comments = _build_threaded_comments(threaded_comments_xml)

    # Shapes (drawing)
    if drawing_xml is not None:
        shapes, images, charts = parse_drawing(drawing_xml)
        ws.shapes = shapes
        ws.floating_images = images
        # Resolve image src to actual file path inside ZIP
        if image_map:
            for img in ws.floating_images:
                if img.src in image_map:
                    img.src = image_map[img.src]  # now it's the ZIP path, e.g., "xl/media/image1.png"
        ws.floating_charts = charts
        for chart in ws.floating_charts:
            r_id = getattr(chart, '_chart_rId', None)
            if r_id and r_id in chart_map:
                real_chart = chart_map[r_id]
                # Copy all fields from real_chart into the placeholder
                chart.chart_type = real_chart.chart_type
                chart.grouping = real_chart.grouping
                chart.direction = real_chart.direction
                chart.title = real_chart.title
                chart.series = real_chart.series
                chart.category_axis = real_chart.category_axis
                chart.value_axis = real_chart.value_axis
                # Remove temporary attribute
                delattr(chart, '_chart_rId')

    # Dimensions
    _update_dimensions(ws)

    return ws


# ──────────────────────────────────────────
# Internal helper functions
# ──────────────────────────────────────────

def _build_sheet_properties(sheet_xml: Element) -> SheetProperties:
    sp = xml_find(sheet_xml, "sheetPr", NS)
    props = SheetProperties()
    if sp is not None:
        props.tab_color = color_hex_from_xml(xml_find(sp, "tabColor", NS), NS)
        props.filter_mode = xml_bool(sp, "filterMode")
        props.published = xml_bool(sp, "published", True)
        # showGridlines is in sheetViews -> sheetView
        views = xml_find(sheet_xml, "sheetViews", NS)
        if views is not None:
            sv = xml_find(views, "sheetView", NS)
            if sv is not None:
                props.show_gridlines = xml_bool(sv, "showGridLines", True)
    return props


def _build_page_setup(sheet_xml: Element) -> PageSetup:
    ps_elem = xml_find(sheet_xml, "pageSetup", NS)
    ps = PageSetup()
    if ps_elem is not None:
        orient = xml_attr(ps_elem, "orientation", "portrait")
        ps.orientation = PAGE_ORIENTATION_MAP.get(orient, Orientation.PORTRAIT)
        ps.scale = xml_int(ps_elem, "scale", 100)
        ps.paper_size = xml_int(ps_elem, "paperSize", 9)
        ps.fit_to_width = xml_int(ps_elem, "fitToWidth", None) or None
        ps.fit_to_height = xml_int(ps_elem, "fitToHeight", None) or None
    return ps


def _build_page_margins(sheet_xml: Element) -> PageMargins:
    pm_elem = xml_find(sheet_xml, "pageMargins", NS)
    margins = PageMargins()
    if pm_elem is not None:
        margins.left = xml_float(pm_elem, "left", 0.7)
        margins.right = xml_float(pm_elem, "right", 0.7)
        margins.top = xml_float(pm_elem, "top", 0.75)
        margins.bottom = xml_float(pm_elem, "bottom", 0.75)
        margins.header = xml_float(pm_elem, "header", 0.3)
        margins.footer = xml_float(pm_elem, "footer", 0.3)
    return margins


def _build_sheet_protection(sheet_xml: Element) -> SheetProtection:
    prot_elem = xml_find(sheet_xml, "sheetProtection", NS)
    prot = SheetProtection()
    if prot_elem is not None:
        prot.sheet = xml_bool(prot_elem, "sheet", True)
        prot.objects = xml_bool(prot_elem, "objects")
        prot.scenarios = xml_bool(prot_elem, "scenarios")
        # For the rest, we use defaults which are True when protection is absent.
        prot.format_cells = not xml_bool(prot_elem, "formatCells")
        prot.format_columns = not xml_bool(prot_elem, "formatColumns")
        prot.format_rows = not xml_bool(prot_elem, "formatRows")
        prot.insert_columns = not xml_bool(prot_elem, "insertColumns")
        prot.insert_rows = not xml_bool(prot_elem, "insertRows")
        prot.insert_hyperlinks = not xml_bool(prot_elem, "insertHyperlinks")
        prot.delete_columns = not xml_bool(prot_elem, "deleteColumns")
        prot.delete_rows = not xml_bool(prot_elem, "deleteRows")
        prot.select_locked_cells = xml_bool(prot_elem, "selectLockedCells", True)
        prot.select_unlocked_cells = xml_bool(prot_elem, "selectUnlockedCells", True)
    return prot


def _build_columns(sheet_xml: Element, ws: Worksheet) -> None:
    cols_elem = xml_find(sheet_xml, "cols", NS)
    if cols_elem is None:
        return
    for col_el in xml_findall(cols_elem, "col", NS):
        idx = xml_int(col_el, "min")
        width = xml_float(col_el, "width", None)
        hidden = xml_bool(col_el, "hidden")
        style = xml_int(col_el, "style", None) or None
        # The col element can span min..max, we handle only min for simplicity,
        # but a full implementation would iterate.
        ws.columns[idx] = Column(index=idx, width=width, hidden=hidden, style_id=style)
        # If max > min, duplicate for all indices.
        max_idx = xml_int(col_el, "max", idx)
        for ci in range(idx+1, max_idx+1):
            ws.columns[ci] = Column(index=ci, width=width, hidden=hidden, style_id=style)


def _build_merges(sheet_xml: Element, ws: Worksheet) -> None:
    merges_elem = xml_find(sheet_xml, "mergeCells", NS)
    if merges_elem is None:
        return
    for mc in xml_findall(merges_elem, "mergeCell", NS):
        ref = xml_attr(mc, "ref", "")
        if ref:
            min_r, min_c, max_r, max_c = parse_range(ref)
            ws.merged_cells.append(MergedCellRange(min_row=min_r, max_row=max_r,
                                                   min_col=min_c, max_col=max_c))


def _build_hyperlinks(sheet_xml: Element) -> List[Hyperlink]:
    links = []
    hls = xml_find(sheet_xml, "hyperlinks", NS)
    if hls is None:
        return links
    for hl in xml_findall(hls, "hyperlink", NS):
        links.append(Hyperlink(
            ref=xml_attr(hl, "ref", ""),
            target=xml_attr(hl, "r:id", ""),  # relationship id
            tooltip=xml_attr(hl, "tooltip"),
            display=xml_attr(hl, "display"),
        ))
    return links


def _build_data_validations(sheet_xml: Element) -> List[DataValidation]:
    dvs = []
    dv_elem = xml_find(sheet_xml, "dataValidations", NS)
    if dv_elem is None:
        return dvs
    for dv in xml_findall(dv_elem, "dataValidation", NS):
        type_str = xml_attr(dv, "type", "custom")
        dv_type = DATA_VALIDATION_TYPE_MAP.get(type_str, DataValidationType.CUSTOM)
        op_str = xml_attr(dv, "operator")
        dv_op = DATA_VALIDATION_OPERATOR_MAP.get(op_str) if op_str else None
        rule = DataValidationRule(
            type=dv_type,
            operator=dv_op,
            allow_blank=xml_bool(dv, "allowBlank", False),
            show_input_message=xml_bool(dv, "showInputMessage", False),
            show_error_message=xml_bool(dv, "showErrorMessage", True),
            error_title=xml_attr(dv, "errorTitle"),
            error_message=xml_attr(dv, "error"),
            prompt_title=xml_attr(dv, "promptTitle"),
            prompt_message=xml_attr(dv, "prompt"),
            formula1=xml_attr(dv, "formula1"),
            formula2=xml_attr(dv, "formula2"),
        )
        dvs.append(DataValidation(
            ref=xml_attr(dv, "sqref", ""),
            rule=rule,
        ))
    return dvs


def _build_rows(sheet_xml: Element, ws: Worksheet, ss: SharedStrings,
                stylesheet: SpreadsheetStyleSheet) -> None:
    sheet_data = xml_find(sheet_xml, "sheetData", NS)
    if sheet_data is None:
        return
    for row_el in xml_findall(sheet_data, "row", NS):
        row_idx = xml_int(row_el, "r")
        row = Row(index=row_idx)
        row.height = xml_float(row_el, "ht", None) or None
        row.hidden = xml_bool(row_el, "hidden")
        row.style_id = xml_int(row_el, "s", None) or None
        # customHeight?

        for c_el in xml_findall(row_el, "c", NS):
            col_idx = parse_cell_coordinate(xml_attr(c_el, "r"))[1]
            cell = Cell(row=row_idx, col=col_idx)

            # Style index
            style_idx = xml_int(c_el, "s", None)
            if style_idx is not None:
                cell.style_id = style_idx

            # Cell type
            t = xml_attr(c_el, "t", "n")  # default numeric

            # Value extraction
            v_el = xml_find(c_el, "v", NS)
            f_el = xml_find(c_el, "f", NS)

            # Formula
            if f_el is not None:
                formula_text = xml_text(f_el)
                shared_index = xml_int(f_el, "si", None) or None
                array = xml_bool(f_el, "t", False) and xml_attr(f_el, "t") == "array"
                cell.formula = build_cell_formula(formula_text, shared_index, array)

            # Value according to type
            if t == "s":  # shared string
                if v_el is not None:
                    idx = int(xml_text(v_el))
                    if 0 <= idx < len(ss.strings):
                        cell.value = ss.strings[idx]
                if ss.get("rich_text_map"):
                    cell.rich_text = ss.rich_text_map.get(idx)
                        
            elif t == "b":  # boolean
                if v_el is not None:
                    cell.value = xml_text(v_el) == "1"
            elif t == "e":  # error
                cell.value = xml_text(v_el)  # keep as string like "#VALUE!"
            elif t == "n":  # number
                if v_el is not None:
                    cell.value = float(xml_text(v_el)) if '.' in xml_text(v_el) else int(xml_text(v_el))
            elif t == "str":  # formula string
                cell.value = xml_text(f_el) if f_el is not None else xml_text(v_el)
            elif t == "inlineStr":  # inline string
                is_elem = xml_find(c_el, "is", NS)
                if is_elem is not None:
                    t_elem = xml_find(is_elem, "t", NS)
                    if t_elem is not None:
                        cell.value = xml_text(t_elem)
                    else:
                        # rich text inline
                        parts = [xml_text(rt_t) for rt_t in xml_findall(is_elem, "r/t", NS)]
                        cell.value = "".join(parts)
            else:
                # default to v
                if v_el is not None:
                    cell.value = xml_text(v_el)

            # Hyperlink (inline) - we handle separately via hyperlinks list
            # Comment (legacy) – references comments via relationships, handled separately.

            # Add to row
            row.cells[col_idx] = cell

        ws.rows[row_idx] = row


def _build_comments(comments_xml: Element) -> CommentCollection:
    coll = CommentCollection()
    # Authors
    authors_list = xml_find(comments_xml, "authors", NS)
    if authors_list is not None:
        for a in xml_findall(authors_list, "author", NS):
            coll.authors.append(Author(name=xml_text(a)))

    # Comments
    comment_list = xml_find(comments_xml, "commentList", NS)
    if comment_list is not None:
        for cmt in xml_findall(comment_list, "comment", NS):
            ref = xml_attr(cmt, "ref", "")
            author_id = xml_int(cmt, "authorId", 0)
            text = _parse_comment_text(xml_find(cmt, "text", NS))
            coll.comments.append(Comment(ref=ref, author_id=author_id, text=text))
    return coll


def _parse_comment_text(text_elem: Element) -> CommentText:
    ct = CommentText()
    if text_elem is None:
        return ct
    for r in xml_findall(text_elem, "r", NS):
        run = CommentTextRun(text="")
        t_el = xml_find(r, "t", NS)
        if t_el is not None:
            run.text = xml_text(t_el)
        rpr = xml_find(r, "rPr", NS)
        if rpr is not None:
            run.bold = xml_find(rpr, "b", NS) is not None
            run.italic = xml_find(rpr, "i", NS) is not None
            run.underline = xml_find(rpr, "u", NS) is not None
            col = xml_find(rpr, "color", NS)
            run.color = color_hex_from_xml(col, NS) if col is not None else None
        ct.runs.append(run)
    # If no runs, maybe plain text
    if not ct.runs:
        plain = xml_text(text_elem)
        if plain:
            ct.runs.append(CommentTextRun(text=plain))
    return ct


def _build_threaded_comments(tc_xml: Element) -> List[ThreadedComment]:
    tcs = []
    for tc in xml_findall(tc_xml, "threadedComment", NS):
        ref = xml_attr(tc, "ref", "")
        text = xml_text(xml_find(tc, "text", NS))
        author = xml_attr(tc, "personId", "")  # would need person list
        date = xml_attr(tc, "dT", None)
        tcs.append(ThreadedComment(ref=ref, text=text, author=author, date=date))
    return tcs


def _update_dimensions(ws: Worksheet) -> None:
    """Compute sheet dimensions from rows and cols."""
    dim = SheetDimensions()
    if ws.rows:
        dim.min_row = min(ws.rows.keys())
        dim.max_row = max(ws.rows.keys())
    if ws.columns:
        dim.min_col = min(ws.columns.keys())
        dim.max_col = max(ws.columns.keys())
    # Also consider cells
    for row in ws.rows.values():
        if row.cells:
            min_col = min(row.cells.keys())
            max_col = max(row.cells.keys())
            if dim.min_col == 0 or min_col < dim.min_col:
                dim.min_col = min_col
            if dim.max_col == 0 or max_col > dim.max_col:
                dim.max_col = max_col
    ws.dimensions = dim