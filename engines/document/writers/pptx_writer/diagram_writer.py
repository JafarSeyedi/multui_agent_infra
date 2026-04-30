# engines/document/writers/pptx_writer/diagram_writer.py
"""
Write a diagram XML part from a DrawingContent that holds a structured
SmartArt tree in its vector_data (JSON).  No raw XML needed.
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from xml.etree.ElementTree import Element, SubElement, tostring
import json

from ...models.usdm_models import DrawingContent

# DrawingML namespaces
DGM = "http://schemas.openxmlformats.org/drawingml/2006/diagram"
A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
R   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

NSMAP = {"dgm": DGM, "a": A, "r": R}


def write_diagram(drawing: DrawingContent) -> bytes:
    """
    Generate the complete diagram XML (e.g., ppt/diagrams/data1.xml)
    from a DrawingContent whose vector_data is a JSON‑serialised tree.

    Expected JSON format (mirrors the parser output):
    {
        "type": "hierarchy",          // layout name
        "root": {                     // root node
            "id": "0",
            "text": "Root",
            "children": [ ... ]
        }
    }
    """
    # 1. Try to parse the structured tree from vector_data
    try:
        data = json.loads(drawing.vector_data) if drawing.vector_data else {}
    except json.JSONDecodeError:
        data = {}

    root_node = data.get("root")
    layout_name = data.get("type", "hierarchy")

    # 2. Build the data model XML
    dgm_elem = Element(f"{{{DGM}}}dataModel")

    # ---- point list (ptLst) ----
    pt_lst = SubElement(dgm_elem, f"{{{DGM}}}ptLst")
    _build_point_list(pt_lst, root_node, node_id_map := {})

    # ---- connection list (cxnLst) ----
    if root_node:
        cxn_lst = SubElement(dgm_elem, f"{{{DGM}}}cxnLst")
        _build_connections(cxn_lst, root_node, node_id_map)

    # 3. Return pretty-printed XML bytes
    return tostring(dgm_elem, xml_declaration=True, encoding="UTF-8")


def _build_point_list(parent: Element, node: Optional[dict], id_map: Dict[str, str]) -> None:
    """Recursively create <dgm:pt> elements and populate id_map."""
    if node is None:
        return

    model_id = node.get("id", "0")
    # Ensure unique model IDs (prefix with "n" if needed)
    unique_id = f"n{model_id}"
    id_map[model_id] = unique_id

    pt = SubElement(parent, f"{{{DGM}}}pt", {"modelId": unique_id})
    # Shape properties (optional) – we use a minimal rectangle
    sp_pr = SubElement(pt, f"{{{A}}}spPr")
    SubElement(sp_pr, f"{{{A}}}prstGeom", {"prst": "rect"})

    # Text
    text = node.get("text", "")
    if text:
        tx_body = SubElement(pt, f"{{{A}}}txBody")
        SubElement(tx_body, f"{{{A}}}bodyPr")
        p = SubElement(tx_body, f"{{{A}}}p")
        r = SubElement(p, f"{{{A}}}r")
        SubElement(r, f"{{{A}}}t").text = text

    # Children
    for child in node.get("children", []):
        _build_point_list(parent, child, id_map)


def _build_connections(parent: Element, node: Optional[dict], id_map: Dict[str, str]) -> None:
    """Create <dgm:cxn> elements for parent→child relationships."""
    if node is None:
        return
    src_unique = id_map.get(node.get("id"))
    if src_unique is None:
        return
    for child in node.get("children", []):
        dst_unique = id_map.get(child.get("id"))
        if dst_unique:
            cxn = SubElement(parent, f"{{{DGM}}}cxn", {
                "srcId": src_unique,
                "destId": dst_unique,
            })
        _build_connections(parent, child, id_map)