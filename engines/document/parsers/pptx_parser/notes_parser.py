# engines/document/parsers/pptx_parser/media_parser.py
"""
Extracts audio/video media references from a slide XML.
Also provides a function to load the binary file data for round‑trip.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Tuple
from xml.etree.ElementTree import Element
from zipfile import ZipFile

from engines.document.models.psdm_models import MediaReference
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
        r_id = elem.get(f"{{{NS['r']}}}id")
    if not r_id:
        return None

    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    media_type = "audio" if tag == "audio" else "video"

    target = get_target_for_id(slide_rels, r_id)
    if not target:
        return None
    full_path = resolve_path(base_dir, target)

    mime = _guess_mime(target)
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
        _meta={"full_path": full_path},
    )


def load_media_binaries(
    slide_media_refs: List[MediaReference],
    slide_elements: List,  # LogicalElement list
    zip_file: ZipFile,
) -> None:
    """
    Load the binary content of all media files associated with a slide
    and store it in MediaReference._meta["data"].

    Args:
        slide_media_refs: list of MediaReference from slide.media_references.
        slide_elements: slide's LogicalElement list (to check for embedded media).
        zip_file: open ZipFile of the PPTX.
    """
    def _load(ref: MediaReference):
        path = ref._meta.get("full_path")
        if path:
            try:
                ref._meta["data"] = zip_file.read(path)
            except KeyError:
                pass

    for ref in slide_media_refs:
        _load(ref)

    for elem in slide_elements:
        ref = elem._meta.get("media_reference")
        if isinstance(ref, MediaReference):
            _load(ref)


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
    if val is None:
        return None
    try:
        return float(val) / 1000.0
    except ValueError:
        return None