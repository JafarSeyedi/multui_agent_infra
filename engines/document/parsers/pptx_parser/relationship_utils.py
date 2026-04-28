# engines/document/parsers/pptx_parser/relationship_utils.py
"""
Utility functions for resolving relationships inside a PPTX package.
Supports package-level, slide-level, and drawing-level rels.
"""

from __future__ import annotations
from typing import Dict, Optional, List, Tuple
from xml.etree.ElementTree import Element
from zipfile import ZipFile

# Relationships namespace
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NSMAP = {"rel": REL_NS}


def load_rels(zip_file: ZipFile, rels_path: str) -> Dict[str, Tuple[str, str]]:
    """
    Load a .rels file and return a dict mapping relationship ID → (type, target).

    Args:
        zip_file: The open PPTX ZIP archive.
        rels_path: Path inside the ZIP, e.g., "ppt/_rels/presentation.xml.rels".

    Returns:
        Dictionary: rId → (relationship_type, target).
    """
    rels: Dict[str, Tuple[str, str]] = {}
    try:
        xml_bytes = zip_file.read(rels_path)
        root = Element.fromstring(xml_bytes)
        for rel_elem in root.findall("rel:Relationship", NSMAP):
            r_id = rel_elem.get("Id")
            r_type = rel_elem.get("Type", "")
            target = rel_elem.get("Target", "")
            if r_id:
                rels[r_id] = (r_type, target)
    except (KeyError, Exception):
        pass
    return rels


def get_target_for_id(
    rels: Dict[str, Tuple[str, str]],
    r_id: str,
) -> Optional[str]:
    """Return the target path for a given relationship ID."""
    entry = rels.get(r_id)
    return entry[1] if entry else None


def get_targets_by_type(
    rels: Dict[str, Tuple[str, str]],
    rel_type: str,
) -> List[str]:
    """Return all targets of a specific relationship type."""
    targets = []
    for r_id, (typ, target) in rels.items():
        if typ.endswith(rel_type):
            targets.append(target)
    return targets


def resolve_slide_rels(
    zip_file: ZipFile,
    slide_path: str,
) -> Dict[str, Tuple[str, str]]:
    """
    Load relationships for a specific slide part.

    Args:
        zip_file: The open PPTX ZIP.
        slide_path: Path inside ZIP, e.g., "ppt/slides/slide1.xml".

    Returns:
        Relationship dict for that slide.
    """
    # Convert slide_path to its rels equivalent
    parts = slide_path.rsplit("/", 1)
    if len(parts) == 2:
        folder, filename = parts
        rels_path = f"{folder}/_rels/{filename}.rels"
    else:
        rels_path = f"_rels/{slide_path}.rels"
    return load_rels(zip_file, rels_path)


def resolve_path(base_dir: str, target: str) -> str:
    """
    Resolve a relative target against a base directory inside the ZIP.

    Example:
        base_dir = "ppt/slides", target = "../media/image1.png"
        → "ppt/media/image1.png"
    """
    if not target.startswith(".."):
        return f"{base_dir}/{target}" if base_dir else target
    base_parts = base_dir.split("/")
    for part in target.split("/"):
        if part == "..":
            if base_parts:
                base_parts.pop()
        else:
            base_parts.append(part)
    return "/".join(base_parts)


def resolve_image_path(
    slide_rels: Dict[str, Tuple[str, str]],
    r_id: str,
    base_dir: str,
) -> Optional[str]:
    """
    Resolve an image relationship ID to a full path inside the ZIP.

    Args:
        slide_rels: Slide's .rels dict (rId → (type, target)).
        r_id: Relationship ID (e.g., "rId2").
        base_dir: Base directory for the slide (e.g., "ppt/slides").

    Returns:
        Full path to the image file, or None if not found.
    """
    entry = slide_rels.get(r_id)
    if entry and entry[0].endswith("/image"):
        return resolve_path(base_dir, entry[1])
    return None