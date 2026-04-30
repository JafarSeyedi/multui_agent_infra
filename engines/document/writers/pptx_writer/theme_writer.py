# engines/document/writers/pptx_writer/theme_writer.py
"""
Write the complete theme1.xml from a Theme object.
All colour, font, format scheme data restored, including unknown children.
"""

from __future__ import annotations
from xml.etree.ElementTree import Element, SubElement

from ...models.psdm_models import Theme
from .constants import NAMESPACES
from ..drawingml_helpers import set_color, write_fill, write_line, write_effects
from .utils import dict_to_element

A = f"{{{NAMESPACES['a']}}}"


def write_theme(theme: Theme) -> Element:
    root = Element(f"{A}theme", {"name": theme.name or "Office Theme"})
    themeElements = SubElement(root, f"{A}themeElements")

    # ── Colour scheme ────────────────────────────────────────────
    if theme.color_scheme:
        clrScheme = SubElement(themeElements, f"{A}clrScheme", {
            "name": theme._meta.get("color_scheme_name", "Office")
        })
        for name, color_str in theme.color_scheme.items():
            elem = SubElement(clrScheme, f"{A}{name}")
            set_color(elem, color_str)

    # ── Font scheme ──────────────────────────────────────────────
    if theme.major_font or theme.minor_font:
        fontScheme = SubElement(themeElements, f"{A}fontScheme", {
            "name": theme._meta.get("font_scheme_name", "Office")
        })
        if theme.major_font:
            major = SubElement(fontScheme, f"{A}majorFont")
            SubElement(major, f"{A}latin", {"typeface": theme.major_font})
            for script in theme._meta.get("major_font_scripts", []):
                SubElement(major, f"{A}{script['tag']}", {"typeface": script['typeface']})
        if theme.minor_font:
            minor = SubElement(fontScheme, f"{A}minorFont")
            SubElement(minor, f"{A}latin", {"typeface": theme.minor_font})
            for script in theme._meta.get("minor_font_scripts", []):
                SubElement(minor, f"{A}{script['tag']}", {"typeface": script['typeface']})

    # ── Format scheme ─────────────────────────────────────────────
    fmt_data = theme._meta.get("format_scheme")
    if fmt_data:
        fmtScheme = SubElement(themeElements, f"{A}fmtScheme", {
            "name": theme._meta.get("format_scheme_name", "Office")
        })
        # Known lists – use specialised writers
        if "fill_styles" in fmt_data:
            fillLst = SubElement(fmtScheme, f"{A}fillStyleLst")
            for fill in fmt_data["fill_styles"]:
                write_fill(fillLst, fill)

        if "line_styles" in fmt_data:
            lnLst = SubElement(fmtScheme, f"{A}lnStyleLst")
            for line in fmt_data["line_styles"]:
                ln = SubElement(lnLst, f"{A}ln")
                write_line(ln, line)

        if "effect_styles" in fmt_data:
            effLst = SubElement(fmtScheme, f"{A}effectStyleLst")
            for ef in fmt_data["effect_styles"]:
                style = SubElement(effLst, f"{A}effectStyle")
                if "outer_shadow" in ef:
                    effectLst = SubElement(style, f"{A}effectLst")
                    outer = SubElement(effectLst, f"{A}outerShdw", {
                        "blurRad": str(ef["outer_shadow"].get("blur_rad", "0")),
                        "dist": str(ef["outer_shadow"].get("dist", "0")),
                        "dir": str(ef["outer_shadow"].get("dir", "0")),
                    })
                    if ef["outer_shadow"].get("color"):
                        set_color(outer, ef["outer_shadow"]["color"])

        if "bg_fill_styles" in fmt_data:
            bgLst = SubElement(fmtScheme, f"{A}bgFillStyleLst")
            for fill in fmt_data["bg_fill_styles"]:
                write_fill(bgLst, fill)

        # ── Opaque / unknown children (round‑trip safety) ─────────
        for key, value in fmt_data.items():
            if key in ("fill_styles", "line_styles", "effect_styles", "bg_fill_styles"):
                continue
            _write_unknown_child(fmtScheme, {key: value}, NAMESPACES)

    # ── Extra elements (extLst, etc.) ────────────────────────────
    extLst_data = theme._meta.get("extLst")
    if extLst_data:
        extLst = SubElement(root, f"{A}extLst")
        dict_to_element(extLst, extLst_data, NAMESPACES)

    return root


def _write_unknown_child(parent: Element, data: dict, ns: dict) -> None:
    """
    Write arbitrary children whose structure mirrors the dicts stored
    by the parser (tag name → dict of attributes/children).
    """
    for tag_name, child_data in data.items():
        if isinstance(child_data, dict):
            elem = SubElement(parent, f"{{{ns['a']}}}{tag_name}")
            dict_to_element(elem, child_data, ns)
        elif isinstance(child_data, list):
            for item in child_data:
                elem = SubElement(parent, f"{{{ns['a']}}}{tag_name}")
                if isinstance(item, dict):
                    dict_to_element(elem, item, ns)
                else:
                    elem.text = str(item)
        else:
            parent.set(tag_name, str(child_data))