# engines/document/parsers/pptx_parser/media_parser.py
"""
Extracts audio/video media references from a slide XML.
Produces MediaReference objects and optionally AudioContent/VideoContent.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from xml.etree.ElementTree import Element

from ...models.psdm_models import MediaReference
from ...models.usdm_models import AudioContent, VideoContent
from .constants import NAMESPACES
from .relationship_utils import get_target_for_id, resolve_path

NS = NAMESPACES


def parse_media_references(
    slide_xml: Element,
    slide_rels: Dict[str, Tuple[str, str]],
    base_dir: str,
) -> List[MediaReference]:
    """
    Scan the entire slide XML for <p:audio> and <p:video> elements and
    return a list of MediaReference objects with resolved paths.
    """
    refs: List[MediaReference] = []
    # Look for <p:audio> and <p:video> anywhere in the slide
    for elem in slide_xml.iter():
        if elem.tag == f"{{{NS['p']}}}audio" or elem.tag == f"{{{NS['p']}}}video":
            media_ref = _parse_media_element(elem, slide_rels, base_dir)
            if media_ref:
                refs.append(media_ref)
    return refs


def _parse_media_element(
    elem: Element,
    slide_rels: Dict[str, Tuple[str, str]],
    base_dir: str,
) -> Optional[MediaReference]:
    """Parse a single <p:audio> or <p:video> element."""
    r_id = elem.get(f"{{{NS['r']}}}link")  # common attribute for media relationship
    if not r_id:
        # try r:id directly
        r_id = elem.get(f"{{{NS['r']}}}id")
    if not r_id:
        return None

    # Determine media type from tag
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    media_type = "audio" if tag == "audio" else "video"

    # Resolve target
    target = get_target_for_id(slide_rels, r_id)
    if not target:
        return None
    full_path = resolve_path(base_dir, target)

    # Try to guess mime type from extension
    mime = _guess_mime(target)

    # Optional attributes: start time, end time, loop
    start = _parse_time(elem.get("start"))
    end = _parse_time(elem.get("end"))
    loop = elem.get("loop") == "1"

    return MediaReference(
        relationship_id=r_id,
        media_type=media_type,
        mime_type=mime,
        start_time=start,
        end_time=end,
        loop=loop,
        _meta={"full_path": full_path},  # store resolved path for convenience
    )


def _guess_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "wma": "audio/x-ms-wma",
        "m4a": "audio/mp4",
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "wmv": "video/x-ms-wmv",
        "mov": "video/quicktime",
        "flv": "video/x-flv",
        "mkv": "video/x-matroska",
    }
    return mime_map.get(ext, "application/octet-stream")


def _parse_time(val: Optional[str]) -> Optional[float]:
    """Convert a time string like '1000' (ms) to float seconds."""
    if val is None:
        return None
    try:
        return float(val) / 1000.0
    except ValueError:
        return None