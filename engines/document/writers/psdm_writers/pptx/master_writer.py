# engines/document/writers/pptx_writer/master_writer.py
"""
Write slide master and slide layout XML elements from SlideMaster and SlideLayout.
Complete round‑trip: all placeholders, backgrounds, text styles, and metadata.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ....models.psdm_models import HandoutMaster
from ....models.psdm_models import NotesMaster
from ....models.psdm_models import SlideLayout
from ....models.psdm_models import SlideMaster
from .constants import NAMESPACES
from ...usdm_writers.shared.drawingml_helpers import set_solid_color
from .shape_writer import write_shape
from .style_writer import write_tx_styles

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"
R = f"{{{NAMESPACES['r']}}}"


def write_master(master: SlideMaster) -> Element:
    """Generate a <p:sldMaster> element."""
    root = Element(f"{P}sldMaster")
    # Name and other attributes originally present
    for attr, val in master._meta.get("master_attrs", {}).items():
        root.set(attr, str(val))

    # Common slide data
    cSld = SubElement(root, f"{P}cSld")

    # Background
    if master.background_color or master.background_image:
        bg = SubElement(cSld, f"{P}bg")
        bgPr = SubElement(bg, f"{P}bgPr")
        if master.background_color:
            set_solid_color(bgPr, master.background_color)
        if master.background_image:
            blipFill = SubElement(bgPr, f"{A}blipFill")
            SubElement(blipFill, f"{A}blip", {f"{R}embed": master.background_image.src})
            stretch = SubElement(blipFill, f"{A}stretch")
            SubElement(stretch, f"{A}fillRect")

    # Shape tree – include placeholder shapes from the default layout?
    # Typically the master's spTree contains the master's own shapes (e.g., title, footer).
    # The parser stored those as placeholders in the master's primary layout.
    # We'll add all placeholders from the first layout (or all) as master shapes.
    if master.layouts:
        first_layout = next(iter(master.layouts.values()))
        spTree = SubElement(cSld, f"{P}spTree")
        for placeholder in first_layout.placeholders:
            shape_elem = write_shape(placeholder.shape, element_id=str(placeholder.idx) if placeholder.idx >= 0 else "1")
            spTree.append(shape_elem)

    # Text styles
    if master.default_text_style:
        txStyles = write_tx_styles(master.default_text_style)
        root.append(txStyles)

    # Extra metadata (like sldLayoutIdLst – the references to layouts)
    # The main writer will generate the layout list separately; we don't include them here.

    return root


def write_layout(layout: SlideLayout, master_name: str | None = None) -> Element:
    """Generate a <p:sldLayout> element."""
    root = Element(f"{P}sldLayout")
    # Layout name
    root.set("name", layout.name)
    # Any other stored attributes
    for attr, val in layout._meta.get("layout_attrs", {}).items():
        if attr != "name":   # already set
            root.set(attr, str(val))

    # Common slide data
    cSld = SubElement(root, f"{P}cSld")
    spTree = SubElement(cSld, f"{P}spTree")

    # Placeholders
    for placeholder in layout.placeholders:
        shape_elem = write_shape(placeholder.shape, element_id=str(placeholder.idx) if placeholder.idx >= 0 else "1")
        spTree.append(shape_elem)

    # If master_name is provided, we can add a reference, but it's not stored inside the layout XML (it's in relationship). So we skip.

    return root


def write_handout_master(handout_master: HandoutMaster) -> Element:
    """Generate a <p:handoutMaster> element."""
    root = Element(f"{P}handoutMaster")
    root.set("name", handout_master.name)

    for attr, val in handout_master._meta.get("handout_master_attrs", {}).items():
        if attr != "name":
            root.set(attr, str(val))

    # Common slide data
    cSld = SubElement(root, f"{P}cSld")
    SubElement(cSld, f"{P}spTree")

    # Background
    if handout_master.background_color or handout_master.background_image:
        bg = SubElement(cSld, f"{P}bg")
        bgPr = SubElement(bg, f"{P}bgPr")
        if handout_master.background_color:
            set_solid_color(bgPr, handout_master.background_color)
        if handout_master.background_image:
            blipFill = SubElement(bgPr, f"{A}blipFill")
            SubElement(blipFill, f"{A}blip", {f"{R}embed": handout_master.background_image.src})
            SubElement(blipFill, f"{A}stretch")

    # Text styles
    if handout_master.default_text_style:
        txStyles = write_tx_styles(handout_master.default_text_style)
        root.append(txStyles)

    return root


def write_notes_master(notes_master: NotesMaster) -> Element:
    """Generate a <p:notesMaster> element."""
    root = Element(f"{P}notesMaster")
    root.set("name", notes_master.name)

    for attr, val in notes_master._meta.get("notes_master_attrs", {}).items():
        if attr != "name":
            root.set(attr, str(val))

    # Common slide data
    cSld = SubElement(root, f"{P}cSld")
    SubElement(cSld, f"{P}spTree")

    # Background
    if notes_master.background_color or notes_master.background_image:
        bg = SubElement(cSld, f"{P}bg")
        bgPr = SubElement(bg, f"{P}bgPr")
        if notes_master.background_color:
            set_solid_color(bgPr, notes_master.background_color)
        if notes_master.background_image:
            blipFill = SubElement(bgPr, f"{A}blipFill")
            SubElement(blipFill, f"{A}blip", {f"{R}embed": notes_master.background_image.src})
            SubElement(blipFill, f"{A}stretch")

    # Text styles
    if notes_master.default_text_style:
        txStyles = write_tx_styles(notes_master.default_text_style)
        root.append(txStyles)

    return root
