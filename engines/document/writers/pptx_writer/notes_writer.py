# engines/document/writers/pptx_writer/notes_writer.py
"""
Write <p:notes> element from NotesSlide, reusing the shared rich‑text writer.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.psdm_models import NotesSlide
from ..drawingml_helpers import write_rich_text_body
from .constants import NAMESPACES

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"
R = f"{{{NAMESPACES['r']}}}"


def write_notes_slide(notes: NotesSlide, slide_rid: str | None = None) -> Element:
    """
    Build a <p:notes> element for a notes slide.

    Args:
        notes: The NotesSlide object.
        slide_rid: Relationship ID linking back to the slide (e.g., "rId1").

    Returns:
        <p:notes> root element.
    """
    root = Element(f"{P}notes")

    # Common slide data
    cSld = SubElement(root, f"{P}cSld")
    spTree = SubElement(cSld, f"{P}spTree")

    # Notes placeholder shape
    sp = SubElement(spTree, f"{P}sp")
    nvSpPr = SubElement(sp, f"{P}nvSpPr")
    SubElement(nvSpPr, f"{P}cNvPr", {"id": "1", "name": "Notes Placeholder"})
    SubElement(nvSpPr, f"{P}cNvSpPr")
    nvPr = SubElement(nvSpPr, f"{P}nvPr")
    SubElement(nvPr, f"{P}ph", {"type": "body", "idx": "1"})

    # Shape properties (inherited from master; minimal)
    spPr = SubElement(sp, f"{P}spPr")
    xfrm = SubElement(spPr, f"{A}xfrm")
    SubElement(xfrm, f"{A}off", {"x": "0", "y": "0"})
    SubElement(xfrm, f"{A}ext", {"cx": "0", "cy": "0"})

    # Text body with rich text
    txBody = SubElement(sp, f"{P}txBody")
    SubElement(txBody, f"{A}bodyPr")
    write_rich_text_body(txBody, notes.text)

    # Link back to the slide
    if slide_rid:
        SubElement(root, f"{P}slide", {f"{R}id": slide_rid})

    return root
