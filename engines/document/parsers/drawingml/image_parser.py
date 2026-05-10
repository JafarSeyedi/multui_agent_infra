# engines/document/parsers/drawingml/image_parser.py
"""
Parses image references from DrawingML (a:blip) and resolves them to ImageContent.
Shared between XLSX and PPTX parsers.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from zipfile import ZipFile

from ...models.usdm_models import ImageContent

# DrawingML namespaces
NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",    # for PPTX
    "xdr": "http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing",  # for XLSX
}


def parse_image(blip_element: Element) -> ImageContent | None:
    """
    Extract image metadata from an <a:blip> element.

    Returns:
        ImageContent with src set to the relationship ID (e.g., "rId2").
    """
    if blip_element is None:
        return None

    embed = blip_element.get(f"{{{NS['r']}}}embed")
    if not embed:
        return None

    # Optional size information can be extracted from the parent <pic> element,
    # but we only handle the blip here. The caller should set width/height if available.
    return ImageContent(src=embed)


def parse_image_from_pic(pic_element: Element) -> ImageContent | None:
    """
    Extract a complete ImageContent from a <p:pic> (PPTX) or <xdr:pic> (XLSX) element.
    This includes sizing from the shape properties.

    Returns:
        ImageContent with width/height if present in the pic's xfrm.
    """
    # Find the <a:blip> within the pic
    blip = None
    for elem in pic_element.iter():
        if elem.tag.endswith("}blip"):
            blip = elem
            break

    img = parse_image(blip) if blip is not None else None
    if img is None:
        return None

    # Extract size from the shape transform (xfrm)
    sp_pr = pic_element.find("p:spPr", NS) or pic_element.find("xdr:spPr", NS) or pic_element.find("a:spPr", NS)
    if sp_pr is not None:
        xfrm = sp_pr.find("a:xfrm", NS)
        if xfrm is not None:
            ext = xfrm.find("a:ext", NS)
            if ext is not None:
                cx = int(ext.get("cx", 0))
                cy = int(ext.get("cy", 0))
                if cx:
                    img.width = cx / 12700   # EMU to points
                if cy:
                    img.height = cy / 12700

    # Alternative text
    nv_pic_pr = pic_element.find("p:nvPicPr", NS) or pic_element.find("xdr:nvPicPr", NS)
    if nv_pic_pr is not None:
        c_nv_pr = nv_pic_pr.find("p:cNvPr", NS) or nv_pic_pr.find("xdr:cNvPr", NS)
        if c_nv_pr is not None:
            img.alt = c_nv_pr.get("descr")

    return img


def resolve_image(
    img: ImageContent,
    image_rels: dict[str, str],
    zip_file: ZipFile,
    base_path: str = "",
) -> ImageContent:
    """
    Replace the relationship ID in an ImageContent with the actual ZIP path.

    Args:
        img: ImageContent with src set to a relationship ID (e.g., "rId2").
        image_rels: Dictionary mapping rel ID to target (from drawing or slide .rels).
        zip_file: The open ZIP archive.
        base_path: The directory containing the rels file (e.g., "ppt/slides").
    Returns:
        The same ImageContent instance with src replaced by the path to the image file
        (e.g., "ppt/media/image1.png").
    """
    r_id = img.src
    if r_id in image_rels:
        target = image_rels[r_id]
        if base_path:
            # Resolve relative to base_path
            if target.startswith("../"):
                # Navigate up
                parts = base_path.split("/")
                target_parts = target.split("/")
                for part in target_parts:
                    if part == "..":
                        parts.pop()
                    else:
                        parts.append(part)
                img.src = "/".join(parts)
            else:
                img.src = f"{base_path}/{target}" if base_path else target
        else:
            img.src = target
    return img
