# engines/document/parsers/pptx_parser/shape_parser.py
"""
PPTX shape parser.
Wraps the shared DrawingML shape parser and adds full PPTX‑specific details
to ensure round‑trip fidelity.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from xml.etree.ElementTree import Element

from engines.document.parsers.drawingml.shape_parser import parse_shape as parse_dml_shape
from engines.document.models.usdm_models import ShapeContent
from engines.document.models.psdm_models import Placeholder, PlaceholderType
from .constants import NAMESPACES, PPTX_PLACEHOLDER_MAP

NS = NAMESPACES


def parse_pptx_shape(sp_element: Element) -> ShapeContent:
    """
    Parse a <p:sp> (or <p:grpSp>, <p:pic>, <p:graphicFrame>) into a ShapeContent,
    preserving every detail for round‑trip.
    """
    shape = parse_dml_shape(sp_element, NS)

    # ----------- Non‑visual properties (nvSpPr) -----------
    nv_sp_pr = sp_element.find("p:nvSpPr", NS)
    if nv_sp_pr is not None:
        # cNvPr
        c_nv_pr = nv_sp_pr.find("p:cNvPr", NS)
        if c_nv_pr is not None:
            shape.name = c_nv_pr.get("name", shape.name)
            # Store all cNvPr attributes for round‑trip
            shape._meta["cNvPr"] = dict(c_nv_pr.attrib)
            # description (alt text)
            descr = c_nv_pr.get("descr")
            if descr:
                shape._meta["description"] = descr
            hlink = c_nv_pr.find("a:hlinkClick", NS)
            if hlink is not None:
                shape._meta["hyperlink"] = {
                    "r_id": hlink.get(f"{{{NS['r']}}}id"),
                    "action": hlink.get("action"),
                }

        # cNvSpPr (shape‑specific non‑visual)
        c_nv_sp_pr = nv_sp_pr.find("p:cNvSpPr", NS)
        if c_nv_sp_pr is not None:
            shape._meta["cNvSpPr"] = dict(c_nv_sp_pr.attrib)
            # txBox – indicates this is a text box
            tx_box = c_nv_sp_pr.get("txBox")
            if tx_box is not None:
                shape._meta["is_textbox"] = tx_box == "1"

        # nvPr – placeholder info
        nv_pr = nv_sp_pr.find("p:nvPr", NS)
        if nv_pr is not None:
            ph_elem = nv_pr.find("p:ph", NS)
            if ph_elem is not None:
                ph_type_str = ph_elem.get("type", "body")
                ph_idx = int(ph_elem.get("idx", "-1"))
                ph_type = PlaceholderType(PPTX_PLACEHOLDER_MAP.get(ph_type_str, "body"))
                placeholder = Placeholder(idx=ph_idx, type=ph_type, shape=shape)
                shape._meta["placeholder"] = placeholder
                shape._meta["placeholder_type"] = ph_type.value
                shape._meta["placeholder_idx"] = ph_idx
            # Keep a copy of entire nvPr attributes
            shape._meta["nvPr"] = dict(nv_pr.attrib)

    # ----------- Shape properties (spPr) extras -----------
    sp_pr = sp_element.find("p:spPr", NS)
    if sp_pr is not None:
        # Store any attributes not covered by the basic ones (e.g., bwMode)
        for key, val in sp_pr.attrib.items():
            if key not in ("xfrm", "prstGeom", "custGeom", "solidFill", "gradFill",
                           "pattFill", "noFill", "ln", "effectLst", "effectDag",
                           "sp3d", "scene3d"):
                shape._meta.setdefault("spPr_attrs", {})[key] = val
        # Check for media fill (video/audio)
        blip_fill = sp_pr.find("a:blipFill", NS)
        if blip_fill is not None:
            blip = blip_fill.find("a:blip", NS)
            if blip is not None:
                media_link = blip.get(f"{{{NS['r']}}}link")
                if media_link:
                    shape._meta["media_link_rId"] = media_link

    # ----------- Style reference (if any) -----------
    style_ref = sp_element.find("p:style", NS)
    if style_ref is not None:
        shape._meta["style_ref"] = dict(style_ref.attrib)
        # could be a reference to a quick style

    return shape

