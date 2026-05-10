# engines/document/parsers/pptx_parser/media_parser.py
"""
Extracts audio/video media references from a slide XML.
Also provides a function to load the binary file data for round‑trip.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element
from zipfile import ZipFile

from ...models.psdm_models import MediaReference, NotesSlide
from ...models.usdm_models import RichTextContent

from .constants import NAMESPACES
from .relationship_utils import get_target_for_id
from .relationship_utils import resolve_path

NS = NAMESPACES


def parse_notes_slide(notes_xml: Element) -> NotesSlide | None:
    # Placeholder – return an empty NotesSlide or None
    return NotesSlide(text=RichTextContent(spans=[]))

def _parse_media_element(
    elem: Element,
    slide_rels: dict[str, tuple[str, str]],
    base_dir: str,
) -> MediaReference | None:
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


def _parse_time(val: str | None) -> float | None:
    if val is None:
        return None
    try:
        return float(val) / 1000.0
    except ValueError:
        return None
