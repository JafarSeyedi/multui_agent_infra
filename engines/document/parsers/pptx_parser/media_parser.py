# engines/document/parsers/pptx_parser/media_parser.py
"""
Extracts audio/video media references from a slide XML.
Produces MediaReference objects and loads binary data.
"""
from __future__ import annotations

from zipfile import ZipFile
from xml.etree.ElementTree import Element

from ...models.psdm_models import MediaReference
from .constants import NAMESPACES
from .relationship_utils import get_target_for_id
from .relationship_utils import resolve_path

NS = NAMESPACES


def parse_media_references(
    slide_xml: Element,
    slide_rels: dict[str, tuple[str, str]],
    base_dir: str,
) -> list[MediaReference]:
    """
    Scan the entire slide XML for <p:audio> and <p:video> elements and
    return a list of MediaReference objects with resolved paths.
    """
    refs: list[MediaReference] = []
    for elem in slide_xml.iter():
        if elem.tag == f"{{{NS['p']}}}audio" or elem.tag == f"{{{NS['p']}}}video":
            media_ref = _parse_media_element(elem, slide_rels, base_dir)
            if media_ref:
                refs.append(media_ref)
    return refs


def load_media_binaries(
    media_references: list[MediaReference],
    elements: list,  # LogicalElement list, unused but kept for API compatibility
    zip_file: ZipFile,
) -> None:
    """
    Load binary data for media references. This is a placeholder; actual
    extraction would read the referenced file from the ZIP and store it
    in the MediaReference's binary payload or attach to the element.
    Currently we only ensure the path is resolved; no binary loading.
    """
    for ref in media_references:
        # The full path is stored in _meta during parsing
        if "_meta" in ref.__dict__ and "full_path" in ref._meta:
            path = ref._meta["full_path"]
            try:
                data = zip_file.read(path)
                # Optionally store bytes in ref._meta["binary"] or create BinaryContent
                ref._meta["binary"] = data
            except KeyError:
                pass  # file missing, ignore


def _parse_media_element(
    elem: Element,
    slide_rels: dict[str, tuple[str, str]],
    base_dir: str,
) -> MediaReference | None:
    r_id = elem.get(f"{{{NS['r']}}}link") or elem.get(f"{{{NS['r']}}}id")
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