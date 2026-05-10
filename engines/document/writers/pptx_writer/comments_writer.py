# engines/document/writers/pptx_writer/comments_writer.py
"""
Write <p:cmLst> from SlideComment list.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.psdm_models import SlideComment
from .constants import NAMESPACES

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"


def write_comments(comments: list[SlideComment]) -> Element:
    cmLst = Element(f"{P}cmLst")
    for cm in comments:
        cmElem = SubElement(cmLst, f"{P}cm", {
            "cmId": str(cm.comment_id),
            "author": cm.author,
        })
        if cm.date:
            cmElem.set("dt", cm.date)
        if cm.position_x is not None and cm.position_y is not None:
            SubElement(cmElem, f"{P}pos", {"x": str(int(cm.position_x)), "y": str(int(cm.position_y))})
        if cm.text:
            textElem = SubElement(cmElem, f"{P}text")
            r = SubElement(textElem, f"{A}r")
            SubElement(r, f"{A}t").text = cm.text
    return cmLst
