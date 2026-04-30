# engines/document/parsers/drawingml/shape_parser.py
"""
Complete DrawingML shape parser.
Handles <p:sp> (PPTX) and <xdr:sp> (XLSX) elements, producing a fully typed
ShapeContent with all visual properties captured for round‑trip fidelity.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from xml.etree.ElementTree import Element

from ...models.usdm_models import (
    ShapeContent,
    RichTextContent,
    RichTextSpan,
)

# ── Namespaces ──────────────────────────────────────────────────
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",
}


# ── Public entry point ───────────────────────────────────────────
def parse_shape(
    sp_element: Element,
    ns: Optional[Dict[str, str]] = None,
) -> ShapeContent:
    """
    Parse a <p:sp> or <xdr:sp> element into ShapeContent.

    Args:
        sp_element: The shape element (e.g., <p:sp>).
        ns: Optional custom namespace mapping; defaults to the built‑in NS.

    Returns:
        Fully populated ShapeContent.
    """
    ns = ns or NS

    # 1. Name (from cNvPr)
    nv_sp_pr = sp_element.find("p:nvSpPr", ns) or sp_element.find("xdr:nvSpPr", ns)
    name = ""
    if nv_sp_pr is not None:
        c_nv_pr = nv_sp_pr.find("p:cNvPr", ns) or nv_sp_pr.find("xdr:cNvPr", ns)
        if c_nv_pr is not None:
            name = c_nv_pr.get("name", "")

    # 2. Shape properties (spPr)
    sp_pr = sp_element.find("p:spPr", ns) or sp_element.find("xdr:spPr", ns)
    shape_type = "rect"
    x, y, cx, cy = 0, 0, 100, 100
    rotation = 0
    hidden = False
    fill_color = None
    line_color = None
    line_width = 12700
    meta: Dict[str, Any] = {}

    if sp_pr is not None:
        # Transform
        xfrm = sp_pr.find("a:xfrm", ns)
        if xfrm is not None:
            off = xfrm.find("a:off", ns)
            ext = xfrm.find("a:ext", ns)
            if off is not None:
                x = int(off.get("x", "0"))
                y = int(off.get("y", "0"))
            if ext is not None:
                cx = int(ext.get("cx", "0"))
                cy = int(ext.get("cy", "0"))
            rot = xfrm.get("rot")
            rotation = int(rot) // 60000 if rot else 0
            hidden = xfrm.get("hidden") == "1"

        # Preset geometry
        prst_geom = sp_pr.find("a:prstGeom", ns)
        if prst_geom is not None:
            shape_type = prst_geom.get("prst", "rect")

        # Fill
        fill_info = _parse_fill(sp_pr, ns)
        meta["fill"] = fill_info
        # Use solid fill color for the top‑level fill_color field
        fill_color = fill_info.get("solid_color")

        # Line
        ln = sp_pr.find("a:ln", ns)
        if ln is not None:
            line_info = _parse_line(ln, ns)
            meta["line"] = line_info
            line_color = line_info.get("solid_color")
            line_width = int(ln.get("w", "12700"))

        # Effect properties (shadow, etc.) – optional
        effect_lst = sp_pr.find("a:effectLst", ns)
        if effect_lst is not None:
            # We store the entire structured tree in meta for round‑trip
            meta["effects"] = _serialize_effect_list(effect_lst, ns)

        sp3d = _parse_sp3d(sp_pr, ns)
        meta["sp3d"] = sp3d

        scene3d = _parse_scene3d(sp_pr, ns)
        meta["scene3d"] = scene3d

    # 3. Text body (txBody)
    tx_body = sp_element.find("p:txBody", ns) or sp_element.find("xdr:txBody", ns)
    rich_text = _parse_text_body(tx_body, ns) if tx_body is not None else None

    shape = ShapeContent(
        shape_type=shape_type,
        x=x,
        y=y,
        width=cx,
        height=cy,
        name=name,
        text=rich_text,
        fill_color=fill_color,
        line_color=line_color,
        line_width=line_width,
        rotation=rotation,
        hidden=hidden,
    )
    # Attach extended metadata for round‑trip (no XML inside, only structured dicts)
    shape._meta = meta
    return shape


# ── Fill parsing ─────────────────────────────────────────────────
def _parse_fill(sp_pr: Element, ns: Dict[str, str]) -> Dict[str, Any]:
    """Parse fill properties (solid, gradient, pattern, noFill) and return a dict."""
    fill_info: Dict[str, Any] = {}

    # noFill
    if sp_pr.find("a:noFill", ns) is not None:
        fill_info["type"] = "none"
        return fill_info

    # Solid fill
    solid = sp_pr.find("a:solidFill", ns)
    if solid is not None:
        fill_info["type"] = "solid"
        color = _parse_color(solid, ns)
        fill_info["solid_color"] = color
        return fill_info

    # Gradient fill
    grad = sp_pr.find("a:gradFill", ns)
    if grad is not None:
        fill_info["type"] = "gradient"
        fill_info["degree"] = grad.get("degree")
        # Linear gradient path
        lin = grad.find("a:lin", ns)
        if lin is not None:
            fill_info["linear_angle"] = lin.get("ang")
        # Stops
        stops = []
        for stop_elem in grad.findall("a:gs", ns) + grad.findall("a:gsLst/a:gs", ns):
            pos = stop_elem.get("pos")
            color = _parse_color(stop_elem, ns)
            stops.append({"position": pos, "color": color})
        fill_info["stops"] = stops
        return fill_info

    # Pattern fill
    pat = sp_pr.find("a:pattFill", ns)
    if pat is not None:
        fill_info["type"] = "pattern"
        fill_info["pattern_type"] = pat.get("prst")
        fg = pat.find("a:fgClr", ns)
        bg = pat.find("a:bgClr", ns)
        if fg is not None:
            fill_info["fg_color"] = _parse_color(fg, ns)
        if bg is not None:
            fill_info["bg_color"] = _parse_color(bg, ns)
        return fill_info

    # Group fill (inherit)
    if sp_pr.find("a:grpFill", ns) is not None:
        fill_info["type"] = "group"
        return fill_info

    return fill_info


def _parse_color(parent: Element, ns: Dict[str, str]) -> Optional[str]:
    """Extract a color string from a container element (schemeClr, srgbClr, etc.)."""
    for color_type in ("a:srgbClr", "a:schemeClr", "a:sysClr", "a:scrgbClr", "a:prstClr", "a:hslClr"):
        elem = parent.find(color_type, ns)
        if elem is not None:
            val = elem.get("val")
            if val:
                # srgbClr → "#RRGGBB", schemeClr → "scheme:Dk1", etc.
                prefix = color_type.split(":")[1].replace("Clr", "")
                if prefix == "srgb":
                    return f"#{val}"
                elif prefix == "scheme":
                    return f"scheme:{val}"
                elif prefix == "sys":
                    return f"sys:{val}"
                else:
                    return f"{prefix}:{val}"
            # scrgbClr has r,g,b components
            if color_type == "a:scrgbClr":
                r = elem.get("r")
                g = elem.get("g")
                b = elem.get("b")
                return f"#{r}{g}{b}" if r and g and b else None
    return None


# ── Line parsing ─────────────────────────────────────────────────
def _parse_line(ln: Element, ns: Dict[str, str]) -> Dict[str, Any]:
    """Parse line properties and return a structured dict."""
    line_info: Dict[str, Any] = {}
    line_info["width"] = ln.get("w")

    # Cap, join, dash
    line_info["cap"] = ln.get("cap")
    line_info["cmpd"] = ln.get("cmpd")
    line_info["algn"] = ln.get("algn")

    # Dash type
    prst_dash = ln.find("a:prstDash", ns)
    if prst_dash is not None:
        line_info["dash_type"] = prst_dash.get("val")

    # Head/tail ends (arrows)
    head = ln.find("a:headEnd", ns)
    tail = ln.find("a:tailEnd", ns)
    if head is not None:
        line_info["head_end_type"] = head.get("type")
        line_info["head_end_w"] = head.get("w")
        line_info["head_end_len"] = head.get("len")
    if tail is not None:
        line_info["tail_end_type"] = tail.get("type")
        line_info["tail_end_w"] = tail.get("w")
        line_info["tail_end_len"] = tail.get("len")

    # Solid fill
    solid_fill = ln.find("a:solidFill", ns)
    if solid_fill is not None:
        line_info["solid_color"] = _parse_color(solid_fill, ns)

    # Gradient line (rare)
    grad_fill = ln.find("a:gradFill", ns)
    if grad_fill is not None:
        line_info["gradient"] = True  # simplified

    # No fill
    if ln.find("a:noFill", ns) is not None:
        line_info["solid_color"] = None

    return line_info


# ── Rich text parsing ────────────────────────────────────────────
def _parse_text_body(tx_body: Element, ns: Dict[str, str]) -> RichTextContent:
    """Parse <p:txBody> (or <xdr:txBody>) into RichTextContent."""
    spans: List[RichTextSpan] = []

    for p_elem in tx_body.findall("a:p", ns):
        # Paragraph properties (can be stored if needed)
        # p_pr = p_elem.find("a:pPr", ns)
        for r_elem in p_elem.findall("a:r", ns):
            t_elem = r_elem.find("a:t", ns)
            text = t_elem.text if t_elem is not None and t_elem.text else ""

            r_pr = r_elem.find("a:rPr", ns)
            span = RichTextSpan(text=text)
            if r_pr is not None:
                style = r_pr.get("style")
                if style:
                    span.character_style = style
                hl = r_pr.find("a:highlight/a:srgbClr", ns)
                if hl is not None:
                    span.background = f"#{hl.get('val', '')}"

                # Hyperlink
                hlink = r_pr.find("a:hlinkClick", ns)
                if hlink is not None:
                    span.href = hlink.get("r:id") if hlink.get("r:id") else hlink.get("id")

            spans.append(span)

        # Line break after paragraph (simulate with \n)
        if spans and not spans[-1].text.endswith("\n"):
            spans[-1].text += "\n"

    return RichTextContent(spans=spans)


# ── Effect list serialization ────────────────────────────────────
def _serialize_effect_list(effect_lst: Element, ns: Dict[str, str]) -> Dict[str, Any]:
    """Convert <a:effectLst> to a dict for round‑trip."""
    effects: Dict[str, Any] = {}
    # Outer shadow
    outer_shdw = effect_lst.find("a:outerShdw", ns)
    if outer_shdw is not None:
        effects["outer_shadow"] = {
            "blur_rad": outer_shdw.get("blurRad"),
            "dist": outer_shdw.get("dist"),
            "dir": outer_shdw.get("dir"),
            "color": _parse_color(outer_shdw, ns),
        }
    # Inner shadow, reflection, glow, etc. can be added similarly.
    return effects

def _parse_scene3d(sp_pr, ns):
    scene = sp_pr.find("a:scene3d", ns)
    if scene is not None:
        camera = scene.find("a:camera", ns)
        light_rig = scene.find("a:lightRig", ns)
        return {
            "camera": dict(camera.attrib) if camera is not None else None,
            "light_rig": dict(light_rig.attrib) if light_rig is not None else None,
        }
    return None

def _parse_sp3d(sp_pr, ns):
    sp3d = sp_pr.find("a:sp3d", ns)
    if sp3d is not None:
        bevel_t = sp3d.find("a:bevelT", ns)
        bevel_b = sp3d.find("a:bevelB", ns)
        return {
            "bevel_top": dict(bevel_t.attrib) if bevel_t else None,
            "bevel_bottom": dict(bevel_b.attrib) if bevel_b else None,
        }
    return None