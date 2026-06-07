# engines/document/writers/pptx_writer/relationship_utils.py
"""
Helpers for building and writing .rels files for the PPTX package.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
from xml.etree.ElementTree import tostring

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

def build_rels_element(
    relationships: list[tuple[str, str, str]],   # (rId, type, target)
) -> Element:
    """
    Build a <Relationships> element for a .rels file.

    Args:
        relationships: list of (rId, type, target) tuples.

    Returns:
        <Relationships xmlns="..."> Element
    """
    root = Element("Relationships", {"xmlns": REL_NS})
    for r_id, rtype, target in relationships:
        rel = SubElement(root, "Relationship")
        rel.set("Id", r_id)
        rel.set("Type", rtype)
        rel.set("Target", target)
    return root


def rels_to_xml(rels_element: Element) -> bytes:
    """Convert a <Relationships> Element to pretty‑printed XML bytes."""
    return tostring(rels_element, xml_declaration=True, encoding="UTF-8", method="xml")


def create_slide_rels(
    layout_rid: str | None = None,
    notes_rid: str | None = None,
    image_map: dict[str, str] | None = None,
    chart_map: dict[str, str] | None = None,
    media_map: dict[str, str] | None = None,
) -> Element:
    """
    Build relationships for a single slide.
    Automatically generates rIds for images, charts, media.

    Args:
        layout_rid: Relationship ID for the slide layout (if known, e.g., "rId1").
        notes_rid: Relationship ID for the notes slide (if present).
        image_map: dict mapping rId → image filename (e.g., "rId2"→"image1.png").
        chart_map: dict mapping rId → chart filename (e.g., "rId3"→"chart1.xml").
        media_map: dict mapping rId → media filename.

    Returns:
        <Relationships> element.
    """
    rels = []
    if layout_rid:
        rels.append((
            layout_rid,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout",
            "../slideLayouts/..."  # actual target resolved at write time
        ))
    if notes_rid:
        rels.append((
            notes_rid,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide",
            f"../notesSlides/notesSlide{notes_rid.replace('rId','')}.xml"
        ))

    def add_entries(mapping, rel_type_suffix):
        if mapping:
            for rid, target in mapping.items():
                rels.append((
                    rid,
                    f"http://schemas.openxmlformats.org/officeDocument/2006/relationships/{rel_type_suffix}",
                    target
                ))

    add_entries(image_map, "image")
    add_entries(chart_map, "chart")
    add_entries(media_map, "media")
    return build_rels_element(rels)
