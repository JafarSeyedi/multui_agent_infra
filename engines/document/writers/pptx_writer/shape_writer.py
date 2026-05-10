# engines/document/writers/pptx_writer/shape_writer.py
"""
Write <p:sp>, <p:pic>, <p:grpSp> from ShapeContent / ImageContent / GroupShapeContent.
No missing features; all visual properties recovered from model + _meta.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

from ...models.psdm_models import GroupShapeContent
from ...models.psdm_models import Placeholder
from ...models.usdm_models import ImageContent
from ...models.usdm_models import ShapeContent
from ..drawingml_helpers import write_effects
from ..drawingml_helpers import write_fill
from ..drawingml_helpers import write_line
from ..drawingml_helpers import write_rich_text_body
from ..drawingml_helpers import write_scene3d
from ..drawingml_helpers import write_sp3d
from .constants import NAMESPACES

P = f"{{{NAMESPACES['p']}}}"
A = f"{{{NAMESPACES['a']}}}"
R = f"{{{NAMESPACES['r']}}}"


def write_shape(shape: ShapeContent, element_id: str = "1") -> Element:
    """Create <p:sp> with complete shape properties."""
    sp = Element(f"{P}sp")

    # nvSpPr ------------------------------------------------------------
    nvSpPr = SubElement(sp, f"{P}nvSpPr")

    # cNvPr
    cNvPr_attrs = shape._meta.get("cNvPr", {}).copy()
    cNvPr_attrs.setdefault("id", element_id)
    cNvPr_attrs.setdefault("name", shape.name or "Shape")
    cNvPr = SubElement(nvSpPr, f"{P}cNvPr", cNvPr_attrs)

    # Hyperlink in cNvPr
    hlink = shape._meta.get("hyperlink")
    if hlink:
        hl = SubElement(cNvPr, f"{A}hlinkClick")
        if "r_id" in hlink:
            hl.set(f"{R}id", hlink["r_id"])
        if "action" in hlink:
            hl.set("action", hlink["action"])

    # cNvSpPr: shape non‑visual (e.g., txBox)
    cNvSpPr_attrs = shape._meta.get("cNvSpPr", {})
    SubElement(nvSpPr, f"{P}cNvSpPr", cNvSpPr_attrs)

    # nvPr / placeholder
    nvPr = SubElement(nvSpPr, f"{P}nvPr")
    ph = shape._meta.get("placeholder")
    if isinstance(ph, Placeholder):
        from .constants import PSDM_TO_PPTX_PLACEHOLDER
        pptx_type = PSDM_TO_PPTX_PLACEHOLDER.get(ph.type.value, "body")
        if pptx_type:
            SubElement(nvPr, f"{P}ph", {"type": pptx_type, "idx": str(ph.idx) if ph.idx >= 0 else "1"})
    else:
        ph_type = shape._meta.get("placeholder_type")
        if ph_type:
            SubElement(nvPr, f"{P}ph", {"type": ph_type, "idx": str(shape._meta.get("placeholder_idx", "1"))})

    # spPr ---------------------------------------------------------------
    spPr = SubElement(sp, f"{P}spPr")
    _write_spPr_content(spPr, shape)

    # txBody (if text present) ------------------------------------------
    if shape.text and shape.text.spans:
        txBody = SubElement(sp, f"{P}txBody")
        SubElement(txBody, f"{A}bodyPr")
        write_rich_text_body(txBody, shape.text)

    return sp


def _write_spPr_content(spPr: Element, shape: ShapeContent) -> None:
    # Transform (xfrm)
    xfrm = SubElement(spPr, f"{A}xfrm")
    if shape.rotation:
        xfrm.set("rot", str(shape.rotation * 60000))  # degrees → EMU
    SubElement(xfrm, f"{A}off", {"x": str(shape.x), "y": str(shape.y)})
    attrs = {}
    if shape.width is not None:
        attrs["cx"] = str(shape.width)
    if shape.height is not None:
        attrs["cy"] = str(shape.height)
    SubElement(xfrm, f"{A}ext", attrs)

    # Preset geometry
    SubElement(spPr, f"{A}prstGeom", {"prst": shape.shape_type})

    # Fill
    write_fill(spPr, shape._meta.get("fill"))

    # Line
    line_info = shape._meta.get("line")
    if line_info:
        ln = SubElement(spPr, f"{A}ln")
        write_line(ln, line_info)

    # Effects
    effects = shape._meta.get("effects")
    if effects:
        effectLst = SubElement(spPr, f"{A}effectLst")
        write_effects(effectLst, effects)

    # 3D properties
    scene3d = shape._meta.get("scene3d")
    if scene3d:
        write_scene3d(spPr, scene3d)
    sp3d = shape._meta.get("sp3d")
    if sp3d:
        write_sp3d(spPr, sp3d)

    # Any extra spPr attributes from parsing
    spPr_attrs = shape._meta.get("spPr_attrs", {})
    for k, v in spPr_attrs.items():
        spPr.set(k, str(v))


# Picture ----------------------------------------------------------------
def write_picture(img: ImageContent, element_id: str = "1") -> Element:
    """Create <p:pic> element."""
    pic = Element(f"{P}pic")
    nvPicPr = SubElement(pic, f"{P}nvPicPr")
    SubElement(nvPicPr, f"{P}cNvPr", {"id": element_id, "name": "Picture", "descr": img.alt or ""})
    SubElement(nvPicPr, f"{P}cNvPicPr")
    SubElement(nvPicPr, f"{P}nvPr")

    blipFill = SubElement(pic, f"{P}blipFill")
    blip = SubElement(blipFill, f"{A}blip", {f"{R}embed": img.src})
    stretch = SubElement(blipFill, f"{A}stretch")
    SubElement(stretch, f"{A}fillRect")

    spPr = SubElement(pic, f"{P}spPr")
    xfrm = SubElement(spPr, f"{A}xfrm")
    SubElement(xfrm, f"{A}off", {"x": "0", "y": "0"})
    SubElement(xfrm, f"{A}ext", {
        "cx": str(int(img.width * 12700)) if img.width else "0",
        "cy": str(int(img.height * 12700)) if img.height else "0"
    })
    SubElement(spPr, f"{A}prstGeom", {"prst": "rect"})
    return pic


# Group shape ------------------------------------------------------------
def write_group_shape(group: GroupShapeContent, element_id: str = "1") -> Element:
    """Write <p:grpSp> with nested shapes."""
    grp = Element(f"{P}grpSp")
    nvGrpSpPr = SubElement(grp, f"{P}nvGrpSpPr")
    SubElement(nvGrpSpPr, f"{P}cNvPr", {"id": element_id, "name": group.name or "Group"})
    SubElement(nvGrpSpPr, f"{P}cNvGrpSpPr")
    SubElement(nvGrpSpPr, f"{P}nvPr")

    grpSpPr = SubElement(grp, f"{P}grpSpPr")
    xfrm = SubElement(grpSpPr, f"{A}xfrm")
    SubElement(xfrm, f"{A}off", {"x": str(group.x), "y": str(group.y)})
    SubElement(xfrm, f"{A}ext", {"cx": str(group.width), "cy": str(group.height)})
    if group.rotation:
        xfrm.set("rot", str(group.rotation * 60000))
    SubElement(grpSpPr, f"{A}prstGeom", {"prst": "rect"})

    for child in group.children:
        if isinstance(child, ShapeContent):
            grp.append(write_shape(child, element_id=str(len(grp))))
        elif isinstance(child, GroupShapeContent):
            grp.append(write_group_shape(child, element_id=str(len(grp))))
    return grp
