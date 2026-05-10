# engines/document/writers/pptx_writer/media_writer.py
"""
Handles media file relationships for a slide.
The actual binary data must be provided by the caller (e.g., from the original ZIP).
"""
from __future__ import annotations

from ...models.psdm_models import MediaReference
from ...models.psdm_models import Slide


def build_slide_media_rels(slide: Slide) -> dict[str, str]:
    """
    Return a dict mapping the original relationship ID → target path
    for every media file associated with the slide.
    """
    rels: dict[str, str] = {}

    # 1. Standalone media (slide.media_references)
    for ref in slide.media_references:
        if not ref.relationship_id:
            continue
        ext = _mime_to_ext(ref.mime_type)
        # Use the original relationship id as the file name, e.g. "rId2.mp4"
        target = f"../media/{ref.relationship_id}.{ext}"
        rels[ref.relationship_id] = target

    # 2. Media attached to shapes (stored in element._meta["media_reference"])
    for elem in slide.elements:
        elem_ref = elem._meta.get("media_reference")
        if isinstance(elem_ref, MediaReference) and elem_ref.relationship_id:
            ext = _mime_to_ext(elem_ref.mime_type)
            target = f"../media/{elem_ref.relationship_id}.{ext}"
            rels[elem_ref.relationship_id] = target

    return rels


def collect_media_files(slides: list[Slide]) -> dict[str, bytes]:
    """
    Walk all slides and collect media binary data.
    It is assumed that the parser loaded the media binaries and stored them
    in MediaReference._meta["data"] (for round‑trip). If not present, the
    caller must supply the files separately.
    """
    media_files: dict[str, bytes] = {}
    for slide in slides:
        for ref in slide.media_references:
            data = ref._meta.get("data")
            if data:
                ext = _mime_to_ext(ref.mime_type)
                filename = f"media/{ref.relationship_id}.{ext}"
                media_files[filename] = data

        for elem in slide.elements:
            elem_ref = elem._meta.get("media_reference")
            if isinstance(elem_ref, MediaReference):
                data = elem_ref._meta.get("data")
                if data:
                    ext = _mime_to_ext(elem_ref.mime_type)
                    filename = f"media/{elem_ref.relationship_id}.{ext}"
                    media_files[filename] = data

    return media_files


def _mime_to_ext(mime: str) -> str:
    mapping = {
        "audio/mpeg": "mp3",
        "audio/wav":  "wav",
        "audio/mp4":  "m4a",
        "video/mp4":  "mp4",
        "video/quicktime": "mov",
        "video/x-ms-wmv":  "wmv",
    }
    return mapping.get(mime, "bin")
