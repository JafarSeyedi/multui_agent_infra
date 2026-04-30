# engines/document/writers/pptx_writer/style_writer.py
"""
Write <p:txStyles> from a CharacterStyle (applied to title, body, other).
Every run property handled, including those stored in _meta for round‑trip.
"""

from __future__ import annotations
from xml.etree.ElementTree import Element, SubElement

from ...models.usdm_models import CharacterStyle
from .constants import NAMESPACES
from ..drawingml_helpers import set_solid_color

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"


def write_tx_styles(default_cs: CharacterStyle) -> Element:
    """
    Build <p:txStyles> containing titleStyle, bodyStyle, otherStyle.
    Each style gets nine levels, all with the same default run properties.
    """
    txStyles = Element(f"{P}txStyles")
    for style_name in ("titleStyle", "bodyStyle", "otherStyle"):
        style = SubElement(txStyles, f"{P}{style_name}")
        # Level 1‑9
        for lvl in range(1, 10):
            lvl_elem = SubElement(style, f"{A}lvl{lvl}pPr")
            defRPr = SubElement(lvl_elem, f"{A}defRPr")
            _write_defRPr(defRPr, default_cs)
    return txStyles


def _write_defRPr(defRPr: Element, cs: CharacterStyle) -> None:
    """
    Populate <a:defRPr> with **all** possible run properties.
    Missing optional fields are simply omitted.
    """
    # Bold / Italic
    if cs.bold:
        SubElement(defRPr, f"{A}b")
    if cs.italic:
        SubElement(defRPr, f"{A}i")

    # Underline
    if cs.underline:
        u = SubElement(defRPr, f"{A}u")
        if cs.underline_type:
            u.set("val", cs.underline_type)

    # Strike / Double strike
    if cs.strike:
        SubElement(defRPr, f"{A}strike")
    if cs.double_strike:
        SubElement(defRPr, f"{A}strike", {"val": "dblStrike"})

    # Superscript / Subscript
    if cs.superscript:
        SubElement(defRPr, f"{A}vertAlign", {"val": "superscript"})
    elif cs.subscript:
        SubElement(defRPr, f"{A}vertAlign", {"val": "subscript"})

    # Small caps / All caps
    if cs.small_caps:
        SubElement(defRPr, f"{A}smallCaps")
    if cs.all_caps:
        SubElement(defRPr, f"{A}caps")

    # Font name and fallback fonts
    if cs.font:
        latin = SubElement(defRPr, f"{A}latin", {"typeface": cs.font})
        if cs.font_family:
            latin.set("pitchFamily", str(cs.font_family))
    if cs.font_charset:
        # Apply to latin as well
        if defRPr.find(f"{A}latin") is not None:
            defRPr.find(f"{A}latin").set("charset", str(cs.font_charset))
    if cs.font_pitch:
        if defRPr.find(f"{A}latin") is not None:
            defRPr.find(f"{A}latin").set("pitch", str(cs.font_pitch))

    # Size (hundredths of a point)
    if cs.size is not None:
        SubElement(defRPr, f"{A}sz", {"val": str(int(cs.size * 100))})
    if cs.size_cs is not None:
        SubElement(defRPr, f"{A}szCs", {"val": str(int(cs.size_cs * 100))})

    # Color
    if cs.color:
        set_solid_color(defRPr, cs.color)

    # Highlight
    if cs.highlight:
        SubElement(defRPr, f"{A}highlight", {"val": cs.highlight})

    # Character spacing & position
    if cs.spacing is not None:
        SubElement(defRPr, f"{A}spc", {"val": str(int(cs.spacing))})
    if cs.position is not None:
        SubElement(defRPr, f"{A}position", {"val": str(int(cs.position))})
    if cs.kerning is not None:
        SubElement(defRPr, f"{A}kern", {"val": str(int(cs.kerning))})

    # Effects
    if cs.shadow:
        SubElement(defRPr, f"{A}shadow")
    if cs.outline:
        SubElement(defRPr, f"{A}outline")
    if cs.emboss:
        SubElement(defRPr, f"{A}emboss")
    if cs.imprint:
        SubElement(defRPr, f"{A}imprint")

    # Hidden & web hidden
    if cs.vanished:
        SubElement(defRPr, f"{A}vanish")
    if cs.web_hidden:
        SubElement(defRPr, f"{A}webHidden")

    # Language & proofing
    if cs.language:
        SubElement(defRPr, f"{A}lang", {"val": cs.language})
    if cs.no_proof:
        SubElement(defRPr, f"{A}noProof")

    # Apply any extra attributes stored during parsing (round‑trip preservation)
    extra = cs._meta.get("defRPr", {})
    for k, v in extra.items():
        # Skip keys already handled explicitly (avoid duplication or conflict)
        if k in (
            "val", "typeface", "name",
            "b", "i", "u", "strike", "sz", "szCs",
            "latin", "ea", "cs", "highlight", "spc", "position", "kern",
            "shadow", "outline", "emboss", "imprint", "vanish", "webHidden",
            "lang", "noProof",
        ):
            continue
        defRPr.set(k, str(v))