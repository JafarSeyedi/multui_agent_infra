# engines/document/parsers/spreadsheet_parser/xlsx/drawings_builder.py
"""
Complete DrawingML parser for SpreadsheetML drawings.
Extracts shapes, images, and chart references with full detail.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.esdm_models import ShapeContent
from ....models.usdm_models import ChartContent
from ....models.usdm_models import ImageContent
from ....models.usdm_models import RichTextContent
from ....models.usdm_models import RichTextSpan
from .utils import xml_attr
from .utils import xml_find
from .utils import xml_findall
from .utils import xml_float
from .utils import xml_int
from .utils import xml_text

# Namespaces
XDR = "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing"
A   = "http://schemas.openxmlformats.org/drawingml/2006/main"
R   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
C   = "http://schemas.openxmlformats.org/drawingml/2006/chart"

NS = {
    "xdr": XDR,
    "a": A,
    "r": R,
    "c": C,
}


def parse_drawing(
    drawing_xml: Element,
    image_map: dict[str, str] | None = None,   # relId -> zip path of image file
) -> tuple[list[ShapeContent], list[ImageContent], list[ChartContent]]:
    """
    Returns lists of fully populated ShapeContent, ImageContent, ChartContent.
    image_map can be empty; if provided, image src will be replaced with real path.
    """
    shapes: list[ShapeContent] = []
    images: list[ImageContent] = []
    charts:list[ChartContent] = []
    # Iterate over all possible anchor types
    for anchor in (
        xml_findall(drawing_xml, "xdr:twoCellAnchor", NS) +
        xml_findall(drawing_xml, "xdr:oneCellAnchor", NS) +
        xml_findall(drawing_xml, "xdr:absoluteAnchor", NS)
    ):
        _parse_anchor(anchor, shapes, images, charts, image_map or {})
    return shapes, images, charts


def _parse_anchor(
    anchor: Element,
    shapes: list,
    images: list,
    charts: list,
    image_map: dict[str, str],
):
    # Position (from/to)
    from_el = xml_find(anchor, "xdr:from", NS)
    from_col, from_row, from_col_off, from_row_off = 0, 0, 0, 0
    if from_el is not None:
        from_col = xml_int(from_el, "xdr:col", 0)
        from_row = xml_int(from_el, "xdr:row", 0)
        from_col_off = xml_int(from_el, "xdr:colOff", 0)
        from_row_off = xml_int(from_el, "xdr:rowOff", 0)

    # Common shape parsing
    def extract_shapes(element):
        for sp in xml_findall(element, "xdr:sp", NS):
            shape = _parse_shape(sp, from_col, from_row, from_col_off, from_row_off)
            if shape:
                shapes.append(shape)
        for grp_sp in xml_findall(element, "xdr:grpSp", NS):
            extract_shapes(grp_sp)

    extract_shapes(anchor)

    # Pictures
    for pic in xml_findall(anchor, "xdr:pic", NS):
        img = _parse_image(pic, from_col_off, from_row_off, image_map)
        if img:
            images.append(img)

    # Graphic frames (charts)
    for gf in xml_findall(anchor, "xdr:graphicFrame", NS):
        chart = _parse_chart_ref(gf)
        if chart is not None:
            charts.append(chart)


def _parse_shape(
    sp: Element,
    col: int, row: int,
    col_off: int, row_off: int,
) -> ShapeContent | None:
    nv_sp_pr = xml_find(sp, "xdr:nvSpPr", NS)
    sp_pr = xml_find(sp, "xdr:spPr", NS)
    tx_body = xml_find(sp, "xdr:txBody", NS)

    name = ""
    if nv_sp_pr is not None:
        c_nv_pr = xml_find(nv_sp_pr, "xdr:cNvPr", NS)
        if c_nv_pr is not None:
            name = xml_attr(c_nv_pr, "name", "Shape")

    # Shape type from preset geometry
    shape_type = "rect"
    if sp_pr is not None:
        prst_geom = xml_find(sp_pr, "a:prstGeom", NS)
        if prst_geom is not None:
            shape_type = xml_attr(prst_geom, "prst", "rect")

    # Transform (position and size in EMU)
    xfrm = xml_find(sp_pr, "a:xfrm", NS) if sp_pr else None
    off = xml_find(xfrm, "a:off", NS) if xfrm else None
    ext = xml_find(xfrm, "a:ext", NS) if xfrm else None

    x = xml_int(off, "x", 0) if off is not None else 0
    y = xml_int(off, "y", 0) if off is not None else 0
    width = xml_int(ext, "cx", 0) if ext is not None else 0
    height = xml_int(ext, "cy", 0) if ext is not None else 0
    rotation = xml_int(xfrm, "rot", 0) if xfrm is not None else 0

    # Fill
    fill_color = None
    if sp_pr is not None:
        solid_fill = xml_find(sp_pr, "a:solidFill", NS)
        if solid_fill is not None:
            srgb = xml_find(solid_fill, "a:srgbClr", NS)
            if srgb is not None:
                fill_color = f"#{xml_attr(srgb, 'val', '')}"
        elif xml_find(sp_pr, "a:noFill", NS) is not None:
            fill_color = None

    # Line
    line_color = None
    line_width = 12700  # default 1pt
    ln = xml_find(sp_pr, "a:ln", NS) if sp_pr else None
    if ln is not None:
        line_width = xml_int(ln, "w", 12700)
        solid_fill_ln = xml_find(ln, "a:solidFill", NS)
        if solid_fill_ln is not None:
            srgb = xml_find(solid_fill_ln, "a:srgbClr", NS)
            if srgb is not None:
                line_color = f"#{xml_attr(srgb, 'val', '')}"
        elif xml_find(ln, "a:noFill", NS) is not None:
            line_color = None

    # Rich text from txBody
    rich_text = None
    if tx_body is not None:
        rich_text = _parse_drawing_rich_text(tx_body)

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
        rotation=rotation // 60000 if rotation else 0,  # EMU rotation to degrees (simplified)
        hidden=False,
    )


def _parse_drawing_rich_text(tx_body: Element) -> RichTextContent | None:
    """
    Parse <a:p> elements with <a:r> runs and <a:rPr> formatting.
    Returns a RichTextContent with full run properties.
    """
    spans = []
    for p in xml_findall(tx_body, "a:p", NS):
        # paragraph properties (optional)
        # pPr = xml_find(p, "a:pPr", NS)
        for r in xml_findall(p, "a:r", NS):
            rpr = xml_find(r, "a:rPr", NS)
            t_el = xml_find(r, "a:t", NS)
            text = xml_text(t_el) if t_el is not None else ""
            span = RichTextSpan(text=text)
            if rpr is not None:
                span.bold = xml_find(rpr, "a:b", NS) is not None
                span.italic = xml_find(rpr, "a:i", NS) is not None
                # underline
                u = xml_find(rpr, "a:u", NS)
                span.underline = u is not None
                # font size (in hundredths of points)
                sz = xml_float(xml_find(rpr, "a:sz", NS), "val", None) if xml_find(rpr, "a:sz", NS) is not None else None
                if sz:
                    span.character_style = f"size:{sz/100}"
                # color
                solid = xml_find(rpr, "a:solidFill/a:srgbClr", NS)
                if solid is not None:
                    span.color = f"#{xml_attr(solid, 'val', '')}"
                # font name
                latin = xml_find(rpr, "a:latin", NS)
                if latin is not None:
                    span.font = xml_attr(latin, "typeface")
            spans.append(span)
    return RichTextContent(spans=spans) if spans else None


def _parse_image(
    pic: Element,
    col_off: int, row_off: int,
    image_map: dict[str, str],
) -> ImageContent | None:
    nv_pic_pr = xml_find(pic, "xdr:nvPicPr", NS)
    blip_fill = xml_find(pic, "xdr:blipFill", NS)
    if blip_fill is None:
        return None
    blip = xml_find(blip_fill, "a:blip", NS)
    if blip is None:
        return None
    embed = xml_attr(blip, "r:embed")
    if embed is None:
        return None

    # Size from transform
    sp_pr = xml_find(pic, "xdr:spPr", NS)
    xfrm = xml_find(sp_pr, "a:xfrm", NS) if sp_pr else None
    off = xml_find(xfrm, "a:off", NS) if xfrm else None
    ext = xml_find(xfrm, "a:ext", NS) if xfrm else None

    x = xml_int(off, "x", 0) if off else 0
    y = xml_int(off, "y", 0) if off else 0
    width = xml_int(ext, "cx", 0) if ext else 0
    height = xml_int(ext, "cy", 0) if ext else 0

    # Resolve actual image path from relationships
    src = embed  # store rel id initially, can be replaced with real path
    if image_map and embed in image_map:
        src = image_map[embed]  # e.g., 'xl/media/image1.png'

    return ImageContent(
        src=src,
        width=width / 12700 if width else None,  # EMU to points (1pt = 12700 EMU)
        height=height / 12700 if height else None,
        alt=xml_attr(nv_pic_pr, "descr", "") if nv_pic_pr else None,
        metadata={"col_off": col_off, "row_off": row_off, "x": x, "y": y},
    )

def _parse_chart_ref(gf: Element) -> ChartContent | None:
    """Return a placeholder ChartContent with only the relationship ID."""
    graphic = xml_find(gf, "a:graphic", NS)
    if graphic is None:
        return None
    graphic_data = xml_find(graphic, "a:graphicData", NS)
    if graphic_data is None:
        return None
    chart_el = xml_find(graphic_data, "c:chart", NS)
    if chart_el is None:
        return None
    r_id = xml_attr(chart_el, "r:id")
    if r_id is None:
        return None
    chart = ChartContent(chart_type="unknown")
    # Temporary attribute to link with chart file data later
    chart._chart_rId = r_id
    return chart
