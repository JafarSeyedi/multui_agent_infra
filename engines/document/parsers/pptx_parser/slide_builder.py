# engines/document/parsers/pptx_parser/slide_builder.py
"""
Builds a fully populated Slide from a <p:sld> element and associated relationships.
Preserves all content for round‑trip.
"""

from __future__ import annotations
from typing import Optional, Dict, List, Any, Tuple
from xml.etree.ElementTree import Element

from ...models.psdm_models import (
    Slide, SlideLayout, SlideMaster, NotesSlide,
)
from ...models.usdm_models import (
    LogicalElement, ElementType,
    ShapeContent, ImageContent, ChartContent, TableContent,
)
from .ole_parser import parse_ole_objects
from .shape_parser import parse_pptx_shape, parse_group_shape
from .media_parser import parse_media_references

from .animation_parser import parse_slide_transition, parse_slide_animations
from .constants import NAMESPACES, REL_TYPE
from ..drawingml.image_parser import (
    parse_image_from_pic, resolve_image,
)
from ..drawingml.chart_ref_parser import parse_chart_ref
from ..drawingml.diagram_parser import parse_diagram_ref
from .utils import element_to_dict

NS = NAMESPACES


def build_slide(
    slide_xml: Element,
    slide_zip_path: str,
    zip_file,                      # ZipFile
    slide_rels: Dict[str, Tuple[str, str]],
    layouts: Dict[str, SlideLayout],
    masters: Dict[str, SlideMaster],
    package_rels: Dict[str, Tuple[str, str]],
) -> Slide:
    """
    Assemble a Slide from its XML.

    The caller is responsible for resolving the layout and any relationships
    for images/charts after this returns.
    """
    # Slide ID from filename (slide1.xml → slide1)
    slide_id = slide_zip_path.rsplit("/", 1)[-1].replace(".xml", "")

    # ---------- Slide‑level attributes ----------
    slide_attrs = dict(slide_xml.attrib)  # e.g., showMasterSp, showMasterPhAnim
    slide_name = slide_attrs.get("name")

    # ---------- Common slide data (cSld) ----------
    cSld = slide_xml.find("p:cSld", NS)
    elements: List[LogicalElement] = []
    background_color = None
    background_image = None

    if cSld is not None:
        # Background
        bg = cSld.find("p:bg", NS)
        if bg is not None:
            bg_pr = bg.find("p:bgPr", NS)
            if bg_pr is not None:
                # Solid
                solid = bg_pr.find("a:solidFill", NS)
                if solid is not None:
                    from ..drawingml.shape_parser import _parse_color
                    background_color = _parse_color(solid, NS)
                # Image (blipFill)
                blip_fill = bg_pr.find("a:blipFill", NS)
                if blip_fill is not None:
                    blip = blip_fill.find("a:blip", NS)
                    if blip is not None:
                        embed = blip.get(f"{{{NS['r']}}}embed")
                        if embed:
                            background_image = ImageContent(src=embed)

        # ---------- Shape tree (spTree) ----------
        sp_tree = cSld.find("p:spTree", NS)
        if sp_tree is not None:
            for child in sp_tree:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == "sp":
                    shape = parse_pptx_shape(child)
                    elements.append(LogicalElement(
                        element_id=shape.name or f"shape_{len(elements)}",
                        element_type=ElementType.SHAPE,
                        content=shape,
                    ))
                elif tag == "pic":
                    img = parse_image_from_pic(child)
                    if img:
                        elements.append(LogicalElement(
                            element_id=img.src or f"pic_{len(elements)}",
                            element_type=ElementType.IMAGE,
                            content=img,
                        ))
                elif tag == "graphicFrame":
                    chart = parse_chart_ref(child)
                    if chart:
                        elements.append(LogicalElement(
                            element_id=f"chart_{len(elements)}",
                            element_type=ElementType.CHART,
                            content=chart,
                        ))
                    else:
                        # could be a diagram or table; we skip for now but preserve in meta
                        pass
                elif tag == "grpSp":
                    shapes = parse_group_shape(child)
                    for shape_obj in shapes:
                        elements.append(LogicalElement(
                            element_id=shape_obj.name or f"shape_{len(elements)}",
                            element_type=ElementType.SHAPE,
                            content=shape_obj,
                        ))
                elif tag == "cxnSp":
                    shape = parse_pptx_shape(child)   # treat connector as shape
                    elements.append(LogicalElement(
                        element_id=shape.name or f"connector_{len(elements)}",
                        element_type=ElementType.SHAPE,
                        content=shape,
                    ))
                elif tag == "tbl":
                    table_content = parse_table(child)
                    elements.append(LogicalElement(
                        element_id=f"table_{len(elements)}",
                        element_type=ElementType.TABLE,
                        content=table_content,
                    ))
                elif tag == "graphicFrame":
                    chart = parse_chart_ref(child)  # existing
                    if chart:
                        elements.append(...)
                    else:
                        # Could be a diagram – check graphicData URI
                        graphic = child.find(".//a:graphic", NS)
                        if graphic is not None:
                            graphic_data = graphic.find("a:graphicData", NS)
                            if graphic_data is not None:
                                diag = parse_diagram_ref(graphic_data)
                                if diag:
                                    elements.append(LogicalElement(
                                        element_id=f"diagram_{len(elements)}",
                                        element_type=ElementType.DRAWING,
                                        content=diag,
                                    ))                    
                elif tag == "media":
                    # A media container (audio/video) – contains a shape and media reference
                    # Extract the inner shape (sp, pic, etc.) for visual representation
                    shape_elem = child.find("p:sp", NS) or child.find("p:pic", NS) or child.find("p:grpSp", NS)
                    if shape_elem is not None:
                        # Parse the shape normally
                        if shape_elem.tag.endswith("sp"):
                            shape = parse_pptx_shape(shape_elem)
                            elem = LogicalElement(...)
                            elements.append(elem)
                        elif shape_elem.tag.endswith("pic"):
                            img = parse_image_from_pic(shape_elem)
                            if img:
                                elements.append(LogicalElement(..., element_type=ElementType.IMAGE, content=img))
                        # No media reference here – it will be handled by parse_media_references
                        # # Then parse the media reference from the <p:media> element itself
                        # media_ref = _parse_media_from_container(child)
                        # if media_ref:
                        #     # Attach the media ref to the last added element (the shape)
                        #     elements[-1]._meta["media_reference"] = media_ref
                    else:
                        # Possibly a direct media element without visual?
                        pass

    ole_objects = parse_ole_objects(slide_xml)
    for ole in ole_objects:
        elements.append(LogicalElement(
            element_id=f"{ole.prog_id}_{ole.relationship_id}",
            element_type=ElementType.OLE_OBJECT,
            content=ole,
        ))

    media_refs = parse_media_references(slide_xml, slide_rels, _dir_of(slide_zip_path))
    # Map relationship ID → MediaReference
    refs_by_rid = {ref.relationship_id: ref for ref in media_refs}
    # Walk through elements and link media to shapes that reference a media file.
    standalone_media = []
    for elem in elements:
        shape = elem.content
        if isinstance(shape, ShapeContent) and hasattr(shape, '_meta'):
            media_rid = shape._meta.get("media_link_rId")
            if media_rid and media_rid in refs_by_rid:
                # Attach the MediaReference directly to the shape element
                elem._meta["media_reference"] = refs_by_rid[media_rid]
                # Remove from the flat list so it is not duplicated
                del refs_by_rid[media_rid]
            elif media_rid:
                # A media link without a matching reference (should not happen)
                pass

    # Any remaining media references are standalone (e.g., background music)
    standalone_media = list(refs_by_rid.values())
    # ---------- Transition ----------
    transition = parse_slide_transition(slide_xml)

    # ---------- Animations ----------
    animations = parse_slide_animations(slide_xml)

    # ---------- Timing (additional) ----------
    timing_elem = slide_xml.find("p:timing", NS)
    timing_data = element_to_dict(timing_elem) if timing_elem is not None else None
    
    # ---------- Build Slide ----------
    slide = Slide(
        slide_id=slide_id,
        layout=None,                                # to be set by caller
        background_color=background_color,
        background_image=background_image,
        elements=elements,
        transition=transition,
        animations=animations,
        notes=None,                                 # to be attached later
        name=slide_name,
        media_references=standalone_media
    )
    # Extra metadata for round‑trip
    slide._meta = {
        "slide_attrs": slide_attrs,
        "path": slide_zip_path,
        "timing": timing_data,
    }
    return slide

def _dir_of(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""

def _parse_media_from_container(media_elem: Element) -> Optional[MediaReference]:
    """Extract a MediaReference from a <p:media> element."""
    # The relationship to the media file is in the <p:media> attributes (r:link)
    r_id = media_elem.get(f"{{{NS['r']}}}link")
    if not r_id:
        return None
    tag = media_elem.tag.split("}")[-1]
    media_type = "audio" if "audio" in tag.lower() else "video"
    # Get timing
    start = _parse_time(media_elem.get("start"))
    end = _parse_time(media_elem.get("end"))
    loop = media_elem.get("loop") == "1"
    return MediaReference(
        relationship_id=r_id,
        media_type=media_type,
        mime_type=_guess_type_from_ext(r_id),  # would need the relationship to get real path, but we can leave empty
        start_time=start,
        end_time=end,
        loop=loop,
    )
    
def _attach_media_to_element(elem: LogicalElement, r_id: str, media_type: str, media_elem: Element):
    """Attach a MediaReference to a shape element."""
    start = _parse_time(media_elem.get("start"))
    end = _parse_time(media_elem.get("end"))
    loop = media_elem.get("loop") == "1"
    ref = MediaReference(
        relationship_id=r_id,
        media_type=media_type,
        start_time=start,
        end_time=end,
        loop=loop,
    )
    elem._meta["media_reference"] = ref

def _add_media_ref(refs: List[MediaReference], r_id: str, media_type: str, elem: Element):
    """Add a MediaReference to the list (for standalone media)."""
    start = _parse_time(elem.get("start"))
    end = _parse_time(elem.get("end"))
    loop = elem.get("loop") == "1"
    refs.append(MediaReference(
        relationship_id=r_id,
        media_type=media_type,
        start_time=start,
        end_time=end,
        loop=loop,
    ))

def _parse_time(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val) / 1000.0
    except ValueError:
        return None    