# engines/document/writers/pptx_writer/slide_writer.py
"""
Write a complete <p:sld> element from a Slide object.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.psdm_models import MediaReference
from ...models.psdm_models import Slide
from ...models.usdm_models import ChartContent
from ...models.usdm_models import DrawingContent
from ...models.usdm_models import ElementType
from ...models.usdm_models import ImageContent
from ...models.usdm_models import LogicalElement
from ...models.usdm_models import OLEObjectContent
from ...models.usdm_models import ShapeContent
from ...models.usdm_models import TableContent
from .animation_writer import write_animations
from .animation_writer import write_transition
from .constants import NAMESPACES
from ..drawingml_helpers import set_solid_color
from .ole_writer import write_ole_element
from .shape_writer import write_picture
from .shape_writer import write_shape
from .table_writer import write_table
from .utils import dict_to_element

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"
R = f"{{{NAMESPACES['r']}}}"
C = f"{{{NAMESPACES.get('c', 'http://schemas.openxmlformats.org/drawingml/2006/chart')}}}"
DGM = f"{{{NAMESPACES.get('dgm', 'http://schemas.openxmlformats.org/drawingml/2006/diagram')}}}"


def write_slide(slide: Slide) -> Element:
    """Generate the <p:sld> XML element for a slide."""
    sld = Element(f"{P}sld")

    # Slide‑level attributes (name, showMasterSp, etc.)
    for attr, val in slide._meta.get("slide_attrs", {}).items():
        sld.set(attr, str(val))

    # Common slide data
    cSld = SubElement(sld, f"{P}cSld")

    # Background
    if slide.background_color or slide.background_image:
        bg = SubElement(cSld, f"{P}bg")
        bgPr = SubElement(bg, f"{P}bgPr")
        if slide.background_color:
            set_solid_color(bgPr, slide.background_color)
        if slide.background_image:
            # blipFill
            blipFill = SubElement(bgPr, f"{A}blipFill")
            _blip = SubElement(blipFill, f"{A}blip", {f"{R}embed": slide.background_image.src})
            stretch = SubElement(blipFill, f"{A}stretch")
            SubElement(stretch, f"{A}fillRect")

    # Shape tree
    spTree = SubElement(cSld, f"{P}spTree")
    _write_spTree(spTree, slide)

    # PresentationTransition
    trans_elem = write_transition(slide.transition)
    if trans_elem is not None:
        sld.append(trans_elem)

    # Timing (animations)
    # Prefer the exact timing tree stored during parsing for round‑trip fidelity.
    stored_timing = slide._meta.get("timing")
    if stored_timing:
        timing_elem = Element(f"{P}timing")
        dict_to_element(timing_elem, stored_timing, NAMESPACES)
        sld.append(timing_elem)
    else:
        timing = write_animations(slide.animations)
        if timing is not None:
            sld.append(timing)

    return sld


def _write_spTree(spTree: Element, slide: Slide) -> None:
    """Append all logical elements to the spTree."""
    for elem in slide.elements:
        if elem.element_type == ElementType.SHAPE:
            shape = elem.content
            if isinstance(shape, ShapeContent):
                spTree.append(write_shape(shape, elem.element_id))
            # else maybe GroupShapeContent? write_group_shape handles that
        elif elem.element_type == ElementType.IMAGE:
            img = elem.content
            if isinstance(img, ImageContent):
                spTree.append(write_picture(img, elem.element_id))
        elif elem.element_type == ElementType.TABLE:
            if isinstance(elem.content, TableContent):
                spTree.append(write_table(elem.content))
        elif elem.element_type == ElementType.CHART:
            chart = elem.content
            if isinstance(chart, ChartContent):
                _write_chart_frame(spTree, chart, elem.element_id)
        elif elem.element_type == ElementType.DRAWING:
            # Diagram / SmartArt
            drawing = elem.content
            if isinstance(drawing, DrawingContent):
                _write_diagram_frame(spTree, drawing, elem.element_id)
        elif elem.element_type == ElementType.OLE_OBJECT:
            ole = elem.content
            if isinstance(ole, OLEObjectContent):
                # The rId was stored in relationship_id; we need the relationship ID string
                rid = ole.relationship_id or ""
                spTree.append(write_ole_element(ole, rid))
        # Media containers were already handled by media references attached to shapes; no separate media element.

    # Media containers: if a shape had a media_reference, wrap it in <p:media>
    for elem in slide.elements:
        if elem.element_type in (ElementType.SHAPE, ElementType.IMAGE):
            media_ref = elem._meta.get("media_reference")
            if isinstance(media_ref, MediaReference):
                _wrap_in_media(spTree, elem, media_ref)


def _write_chart_frame(parent: Element, chart: ChartContent, element_id: str) -> None:
    """Write a graphicFrame containing a chart reference."""
    gf = SubElement(parent, f"{P}graphicFrame")
    nvGraphicFramePr = SubElement(gf, f"{P}nvGraphicFramePr")
    SubElement(nvGraphicFramePr, f"{P}cNvPr", {"id": element_id, "name": "Chart"})
    SubElement(nvGraphicFramePr, f"{P}cNvGraphicFramePr")

    # Transform (size from chart)
    xfrm = SubElement(gf, f"{P}xfrm")
    SubElement(xfrm, f"{A}off", {"x": "0", "y": "0"})
    SubElement(xfrm, f"{A}ext", {
        "cx": str(int(chart.width * 12700)) if chart.width else "0",
        "cy": str(int(chart.height * 12700)) if chart.height else "0",
    })

    graphic = SubElement(gf, f"{A}graphic")
    graphicData = SubElement(graphic, f"{A}graphicData", {
        "uri": "http://schemas.openxmlformats.org/drawingml/2006/chart"
    })
    # The chart part relationship ID was stored in _meta["_chart_rId"] by parser, but the parser resolves the chart and removes that. We need to re‑assign a relationship ID. Typically the writer will create the relationships file; we'll assume the chart's rId is stored in chart._meta["rId"] (set during writing process). For now we use a placeholder.
    rId = chart._meta.get("rId", "") or f"rId{hash(chart) % 1000}"
    SubElement(graphicData, f"{C}chart", {f"{R}id": rId})


def _write_diagram_frame(parent: Element, drawing: DrawingContent, element_id: str) -> None:
    """Write a graphicFrame for a diagram (SmartArt)."""
    gf = SubElement(parent, f"{P}graphicFrame")
    nvGraphicFramePr = SubElement(gf, f"{P}nvGraphicFramePr")
    SubElement(nvGraphicFramePr, f"{P}cNvPr", {"id": element_id, "name": "Diagram"})
    SubElement(nvGraphicFramePr, f"{P}cNvGraphicFramePr")

    xfrm = SubElement(gf, f"{P}xfrm")
    SubElement(xfrm, f"{A}off", {"x": "0", "y": "0"})
    SubElement(xfrm, f"{A}ext", {
        "cx": str(int(drawing.width * 12700)) if drawing.width else "0",
        "cy": str(int(drawing.height * 12700)) if drawing.height else "0",
    })

    graphic = SubElement(gf, f"{A}graphic")
    graphicData = SubElement(graphic, f"{A}graphicData", {
        "uri": "http://schemas.openxmlformats.org/drawingml/2006/diagram"
    })
    # Use the relationship ID stored in drawing._meta (set during writing)
    rId = drawing._meta.get("rId", "") or f"rId{hash(drawing) % 1000}"
    SubElement(graphicData, f"{DGM}relIds", {f"{R}id": rId})


def _wrap_in_media(spTree: Element, logical_elem: LogicalElement, media_ref: MediaReference) -> None:
    """Replace the element with a <p:media> wrapper containing the shape and media reference."""
    # Find the element in spTree (we'll remove it and reinsert)
    # For simplicity, we'll find it by element_id
    for child in spTree:
        if child.tag.endswith("}sp") or child.tag.endswith("}pic"):
            nv = child.find(f"{P}nvSpPr/{P}cNvPr")
            if nv is not None and nv.get("id") == logical_elem.element_id:
                mediaElem = Element(f"{P}media")
                # Copy the visual element inside
                mediaElem.append(child)
                # Add audio/video child
                if media_ref.media_type == "audio":
                    audio = SubElement(mediaElem, f"{P}audio")
                    audio.set(f"{R}link", media_ref.relationship_id)
                    if media_ref.start_time:
                        audio.set("start", str(int(media_ref.start_time * 1000)))
                    if media_ref.end_time:
                        audio.set("end", str(int(media_ref.end_time * 1000)))
                    if media_ref.loop:
                        audio.set("loop", "1")
                else:
                    video = SubElement(mediaElem, f"{P}video")
                    video.set(f"{R}link", media_ref.relationship_id)
                    if media_ref.start_time:
                        video.set("start", str(int(media_ref.start_time * 1000)))
                    if media_ref.end_time:
                        video.set("end", str(int(media_ref.end_time * 1000)))
                    if media_ref.loop:
                        video.set("loop", "1")
                spTree.remove(child)
                spTree.append(mediaElem)
                break
