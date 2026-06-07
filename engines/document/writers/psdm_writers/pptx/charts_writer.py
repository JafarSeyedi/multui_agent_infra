"""
Write chart XML (c:chart) from ChartContent.
This is a minimal stub; full implementation would need to produce proper DrawingML chart XML.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element, SubElement, tostring

from ....models.usdm_models import ChartContent

NS = {
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def write_chart_xml(chart: ChartContent) -> bytes:
    """
    Convert a ChartContent object into a chart XML part.

    Args:
        chart: ChartContent with all series, axes, title, etc.

    Returns:
        bytes of the XML document (utf-8 encoded).
    """
    root = Element(f"{{{NS['c']}}}chartSpace", {"xmlns:a": NS["a"], "xmlns:c": NS["c"]})
    # Add chart element
    chart_elem = SubElement(root, f"{{{NS['c']}}}chart")
    title_elem = SubElement(chart_elem, f"{{{NS['c']}}}title")
    tx_elem = SubElement(title_elem, f"{{{NS['c']}}}tx")
    rich = SubElement(tx_elem, f"{{{NS['a']}}}rich")
    bodyPr = SubElement(rich, f"{{{NS['a']}}}bodyPr")
    bodyPr.set("anchor", "ctr")
    p = SubElement(rich, f"{{{NS['a']}}}p")
    pPr = SubElement(p, f"{{{NS['a']}}}pPr")
    pPr.set("algn", "ctr")
    r = SubElement(p, f"{{{NS['a']}}}r")
    t = SubElement(r, f"{{{NS['a']}}}t")
    t.text = chart.title or "Chart"

    # Plot area
    plot_area = SubElement(chart_elem, f"{{{NS['c']}}}plotArea")
    # Series (simplified)
    for series in chart.series:
        ser_elem = SubElement(plot_area, f"{{{NS['c']}}}ser")
        idx_elem = SubElement(ser_elem, f"{{{NS['c']}}}idx")
        idx_elem.set("val", "0")
        order_elem = SubElement(ser_elem, f"{{{NS['c']}}}order")
        order_elem.set("val", "0")
        tx_elem2 = SubElement(ser_elem, f"{{{NS['c']}}}tx")
        rich2 = SubElement(tx_elem2, f"{{{NS['a']}}}rich")
        p2 = SubElement(rich2, f"{{{NS['a']}}}p")
        r2 = SubElement(p2, f"{{{NS['a']}}}r")
        t2 = SubElement(r2, f"{{{NS['a']}}}t")
        t2.text = series.name or "Series"
        # categories (simplified)
        cat_elem = SubElement(ser_elem, f"{{{NS['c']}}}cat")
        str_ref = SubElement(cat_elem, f"{{{NS['c']}}}strRef")
        f = SubElement(str_ref, f"{{{NS['c']}}}f")
        f.text = series.categories_ref or "Sheet1!$A$1:$A$10"
        # values (simplified)
        val_elem = SubElement(ser_elem, f"{{{NS['c']}}}val")
        num_ref = SubElement(val_elem, f"{{{NS['c']}}}numRef")
        f2 = SubElement(num_ref, f"{{{NS['c']}}}f")
        f2.text = series.values_ref or "Sheet1!$B$1:$B$10"

    # Legend (simplified)
    legend = SubElement(chart_elem, f"{{{NS['c']}}}legend")
    legend_pos = SubElement(legend, f"{{{NS['c']}}}legendPos")
    legend_pos.set("val", "r")

    return tostring(root, encoding="utf-8", xml_declaration=True)