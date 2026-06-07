# engines/document/parsers/psdm_parsers/pptx/notes_parser.py
"""
Parses a PPTX notes slide XML part into a NotesSlide object.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.psdm_models import NotesSlide
from ....models.usdm_models import ParagraphContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from .constants import NAMESPACES

NS = NAMESPACES


def parse_notes_slide(notes_xml: Element) -> NotesSlide | None:
    """Parse a <p:notes> element into a NotesSlide."""
    spans: list[RichTextSpan] = []
    plain_text_parts: list[str] = []

    cSld = notes_xml.find("p:cSld", NS)
    if cSld is not None:
        sp_tree = cSld.find("p:spTree", NS)
        if sp_tree is not None:
            for child in sp_tree:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == "sp":
                    tx_body = child.find("p:txBody", NS)
                    if tx_body is not None:
                        for p_elem in tx_body.findall("a:p", NS):
                            para = _parse_paragraph(p_elem)
                            if para.text and para.text.spans:
                                spans.extend(para.text.spans)
                                for span in para.text.spans:
                                    if span.text:
                                        plain_text_parts.append(span.text)

    rich_text = RichTextContent(spans=spans) if spans else RichTextContent(spans=[])
    plain_text = " ".join(plain_text_parts) if plain_text_parts else ""
    return NotesSlide(text=rich_text, plain_text=plain_text)


def _parse_paragraph(p_elem: Element) -> ParagraphContent:
    """Parse an <a:p> element into ParagraphContent with rich text."""
    spans: list[RichTextSpan] = []
    for r_elem in p_elem.findall("a:r", NS):
        t_elem = r_elem.find("a:t", NS)
        text = t_elem.text if t_elem is not None and t_elem.text is not None else ""

        span = RichTextSpan(text=text)
        r_pr = r_elem.find("a:rPr", NS)
        if r_pr is not None:
            style = r_pr.get("style")
            if style:
                span.character_style = style
            bold_elem = r_pr.find("a:b", NS)
            if bold_elem is not None:
                span.bold = True
            italic_elem = r_pr.find("a:i", NS)
            if italic_elem is not None:
                span.italic = True
        spans.append(span)

    return ParagraphContent(text=RichTextContent(spans=spans))
