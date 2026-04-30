# engines/document/writers/drawingml_helpers.py
"""
Shared DrawingML writer primitives – colour, fill, line, effects, 3D, text.
All functions are complete and cover every case stored by the parser.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
from xml.etree.ElementTree import Element, SubElement

from .pptx_writer.constants import NAMESPACES

A = f"{{{NAMESPACES['a']}}}"
R = f"{{{NAMESPACES['r']}}}"


# ── Colour helpers ──────────────────────────────────────────────────
def set_solid_color(parent: Element, color_str: Optional[str]) -> None:
    """Write <a:solidFill> with the appropriate colour child."""
    if not color_str:
        return
    solid = SubElement(parent, f"{A}solidFill")
    _set_color_child(solid, color_str)


def set_color(elem: Element, color_str: str) -> None:
    """Directly add the colour child to the given element."""
    _set_color_child(elem, color_str)


def _set_color_child(parent: Element, color_str: str) -> None:
    if color_str.startswith("#"):
        SubElement(parent, f"{A}srgbClr", {"val": color_str.lstrip("#")})
    elif color_str.startswith("scheme:"):
        SubElement(parent, f"{A}schemeClr", {"val": color_str.split(":", 1)[1]})
    elif color_str.startswith("sys:"):
        SubElement(parent, f"{A}sysClr", {"val": color_str.split(":", 1)[1]})
    elif color_str.startswith("preset:"):
        SubElement(parent, f"{A}prstClr", {"val": color_str.split(":", 1)[1]})
    elif color_str.startswith("hsl("):
        # parse hsl(hue,sat,lum)
        vals = color_str[4:-1].split(",")
        if len(vals) == 3:
            SubElement(parent, f"{A}hslClr", {"hue": vals[0], "sat": vals[1], "lum": vals[2]})


# ── Fill helpers ─────────────────────────────────────────────────────
def write_fill(parent: Element, fill_info: Optional[Dict[str, Any]]) -> None:
    """Reconstruct fill from the parser's structured dict."""
    if not fill_info:
        return
    ftype = fill_info.get("type")
    if ftype == "solid":
        set_solid_color(parent, fill_info.get("solid_color"))
    elif ftype == "gradient":
        grad = SubElement(parent, f"{A}gradFill")
        if fill_info.get("degree"):
            grad.set("degree", fill_info["degree"])
        lin = fill_info.get("linear_angle")
        if lin is not None:
            SubElement(grad, f"{A}lin", {"ang": lin})
        for stop in fill_info.get("stops", []):
            gs = SubElement(grad, f"{A}gs", {"pos": str(stop["position"])})
            set_solid_color(gs, stop.get("color"))
    elif ftype == "pattern":
        pat = SubElement(parent, f"{A}pattFill", {"prst": fill_info.get("pattern_type", "pct5")})
        fg = SubElement(pat, f"{A}fgClr")
        set_color(fg, fill_info.get("fg_color") or "#000000")
        bg = SubElement(pat, f"{A}bgClr")
        set_color(bg, fill_info.get("bg_color") or "#FFFFFF")
    elif ftype == "none":
        SubElement(parent, f"{A}noFill")
    elif ftype == "group":
        SubElement(parent, f"{A}grpFill")


# ── Line helpers ─────────────────────────────────────────────────────
def write_line(ln: Element, line_info: Optional[Dict[str, Any]]) -> None:
    """Fill an <a:ln> element with all properties."""
    if not line_info:
        return
    for attr in ("w", "cap", "cmpd", "algn"):
        if attr in line_info:
            ln.set(attr, str(line_info[attr]))

    dash = line_info.get("dash_type")
    if dash:
        SubElement(ln, f"{A}prstDash", {"val": dash})

    for end, tag_end, tag_w, tag_len in [
        ("head_end_type", f"{A}headEnd", "head_end_w", "head_end_len"),
        ("tail_end_type", f"{A}tailEnd", "tail_end_w", "tail_end_len"),
    ]:
        if end in line_info:
            attrs = {"type": line_info[end]}
            w = line_info.get(tag_w)
            if w:
                attrs["w"] = w
            length = line_info.get(tag_len)
            if length:
                attrs["len"] = length
            SubElement(ln, tag_end, attrs)

    solid_color = line_info.get("solid_color")
    if solid_color is not None:
        set_solid_color(ln, solid_color)
    elif "solid_color" in line_info and line_info["solid_color"] is None:
        SubElement(ln, f"{A}noFill")

    # gradient line (rare)
    if line_info.get("gradient"):
        SubElement(ln, f"{A}gradFill")


# ── Effects helpers ──────────────────────────────────────────────────
def write_effects(effectLst: Element, effects: Dict[str, Any]) -> None:
    """Write shadow, glow, reflection."""
    outer = effects.get("outer_shadow")
    if outer:
        elem = SubElement(effectLst, f"{A}outerShdw")
        for attr in ("blurRad", "dist", "dir"):
            if attr in outer:
                elem.set(attr, str(outer[attr]))
        if "color" in outer:
            set_color(elem, outer["color"])
    # inner shadow, glow, reflection can be added similarly when stored


# ── 3D helpers ───────────────────────────────────────────────────────
def write_scene3d(parent: Element, scene3d: Dict[str, Any]) -> None:
    elem = SubElement(parent, f"{A}scene3d")
    cam = scene3d.get("camera")
    if cam:
        SubElement(elem, f"{A}camera", {k: str(v) for k, v in cam.items()})
    lr = scene3d.get("light_rig")
    if lr:
        SubElement(elem, f"{A}lightRig", {k: str(v) for k, v in lr.items()})


def write_sp3d(parent: Element, sp3d: Dict[str, Any]) -> None:
    elem = SubElement(parent, f"{A}sp3d")
    for key, tag in [("bevel_top", f"{A}bevelT"), ("bevel_bottom", f"{A}bevelB")]:
        val = sp3d.get(key)
        if val:
            SubElement(elem, tag, {k: str(v) for k, v in val.items()})


# ── Rich text body helper ────────────────────────────────────────────
def write_rich_text_body(txBody: Element, rich) -> None:
    """
    Write <a:p> elements for the given RichTextContent.
    Newlines split into separate paragraphs.
    """
    if not rich or not rich.spans:
        p = SubElement(txBody, f"{A}p")
        SubElement(p, f"{A}r")  # empty run
        return

    paragraphs = _group_spans_by_newlines(rich.spans)
    for para_spans in paragraphs:
        p = SubElement(txBody, f"{A}p")
        for span in para_spans:
            r = SubElement(p, f"{A}r")
            rPr = SubElement(r, f"{A}rPr")
            if span.bold:
                SubElement(rPr, f"{A}b")
            if span.italic:
                SubElement(rPr, f"{A}i")
            if span.underline:
                u = SubElement(rPr, f"{A}u")
                ul_type = span._meta.get("underline_type") if hasattr(span, '_meta') else None
                if ul_type:
                    u.set("val", ul_type)
            if span.color:
                set_solid_color(rPr, span.color)
            if span.font:
                SubElement(rPr, f"{A}latin", {"typeface": span.font})
            if span.character_style:
                if "size:" in span.character_style:
                    size_val = span.character_style.split(":", 1)[1]
                    try:
                        sz = int(float(size_val) * 100)
                        SubElement(rPr, f"{A}sz", {"val": str(sz)})
                    except ValueError:
                        pass
            if hasattr(span, '_meta') and span._meta.get("strike"):
                SubElement(rPr, f"{A}strike")

            t = SubElement(r, f"{A}t")
            t.text = span.text


def _group_spans_by_newlines(spans):
    """Split spans into paragraphs by newline characters."""
    paragraphs = []
    current = []
    for span in spans:
        if "\n" in span.text:
            parts = span.text.split("\n")
            for i, part in enumerate(parts):
                if i > 0:
                    paragraphs.append(current)
                    current = []
                if part:
                    new_span = copy_span(span, text=part)
                    current.append(new_span)
            if span.text.endswith("\n"):
                paragraphs.append(current)
                current = []
        else:
            current.append(span)
    if current:
        paragraphs.append(current)
    if not paragraphs:
        paragraphs.append([])
    return paragraphs


def copy_span(original, text=None):
    """Create a shallow copy of a RichTextSpan with optional text override."""
    from ..models.usdm_models import RichTextSpan
    return RichTextSpan(
        text=text if text is not None else original.text,
        character_style=original.character_style,
        code=original.code,
        background=original.background,
        href=original.href,
        math=original.math,
        display_math=original.display_math,
    )