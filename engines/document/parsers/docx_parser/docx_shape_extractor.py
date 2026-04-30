# engines/document/parsers/docx_parser/docx_shape_extractor.py
"""
Extracts a ShapeContent from a wps:wsp element.
"""
from xml.etree.ElementTree import Element
from typing import Optional
from ...models.usdm_models import ShapeContent, RichTextContent, RichTextSpan
from .docx_utils import safe_find, safe_findall, parse_emu_to_pixels, NS

def parse_inline_shape(shape_elem: Element) -> ShapeContent:
    """
    Parses a wps:wsp shape element into ShapeContent.
    shape_elem is the <wps:wsp> element from the drawing inline.
    """
    ns_map = {
        'wps': NS.get('wps', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape'),
        'a': NS.get('a', 'http://schemas.openxmlformats.org/drawingml/2006/main'),
        'r': NS.get('r', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'),
    }

    # Shape properties
    sp_pr = safe_find(shape_elem, './/wps:spPr', ns_map)
    nv_sp_pr = safe_find(shape_elem, './/wps:nvSpPr', ns_map)
    tx_body = safe_find(shape_elem, './/wps:txBody', ns_map)

    name = ""
    if nv_sp_pr is not None:
        c_nv_pr = safe_find(nv_sp_pr, './/wps:cNvPr', ns_map)
        if c_nv_pr is not None:
            name = c_nv_pr.get('name', '')

    shape_type = "rect"
    if sp_pr is not None:
        prst_geom = safe_find(sp_pr, './/a:prstGeom', ns_map)
        if prst_geom is not None:
            shape_type = prst_geom.get('prst', 'rect').lower()

        xfrm = safe_find(sp_pr, './/a:xfrm', ns_map)
        off = safe_find(xfrm, './/a:off', ns_map) if xfrm else None
        ext = safe_find(xfrm, './/a:ext', ns_map) if xfrm else None
        x = int(off.get('x', 0)) if off is not None else 0
        y = int(off.get('y', 0)) if off is not None else 0
        width = int(ext.get('cx', 0)) if ext is not None else 0
        height = int(ext.get('cy', 0)) if ext is not None else 0
        rotation = int(xfrm.get('rot', 0)) if xfrm else 0
    else:
        x = y = 0
        width = height = 0
        rotation = 0

    # Fill / line colours from spPr
    fill_color = None
    line_color = None
    line_width = 12700
    if sp_pr is not None:
        solid_fill = safe_find(sp_pr, './/a:solidFill', ns_map)
        if solid_fill is not None:
            srgb = safe_find(solid_fill, './/a:srgbClr', ns_map)
            if srgb is not None:
                fill_color = f"#{srgb.get('val', '')}"
        ln = safe_find(sp_pr, './/a:ln', ns_map)
        if ln is not None:
            line_width = int(ln.get('w', '12700'))
            solid_ln = safe_find(ln, './/a:solidFill/a:srgbClr', ns_map)
            if solid_ln is not None:
                line_color = f"#{solid_ln.get('val', '')}"

    # Rich text from txBody
    rich_text = None
    if tx_body is not None:
        rich_text = _parse_drawing_rich_text(tx_body, ns_map)

    return ShapeContent(
        shape_type=shape_type,
        x=x,
        y=y,
        width=width,
        height=height,
        name=name,
        text=rich_text,
        fill_color=fill_color,
        line_color=line_color,
        line_width=line_width,
        rotation=rotation // 60000 if rotation > 0 else 0,
        hidden=False,
    )

def _parse_drawing_rich_text(tx_body, ns_map) -> Optional[RichTextContent]:
    spans = []
    for p in safe_findall(tx_body, './/a:p', ns_map):
        for r in safe_findall(p, './/a:r', ns_map):
            t_el = safe_find(r, './/a:t', ns_map)
            t_el = safe_find(r, './/a:t', ns_map)
            text = t_el.text if t_el is not None and t_el.text is not None else ""
            rpr = safe_find(r, './/a:rPr', ns_map)
            span = RichTextSpan(text=text)
            if rpr is not None:
                style = rpr.get("style")
                if style:
                    span.character_style = style
            spans.append(span)
    return RichTextContent(spans=spans) if spans else None