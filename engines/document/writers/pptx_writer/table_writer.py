# engines/document/writers/pptx_writer/table_writer.py
"""
Write <p:tbl> from TableContent.
Full round‑trip: grid, row/cell properties, rich text with all formatting.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.usdm_models import ParagraphContent
from ...models.usdm_models import TableContent
from ..drawingml_helpers import write_rich_text_body
from .constants import NAMESPACES

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"


def write_table(table: TableContent) -> Element:
    """Generate <p:tbl> element with complete content."""
    tbl = Element(f"{P}tbl")

    # Table properties
    SubElement(tbl, f"{P}tblPr")
    # (additional tblPr like borders, shading would go here – not yet captured by parser)

    # Grid
    grid_cols = (table.metadata or {}).get("grid", [])
    if grid_cols:
        tblGrid = SubElement(tbl, f"{P}tblGrid")
        for width in grid_cols:
            SubElement(tblGrid, f"{P}gridCol", {"w": str(width)})

    # Rows
    for row in table.rows:
        tr = SubElement(tbl, f"{P}tr")
        trPr = SubElement(tr, f"{P}trPr")    # always create trPr (PPTX requires it when children exist)
        if row.is_header:
            SubElement(trPr, f"{A}header")
        height = (row.metadata or {}).get("height")
        if height is not None:
            SubElement(trPr, f"{A}h", {"val": str(height)})

        for cell in row.cells:
            tc = SubElement(tr, f"{P}tc")
            tcPr = SubElement(tc, f"{P}tcPr")
            if cell.col_span > 1:
                SubElement(tcPr, f"{A}gridSpan", {"val": str(cell.col_span)})
            vmerge = (cell.metadata or {}).get("vMerge")
            if vmerge:
                SubElement(tcPr, f"{A}vMerge", {"val": vmerge})
            if (cell.metadata or {}).get("hMerge"):
                SubElement(tcPr, f"{A}hMerge", {"val": "1"})

            # Cell content: must have exactly one <a:txBody>
            txBody = SubElement(tc, f"{A}txBody")
            SubElement(txBody, f"{A}bodyPr")
            if cell.content:
                # Write all paragraphs from the logical elements
                for elem in cell.content:
                    if isinstance(elem.content, ParagraphContent):
                        write_rich_text_body(txBody, elem.content.text)
                    # else: other content (images etc.) not yet supported in table cells;
                    # we skip to avoid corruption.
            else:
                # Empty cell – write one empty paragraph
                p = SubElement(txBody, f"{A}p")
                SubElement(p, f"{A}r")

    return tbl
