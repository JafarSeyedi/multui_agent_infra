# engines/document/parsers/pptx_parser/theme_parser.py
"""
Parses the PPTX theme (theme1.xml) into a Theme dataclass.
Captures the complete colour scheme, font scheme, format scheme,
and any additional theme properties for round‑trip.
"""

from __future__ import annotations
from typing import Dict, Optional, Any
from xml.etree.ElementTree import Element

from engines.document.models.psdm_models import Theme
from .constants import NAMESPACES

NS = NAMESPACES


def parse_theme(theme_xml: Element) -> Theme:
    """
    Parse <a:theme> and return a Theme with all possible detail.
    """
    theme = Theme()
    theme._meta = {}      # for anything not captured in dedicated fields

    # Theme name attribute
    theme.name = theme_xml.get("name")

    # ---------- Color Scheme ----------
    clr_scheme = theme_xml.find(".//a:clrScheme", NS)
    if clr_scheme is not None:
        scheme_name = clr_scheme.get("name")
        theme._meta["color_scheme_name"] = scheme_name
        color_map: Dict[str, str] = {}
        for elem in clr_scheme:
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            color_str = _extract_color_full(elem)
            if color_str:
                color_map[tag] = color_str
        theme.color_scheme = color_map

    # ---------- Font Scheme ----------
    font_scheme = theme_xml.find(".//a:fontScheme", NS)
    if font_scheme is not None:
        font_scheme_name = font_scheme.get("name")
        theme._meta["font_scheme_name"] = font_scheme_name
        major_el = font_scheme.find(".//a:majorFont", NS)
        minor_el = font_scheme.find(".//a:minorFont", NS)
        if major_el is not None:
            theme.major_font = _extract_font(major_el)
        if minor_el is not None:
            theme.minor_font = _extract_font(minor_el)

    # ---------- Format Scheme ----------
    fmt_scheme = theme_xml.find(".//a:fmtScheme", NS)
    if fmt_scheme is not None:
        fmt_name = fmt_scheme.get("name")
        theme._meta["format_scheme_name"] = fmt_name
        # We'll store the entire format scheme as a structured dict (no XML)
        theme._meta["format_scheme"] = _serialize_format_scheme(fmt_scheme)

    # ---------- Extra elements (e.g., extLst) ----------
    ext_lst = theme_xml.find(".//a:extLst", NS)
    if ext_lst is not None:
        theme._meta["extLst"] = _serialize_ext_list(ext_lst)

    return theme


def _extract_color_full(elem: Element) -> Optional[str]:
    """Convert any color element to a string preserving its type."""
    for child in elem:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "srgbClr":
            return f"#{child.get('val', '000000')}"
        if tag == "schemeClr":
            return f"scheme:{child.get('val', '')}"
        if tag == "sysClr":
            return f"sys:{child.get('lastClr', child.get('val', ''))}"
        if tag == "scrgbClr":
            r = child.get("r", "00")
            g = child.get("g", "00")
            b = child.get("b", "00")
            return f"#{r}{g}{b}"
        if tag == "prstClr":
            return f"preset:{child.get('val', '')}"
        if tag == "hslClr":
            hue = child.get("hue", "0")
            sat = child.get("sat", "0")
            lum = child.get("lum", "0")
            return f"hsl({hue},{sat},{lum})"
    return None


def _extract_font(elem: Element) -> str:
    latin = elem.find(".//a:latin", NS)
    if latin is not None:
        return latin.get("typeface", "")
    ea = elem.find(".//a:ea", NS)
    if ea is not None:
        return ea.get("typeface", "")
    cs = elem.find(".//a:cs", NS)
    if cs is not None:
        return cs.get("typeface", "")
    return ""


def _serialize_format_scheme(fmt_scheme: Element) -> Dict[str, Any]:
    """Convert <a:fmtScheme> children into a dict."""
    data = {}
    for child in fmt_scheme:
        tag = child.tag.split("}")[-1]
        if tag == "fillStyleLst":
            data["fill_styles"] = [_serialize_fill(f) for f in child]
        elif tag == "lnStyleLst":
            data["line_styles"] = [_serialize_line(l) for l in child]
        elif tag == "effectStyleLst":
            data["effect_styles"] = [_serialize_effect_style(e) for e in child]
        elif tag == "bgFillStyleLst":
            data["bg_fill_styles"] = [_serialize_fill(f) for f in child]
        else:
            # preserve other children as raw dict (attributes + text)
            data[tag] = _element_to_dict(child)
    return data


def _serialize_fill(elem: Element) -> Dict[str, Any]:
    # delegate to the shape parser's fill serialization
    from engines.document.parsers.drawingml.shape_parser import _parse_fill
    return _parse_fill(elem, NS)


def _serialize_line(elem: Element) -> Dict[str, Any]:
    from engines.document.parsers.drawingml.shape_parser import _parse_line
    return _parse_line(elem, NS)


def _serialize_effect_style(elem: Element) -> Dict[str, Any]:
    from engines.document.parsers.drawingml.shape_parser import _serialize_effect_list
    return _serialize_effect_list(elem.find("a:effectLst", NS) or elem, NS)


def _serialize_ext_list(ext_lst: Element) -> Dict[str, Any]:
    return _element_to_dict(ext_lst)


def _element_to_dict(el: Element) -> Dict[str, Any]:
    """Convert an XML element to a nested dict (attributes + children)."""
    d = dict(el.attrib)
    children = {}
    for child in el:
        tag = child.tag.split("}")[-1]
        if tag not in children:
            children[tag] = []
        children[tag].append(_element_to_dict(child))
    if children:
        d["_children"] = children
    if el.text and el.text.strip():
        d["_text"] = el.text.strip()
    return d