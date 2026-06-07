from __future__ import annotations

from typing import Any

from ....models.usdm_models import ImageContent
from ....models.usdm_models import LogicalElement


IMAGE_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".svg": "image/svg+xml",
    ".emf": "image/x-emf",
    ".wmf": "image/x-wmf",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
}

IMAGE_REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"


def process_images(document: Any) -> dict[str, Any]:
    """
    Extract and process all images from a USDMDocument.

    Scans logical elements for ImageContent, collects image data,
    assigns relationship IDs, and generates Content_Type entries.

    Returns a dict with:
        - 'images': dict mapping rel_id -> {'data': bytes, 'content_type': str, 'filename': str}
        - 'rels': list of relationship dicts for document rels
        - 'content_type_defaults': list of (extension, content_type) tuples
    """
    images: dict[str, Any] = {}
    rels: list[dict[str, str]] = []
    ct_extensions: dict[str, str] = {}
    img_counter = 0

    for elem in getattr(document, "logical_elements", []):
        _scan_element_for_images(elem, images, rels, ct_extensions, img_counter)
        img_counter = len(images)

    return {
        "images": images,
        "rels": rels,
        "content_type_defaults": list(ct_extensions.items()),
    }


def _scan_element_for_images(
    elem: Any,
    images: dict[str, Any],
    rels: list[dict[str, str]],
    ct_extensions: dict[str, str],
    counter: int,
) -> int:
    """Recursively scan an element for ImageContent."""
    if not isinstance(elem, LogicalElement):
        return counter

    content = elem.content
    if isinstance(content, ImageContent):
        counter = _register_image(content, images, rels, ct_extensions, counter)

    # Recurse into container elements
    if hasattr(content, "elements"):
        for sub in content.elements:
            counter = _scan_element_for_images(sub, images, rels, ct_extensions, counter)

    if hasattr(content, "items"):
        for item in content.items:
            if hasattr(item, "elements"):
                for sub in item.elements:
                    counter = _scan_element_for_images(sub, images, rels, ct_extensions, counter)

    if hasattr(content, "rows"):
        for row in content.rows:
            for cell in row.cells:
                for sub in cell.content:
                    counter = _scan_element_for_images(sub, images, rels, ct_extensions, counter)

    return counter


def _register_image(
    img_content: ImageContent,
    images: dict[str, Any],
    rels: list[dict[str, str]],
    ct_extensions: dict[str, str],
    counter: int,
) -> int:
    """Register a single image and return updated counter."""
    src = getattr(img_content, "src", None)
    if not src:
        return counter

    counter += 1
    rel_id = f"rImg{counter}"
    filename = _src_to_filename(src)
    ext = _get_extension(filename)
    content_type = IMAGE_EXTENSIONS.get(ext, "image/png")

    image_data = _resolve_image_data(img_content)

    images[rel_id] = {
        "data": image_data,
        "content_type": content_type,
        "filename": filename,
        "alt": getattr(img_content, "alt", None),
        "width": getattr(img_content, "width", None),
        "height": getattr(img_content, "height", None),
    }

    rels.append({
        "id": rel_id,
        "type": "image",
        "target": f"media/{filename}",
    })

    if ext and ext not in ct_extensions:
        ct_extensions[ext] = content_type

    return counter


def _resolve_image_data(img_content: ImageContent) -> bytes:
    """
    Resolve image data from an ImageContent.

    Tries multiple sources:
    1. metadata['data'] as raw bytes
    2. metadata['base64_data'] as base64-encoded string
    3. src as a file path
    4. src as a data URI
    5. Fallback: empty PNG
    """
    metadata = getattr(img_content, "metadata", {}) or {}

    raw = metadata.get("data")
    if raw and isinstance(raw, bytes):
        return raw

    b64 = metadata.get("base64_data")
    if b64 and isinstance(b64, str):
        import base64
        try:
            return base64.b64decode(b64)
        except Exception:
            pass

    src = getattr(img_content, "src", "")

    if src.startswith("data:"):
        try:
            import base64
            comma = src.index(",")
            return base64.b64decode(src[comma + 1:])
        except Exception:
            pass

    import os
    if os.path.isfile(src):
        try:
            with open(src, "rb") as f:
                return f.read()
        except OSError:
            pass

    return _minimal_png()


def _src_to_filename(src: str) -> str:
    """Convert an image src to a filename suitable for word/media/."""
    import os
    base = os.path.basename(src.split("?")[0].split("#")[0])
    if not base or base == "." or base == "/":
        base = "image1.png"
    if "." not in base:
        base += ".png"
    return base


def _get_extension(filename: str) -> str:
    """Get the lowercase extension from a filename."""
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower()


def generate_image_relationship_entries(images: dict[str, Any]) -> list[dict[str, str]]:
    """
    Generate relationship entries for all registered images.

    Returns list of dicts suitable for document_rels_xml().
    """
    rels: list[dict[str, str]] = []
    for rel_id, info in images.items():
        rels.append({
            "id": rel_id,
            "type": "image",
            "target": f"media/{info['filename']}",
        })
    return rels


def generate_content_type_defaults(images: dict[str, Any]) -> list[tuple[str, str]]:
    """
    Generate Content_Type Default entries for image formats present.

    Returns list of (extension, content_type) tuples.
    """
    seen: dict[str, str] = {}
    for info in images.values():
        ext = _get_extension(info["filename"])
        if ext and ext not in seen:
            seen[ext] = info["content_type"]
    return list(seen.items())


def build_drawing_xml(
    rel_id: str,
    width_emu: int = 914400,
    height_emu: int = 914400,
    alt: str = "",
    title: str = "",
) -> str:
    """
    Build a <w:drawing> element for an inline image.

    Args:
        rel_id: Relationship ID for the image.
        width_emu: Width in English Metric Units (1 inch = 914400 EMU).
        height_emu: Height in EMU.
        alt: Alternative text.
        title: Image title.

    Returns:
        XML string for the w:drawing element.
    """
    alt_attr = f' descr="{_esc_attr(alt)}"' if alt else ""
    title_attr = f' title="{_esc_attr(title)}"' if title else ""
    name = f"Image_{rel_id}"

    return (
        "<w:drawing>"
        "<wp:inline distT=\"0\" distB=\"0\" distL=\"0\" distR=\"0\">"
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        f'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="1" name="{name}"{alt_attr}{title_attr}/>'
        "<wp:cNvGraphicFramePr>"
        '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
        "</wp:cNvGraphicFramePr>"
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        "<pic:nvPicPr>"
        '<pic:cNvPr id="0" name="{name}"{alt_attr}/>'
        "<pic:cNvPicPr/>"
        "</pic:nvPicPr>"
        "<pic:blipFill>"
        f'<a:blip r:embed="{rel_id}"/>'
        "<a:stretch><a:fillRect/></a:stretch>"
        "</pic:blipFill>"
        "<pic:spPr>"
        '<a:xfrm><a:off x="0" y="0"/><a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        "</pic:spPr>"
        "</pic:pic>"
        "</a:graphicData>"
        "</a:graphic>"
        "</wp:inline>"
        "</w:drawing>"
    ).format(
        name=name,
        alt_attr=f' descr="{_esc_attr(alt)}"' if alt else "",
        width_emu=width_emu,
        height_emu=height_emu,
        rel_id=rel_id,
    )


def _esc_attr(val: str) -> str:
    """Escape XML attribute value."""
    s = str(val)
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s


def _minimal_png() -> bytes:
    """Return a minimal 1x1 transparent PNG as fallback."""
    import struct
    import zlib

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)
    raw = zlib.compress(b"\x00\x00\x00\x00\x00")
    idat = chunk(b"IDAT", raw)
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend
