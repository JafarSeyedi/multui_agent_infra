# engines/document/parsers/pptx_parser/master_parser.py
"""
Parses slide masters and slide layouts from PPTX XML.
Populates SlideMaster and SlideLayout with all necessary detail
for round‑trip fidelity.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.psdm_models import Placeholder
from ....models.psdm_models import PlaceholderType
from ....models.psdm_models import SlideLayout
from ....models.psdm_models import SlideMaster
from ....models.usdm_models import (
    CharacterStyle,
)
from .constants import NAMESPACES
from .shape_parser import parse_pptx_shape
from .utils import element_to_dict

NS = NAMESPACES


def parse_layout(layout_xml: Element) -> SlideLayout:
    """
    Parse a <p:sldLayout> element into a SlideLayout.

    Args:
        layout_xml: Root of a slide layout XML (e.g., slideLayout1.xml).

    Returns:
        SlideLayout with populated fields.
    """
    layout_attrs = dict(layout_xml.attrib)
    name = layout_attrs.get("name", "Untitled Layout")
    # The master name is not directly stored in the layout XML; it's resolved
    # via relationships by the caller. We just store it later.
    master_name = None

    layout = SlideLayout(
        name=name,
        master_name=master_name,
    )

    # ---------- Content (cSld) – extract placeholder shapes ----------
    cSld = layout_xml.find("p:cSld", NS)
    if cSld is not None:
        sp_tree = cSld.find("p:spTree", NS)
        if sp_tree is not None:
            for child in sp_tree:
                shape = parse_pptx_shape(child)  # reuses the full shape parser
                # Determine if it's a placeholder and what type
                ph_info = shape._meta.get("placeholder")
                if ph_info and isinstance(ph_info, Placeholder):
                    # Use the already parsed Placeholder
                    layout.placeholders.append(ph_info)
                else:
                    # Non‑placeholder shape on layout (e.g., decorative)
                    # We still record it as a generic shape without placeholder type
                    generic_ph = Placeholder(
                        idx=-1,
                        type=PlaceholderType.BODY,  # default
                        shape=shape,
                    )
                    layout.placeholders.append(generic_ph)

    # Extra metadata for round‑trip
    layout._meta = {
        "layout_attrs": layout_attrs,
    }
    return layout


def parse_master(
    master_xml: Element,
    layouts: dict[str, SlideLayout],
    master_name: str | None = None,
) -> SlideMaster:
    """
    Parse a <p:sldMaster> element into a SlideMaster.

    Args:
        master_xml: Root of a slide master XML (e.g., slideMaster1.xml).
        layouts: Dictionary mapping layout name → SlideLayout (pre‑parsed).
        master_name: Optional name for the master (from relationship or default).

    Returns:
        SlideMaster with populated layout dictionary and properties.
    """
    master_attrs = dict(master_xml.attrib)
    name = master_attrs.get("name", master_name or "Slide Master")

    master = SlideMaster(
        name=name,
        layouts=layouts,
    )

    # ---------- Background ----------
    bg = master_xml.find("p:cSld/p:bg", NS)
    if bg is not None:
        bg_pr = bg.find("p:bgPr", NS)
        if bg_pr is not None:
            # solid fill
            solid = bg_pr.find("a:solidFill", NS)
            if solid is not None:
                from ...drawingml.shape_parser import _parse_color
                master.background_color = _parse_color(solid, NS)
            # image fill
            blip_fill = bg_pr.find("a:blipFill", NS)
            if blip_fill is not None:
                # store as image content
                from ....models.usdm_models import ImageContent
                blip = blip_fill.find("a:blip", NS)
                if blip is not None:
                    embed = blip.get(f"{{{NS['r']}}}embed")
                    if embed:
                        master.background_image = ImageContent(src=embed)

    # ---------- Default text style ----------
    # Look for <p:txStyles> which defines title, body, other styles.
    tx_styles = master_xml.find("p:txStyles", NS)
    if tx_styles is not None:
        # Each child corresponds to a style type: title, body, other
        # We'll extract the first character style (simplified)
        for style_type in ("titleStyle", "bodyStyle", "otherStyle"):
            style_elem = tx_styles.find(f"p:{style_type}", NS)
            if style_elem is not None:
                # Each contains <a:lvl1pPr> to <a:lvl9pPr> for paragraph levels.
                # We'll capture the default run properties from the first level as CharacterStyle.
                lvl1 = style_elem.find("a:lvl1pPr", NS)
                if lvl1 is not None:
                    def_rpr = lvl1.find("a:defRPr", NS)
                    if def_rpr is not None:
                        cs = _parse_def_rpr(def_rpr)
                        master.default_text_style = cs
                        break  # Use the first available

    # ---------- Extra metadata for round‑trip ----------
    master._meta = {
        "master_attrs": master_attrs,
    }

    # Additional master content (e.g., sldLayoutIdLst) is handled by the main parser
    # via relationships; we don't need to store raw XML.
    return master


def _parse_def_rpr(def_rpr: Element) -> CharacterStyle:
    """Convert <a:defRPr> to a CharacterStyle."""
    cs = CharacterStyle(name="Default")
    cs.size = _get_font_size(def_rpr)
    cs.bold = def_rpr.find("a:b", NS) is not None
    cs.italic = def_rpr.find("a:i", NS) is not None
    u = def_rpr.find("a:u", NS)
    cs.underline = u is not None
    if u is not None:
        cs.underline_type = u.get("val")

    # Font family
    latin = def_rpr.find("a:latin", NS)
    if latin is not None:
        cs.font = latin.get("typeface")

    # Color
    solid = def_rpr.find("a:solidFill", NS)
    if solid is not None:
        from ...drawingml.shape_parser import _parse_color
        cs.color = _parse_color(solid, NS)

    # Other attributes
    cs.strike = def_rpr.find("a:strike", NS) is not None
    # Store the original element's attributes in metadata for round‑trip
    cs._meta = {"defRPr": element_to_dict(def_rpr)}
    return cs


def _get_font_size(def_rpr: Element) -> float | None:
    """Extract font size in points from <a:sz>."""
    sz = def_rpr.find("a:sz", NS)
    if sz is not None:
        val = int(sz.get("val", "0"))
        if val:
            return val / 100.0
    return None
