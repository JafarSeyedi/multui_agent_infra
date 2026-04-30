# engines/document/parsers/docx_parser/docx_diagram_extractor.py
"""
Extracts a DOCXDiagram from a diagram XML part (dgm:dataModel).
Builds a full hierarchical tree of DiagramNode objects.
"""

from xml.etree.ElementTree import Element
from typing import Dict, List, Optional
from .docx_models import DOCXDiagram
from .docx_utils import safe_find, safe_findall, NS
from ..drawingml.diagram_parser import DiagramNode

# Namespace mapping for diagram
DGM = 'http://schemas.openxmlformats.org/drawingml/2006/diagram'
A   = NS.get('a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
R   = NS.get('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships')

NS_DGM = {'dgm': DGM, 'a': A, 'r': R}


def parse_diagram(diag_xml: Element) -> DOCXDiagram:
    """Parse a diagram XML and return a DOCXDiagram with tree."""
    diagram = DOCXDiagram()

    # Layout information (the layout type gives the diagram style)
    layout_node = safe_find(diag_xml, './/dgm:layoutNode', NS_DGM)
    if layout_node is not None:
        diagram.layout_type = layout_node.get('name')
        diagram.name = layout_node.get('name')
        desc = safe_find(layout_node, './/dgm:cNvPr', NS_DGM)
        if desc is not None:
            diagram.description = desc.get('descr')

    # Parse the data model (the actual content tree)
    data_model = safe_find(diag_xml, './/dgm:dataModel', NS_DGM)
    if data_model is not None:
        # Points and connections
        pts = safe_find(data_model, './/dgm:ptLst', NS_DGM)
        cnx = safe_find(data_model, './/dgm:cxnLst', NS_DGM)

        # Build a map of id -> DiagramNode
        node_map: Dict[str, DiagramNode] = {}
        if pts is not None:
            for pt in safe_findall(pts, './/dgm:pt', NS_DGM):
                model_id = pt.get('modelId')
                text = _extract_node_text(pt)
                shape_type, fill, line = _extract_node_shape(pt)
                node = DiagramNode(
                    id=model_id,
                    text=text,
                    shape_type=shape_type,
                    fill_color=fill,
                    line_color=line,
                )
                node_map[model_id] = node
                diagram.texts.append(text)

        # Build hierarchy from connections
        if cnx is not None:
            for cxn in safe_findall(cnx, './/dgm:cxn', NS_DGM):
                src_id = cxn.get('srcId')
                dst_id = cxn.get('destId')
                if src_id in node_map and dst_id in node_map:
                    node_map[src_id].children.append(node_map[dst_id])

        # Determine the root: a node that is not a destination of any connection
        all_dest = set()
        for node in node_map.values():
            for child in node.children:
                all_dest.add(child.id)
        for nid, node in node_map.items():
            if nid not in all_dest:
                diagram.root = node
                break
        # If no clear root, pick the first one from points
        if diagram.root is None and node_map:
            diagram.root = next(iter(node_map.values()))

    return diagram


def _extract_node_text(pt_elem: Element) -> str:
    """Get the visible text of a node from its <a:t> elements."""
    parts = []
    for t in safe_findall(pt_elem, './/a:t', NS_DGM):
        if t.text:
            parts.append(t.text)
    return ''.join(parts)


def _extract_node_shape(pt_elem: Element) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract shape type, fill, line from the node's spPr."""
    sp_pr = safe_find(pt_elem, './/a:spPr', NS_DGM)
    shape_type = None
    fill = None
    line = None
    if sp_pr is not None:
        # Preset geometry
        prst_geom = safe_find(sp_pr, './/a:prstGeom', NS_DGM)
        if prst_geom is not None:
            shape_type = prst_geom.get('prst')
        # Solid fill
        solid = safe_find(sp_pr, './/a:solidFill/a:srgbClr', NS_DGM)
        if solid is not None:
            fill = f"#{solid.get('val', '')}"
        # Line
        ln = safe_find(sp_pr, './/a:ln/a:solidFill/a:srgbClr', NS_DGM)
        if ln is not None:
            line = f"#{ln.get('val', '')}"
    return shape_type, fill, line