# engines/document/parsers/drawingml/chart_ref_parser.py
"""
Extracts chart references from DrawingML graphic frames and resolves
them into complete ChartContent objects.
Shared between XLSX and PPTX parsers.
"""

from __future__ import annotations
from xml.etree.ElementTree import Element
from typing import Optional, Dict, Callable, Union
from zipfile import ZipFile

from ...models.usdm_models import ChartContent

# We reuse the comprehensive chart XML parser from the XLSX module.
# If the spreadsheet parser is not available, a fallback can be implemented.
try:
    from ..spreadsheet_parser.xlsx.charts_builder import (
        parse_chart as _parse_chart_xml,
    )
except ImportError:
    _parse_chart_xml = None

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def parse_chart_ref(graphic_frame: Element) -> Optional[ChartContent]:
    """
    Parse a <a:graphicFrame> (or similar) element and extract the chart reference.

    Args:
        graphic_frame: XML element that contains a chart reference.

    Returns:
        ChartContent with chart_type="unknown" and _chart_rId set, or None if no chart.
    """
    graphic = graphic_frame.find("a:graphic", NS)
    if graphic is None:
        return None

    graphic_data = graphic.find("a:graphicData", NS)
    if graphic_data is None:
        return None

    chart_elem = graphic_data.find("c:chart", NS)
    if chart_elem is None:
        return None

    r_id = chart_elem.get(f"{{{NS['r']}}}id")
    if not r_id:
        return None

    chart = ChartContent(chart_type="unknown")
    chart._chart_rId = r_id
    return chart


def resolve_chart(
    r_id: str,
    drawing_rels: Dict[str, str],
    zip_file: ZipFile,
    relationship_target_resolver: Optional[Callable[[str, str], Optional[str]]] = None,
) -> Optional[ChartContent]:
    """
    Resolve a chart relationship ID to a fully parsed ChartContent.

    Args:
        r_id: The relationship ID (e.g., "rId2").
        drawing_rels: Dictionary mapping rel IDs to target paths (from the drawing's .rels).
        zip_file: The open ZIP archive containing the chart XML part.
        relationship_target_resolver: Optional callable(base_path, target) -> full path inside ZIP.
                                       If None, assumes the target is already a full path like "charts/chart1.xml".

    Returns:
        Fully populated ChartContent, or None if parsing fails.
    """
    if r_id not in drawing_rels:
        return None

    target = drawing_rels[r_id]
    # chart parts are usually in "charts/..." relative to the drawing or doc root
    # We need to convert to an absolute path inside the ZIP
    if relationship_target_resolver:
        chart_path = relationship_target_resolver("", target)
    else:
        # Assume target is a direct path inside the ZIP (e.g., "xl/charts/chart1.xml")
        chart_path = target if not target.startswith("..") else None

    if not chart_path:
        return None

    try:
        chart_xml_bytes = zip_file.read(chart_path)
        chart_xml = Element.fromstring(chart_xml_bytes)
        if _parse_chart_xml is not None:
            return _parse_chart_xml(chart_xml)
        else:
            # Minimal fallback if spreadsheet parser unavailable
            return ChartContent(chart_type="unknown")
    except Exception:
        return None