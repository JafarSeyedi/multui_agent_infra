# engines/document/parsers/pptx_parser/comments_parser.py
"""
Parses a PPTX comments XML part into a list of SlideComment objects.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.psdm_models import SlideComment
from .constants import NAMESPACES

NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": NAMESPACES["a"],
}

def parse_comments(comments_xml: Element) -> list[SlideComment]:
    """Parse a <p:cmLst> element (from comments.xml) and return a list of comments."""
    comments: list[SlideComment] = []
    for cm_elem in comments_xml.findall("p:cm", NS):
        comment_id = cm_elem.get("cmId", "")
        author = cm_elem.get("author", "")
        date = cm_elem.get("dt", "")  # ISO date
        # text from <p:text>
        text_elem = cm_elem.find("p:text", NS)
        text = text_elem.text if text_elem is not None and text_elem.text else ""
        # position (optional)
        pos = cm_elem.find("p:pos", NS)
        x = float(pos.get("x", "0")) if pos is not None else None
        y = float(pos.get("y", "0")) if pos is not None else None

        comments.append(SlideComment(
            comment_id=comment_id,
            author=author,
            date=date if date else None,
            text=text,
            position_x=x,
            position_y=y,
        ))
    return comments
