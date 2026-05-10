# engines/document/parsers/drawingml/diagram_parser.py
"""
Parses diagram (SmartArt) reference from DrawingML and resolves the diagram XML.
Returns a DrawingContent with JSON tree.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Callable
from xml.etree.ElementTree import Element
from zipfile import ZipFile

from ...models.usdm_models import DrawingContent

# Shared namespaces
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "dgm": "http://schemas.openxmlformats.org/drawingml/2006/diagram",
}


def parse_diagram_ref(graphic_data: Element) -> DrawingContent | None:
    """
    Extract diagram reference from <a:graphicData> when URI is diagram.
    Returns a placeholder DrawingContent with _diagram_rId.
    """
    # Check URI
    uri = graphic_data.get("uri", "")
    if not uri.endswith("/diagram"):
        return None
    rel_ids = graphic_data.find("dgm:relIds", NS)
    if rel_ids is None:
        return None
    r_id = rel_ids.get(f"{{{NS['r']}}}id")
    if not r_id:
        return None
    content = DrawingContent(vector_data="")
    content._diagram_rId = r_id
    return content


def resolve_diagram(
    r_id: str,
    rels: dict[str, str],   # relationship id -> target
    zip_file: ZipFile,
    base_dir: str,
    rel_resolver: Callable[[str, str], str] | None = None,
) -> DrawingContent | None:
    """
    Resolve a diagram relationship ID to a fully parsed DrawingContent.
    """
    if r_id not in rels:
        return None
    target = rels[r_id]
    if rel_resolver:
        path = rel_resolver(base_dir, target)
    else:
        path = f"{base_dir}/{target}" if base_dir else target
    try:
        xml_bytes = zip_file.read(path)
        root = ET.fromstring(xml_bytes)
        return parse_diagram_xml(root)
    except Exception:
        return None


def parse_diagram_xml(diag_xml: Element) -> DrawingContent:
    """Convert diagram XML (dgm:dataModel) into DrawingContent with JSON tree."""
    layout_node = diag_xml.find(".//dgm:layoutNode", NS)
    name = layout_node.get("name") if layout_node is not None else None

    data_model = diag_xml.find(".//dgm:dataModel", NS)
    root_node = _build_node_tree(data_model) if data_model is not None else None

    tree_dict = {
        "type": name or "diagram",
        "root": _node_to_dict(root_node) if root_node else None,
    }
    vector_data = json.dumps(tree_dict, ensure_ascii=False)
    return DrawingContent(vector_data=vector_data)


# Helper classes
class DiagramNode:
    def __init__(self, model_id, text, children=None, shape_type=None, fill_color=None, line_color=None) -> None:
        self.id = model_id
        self.text = text
        self.children = children or []
        self.shape_type = shape_type
        self.fill_color = fill_color
        self.line_color = line_color


def _build_node_tree(data_model: Element) -> DiagramNode | None:
    pts = data_model.find(".//dgm:ptLst", NS)
    cnx = data_model.find(".//dgm:cxnLst", NS)
    if pts is None:
        return None
    node_map: dict[str, DiagramNode] = {}
    for pt in pts.findall("dgm:pt", NS):
        model_id = pt.get("modelId")
        if model_id is None:
            continue
        text = ""
        for t in pt.iter(f"{{{NS['a']}}}t"):
            if t.text:
                text += t.text
        node_map[model_id] = DiagramNode(model_id, text)
    if cnx is not None:
        for cxn in cnx.findall("dgm:cxn", NS):
            src = cxn.get("srcId")
            dst = cxn.get("destId")
            if src and dst and src in node_map and dst in node_map:
                node_map[src].children.append(node_map[dst])
    all_dest = set()
    for node in node_map.values():
        for child in node.children:
            all_dest.add(child.id)
    for nid, node in node_map.items():
        if nid not in all_dest:
            return node
    return next(iter(node_map.values())) if node_map else None


def _node_to_dict(node: DiagramNode) -> dict:
    return {
        "id": node.id,
        "text": node.text,
        "children": [_node_to_dict(c) for c in node.children] if node.children else []
    }