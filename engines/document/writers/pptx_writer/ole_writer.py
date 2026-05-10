# engines/document/writers/pptx_writer/ole_writer.py
"""
Writes OLE object relationships and binary files for round‑trip.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ...models.psdm_models import Slide
from ...models.usdm_models import OLEObjectContent
from .constants import NAMESPACES

P = f"{{{NAMESPACES['p']}}}"
R = f"{{{NAMESPACES['r']}}}"


def write_ole_element(ole: OLEObjectContent, r_id: str) -> Element:
    """Create <p:oleObj> element for an OLE object."""
    oleElem = Element(f"{P}oleObj", {
        "progId": ole.prog_id or "",
    })
    if ole.display_as_icon:
        oleElem.set("showAsIcon", "1")
    if r_id:
        oleElem.set(f"{R}id", r_id)
    return oleElem


def collect_ole_binaries(slides: list[Slide]) -> dict[str, bytes]:
    """
    Walk all slides and collect OLE binary data.
    Returns a dict mapping internal path (e.g., "ppt/embeddings/oleObject1.bin") → bytes.
    """
    binaries = {}
    for slide in slides:
        for elem in slide.elements:
            if elem.content and isinstance(elem.content, OLEObjectContent):
                ole = elem.content
                data = ole._meta.get("data")
                if data:
                    # Build a sensible path. The original path isn't stored,
                    # so we use a standard naming convention.
                    # We can use the relationship_id to generate a unique name.
                    rid = ole.relationship_id or "ole1"
                    path = f"ppt/embeddings/{rid}.bin"
                    binaries[path] = data
    return binaries
