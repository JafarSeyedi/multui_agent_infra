# engines/document/parsers/pptx_parser/table_parser.py
"""
Parses a <p:tbl> element (PPTX table) into a USDM TableContent.
Handles cell merging, text runs, and cell properties.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from xml.etree.ElementTree import Element

from ...models.usdm_models import (
    TableContent,
    TableRow,
    TableCell,
    LogicalElement,
    ElementType,
    ParagraphContent,
    RichTextContent,
    RichTextSpan,
)
from .constants import NAMESPACES

NS = NAMESPACES


def parse_table(tbl_elem: Element) -> TableContent:
    """
    Parse a <p:tbl> element into a TableContent model.
    """
    rows: List[TableRow] = []
    tr_elements = tbl_elem.findall("p:tr", NS)
    for tr_elem in tr_elements:
        row = parse_table_row(tr_elem)
        rows.append(row)

    # Table‑wide properties (like grid) can be stored in metadata
    tbl_pr = tbl_elem.find("p:tblPr", NS)
    metadata: Dict[str, Any] = {}
    if tbl_pr is not None:
        # store grid column widths if present
        tbl_grid = tbl_elem.find("p:tblGrid", NS)
        if tbl_grid is not None:
            cols = []
            for grid_col in tbl_grid.findall("p:gridCol", NS):
                width = int(grid_col.get("w", "0"))
                cols.append(width)
            if cols:
                metadata["grid"] = cols
    return TableContent(rows=rows, metadata=metadata)


def parse_table_row(tr_elem: Element) -> TableRow:
    cells: List[TableCell] = []
    for tc_elem in tr_elem.findall("p:tc", NS):
        cell = parse_table_cell(tc_elem)
        cells.append(cell)

    # Row properties
    tr_pr = tr_elem.find("p:trPr", NS)
    is_header = False
    metadata = {}
    if tr_pr is not None:
        # Check if row is header (presence of <a:header>)
        if tr_pr.find("a:header", NS) is not None:
            is_header = True
        # Height
        height_elem = tr_pr.find("a:h", NS)
        if height_elem is not None:
            metadata["height"] = int(height_elem.get("val", "0"))
    return TableRow(cells=cells, is_header=is_header, metadata=metadata)


def parse_table_cell(tc_elem: Element) -> TableCell:
    content: List[LogicalElement] = []
    tx_body = tc_elem.find("p:txBody", NS)
    if tx_body is not None:
        # Parse text paragraphs
        for p_elem in tx_body.findall("a:p", NS):
            para_content = parse_paragraph(p_elem)
            elem = LogicalElement(
                element_id=f"cell_para_{id(p_elem)}",
                element_type=ElementType.PARAGRAPH,
                content=para_content,
            )
            content.append(elem)

    # Cell properties
    tc_pr = tc_elem.find("p:tcPr", NS)
    row_span = 1
    col_span = 1
    is_header = False
    cell_metadata = {}
    if tc_pr is not None:
        # Grid span
        grid_span = tc_pr.find("a:gridSpan", NS)
        if grid_span is not None:
            col_span = int(grid_span.get("val", "1"))
        # Vertical merge
        v_merge = tc_pr.find("a:vMerge", NS)
        if v_merge is not None:
            val = v_merge.get("val", "continue")
            if val == "restart":
                # rowSpan cannot be known here; we store attribute
                cell_metadata["vMerge"] = "restart"
            else:
                cell_metadata["vMerge"] = "continue"
        # Horizontal merge
        h_merge = tc_pr.find("a:hMerge", NS)
        if h_merge is not None:
            cell_metadata["hMerge"] = "1"
        # Does it have a header style?
        # Not directly; we inherit from row.
        # Margin, border, shading can be stored similarly.
    return TableCell(
        content=content,
        row_span=row_span,
        col_span=col_span,
        is_header=is_header,  # will be overridden by row
        metadata=cell_metadata,
    )


def parse_paragraph(p_elem: Element) -> ParagraphContent:
    """Parse an <a:p> element into ParagraphContent with rich text."""
    spans: List[RichTextSpan] = []
    for r_elem in p_elem.findall("a:r", NS):
        t_elem = r_elem.find("a:t", NS)
        text = t_elem.text if t_elem is not None and t_elem.text is not None else ""
        
        span = RichTextSpan(text=text)
        r_pr = r_elem.find("a:rPr", NS)
        if r_pr is not None:
            # Use the pre‑existing style key
            style = r_pr.get("style")
            if style:
                span.character_style = style
        spans.append(span)

    # Combine spans into a single RichTextContent, preserving line breaks (each paragraph is a separate element)
    return ParagraphContent(text=RichTextContent(spans=spans))