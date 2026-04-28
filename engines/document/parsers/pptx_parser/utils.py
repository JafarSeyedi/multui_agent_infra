# engines/document/parsers/pptx_parser/utils.py
"""
PPTX parser utility functions – used throughout the parsing process.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from xml.etree.ElementTree import Element


def element_to_dict(elem: Element) -> Dict[str, Any]:
    """
    Convert an XML Element to a nested dictionary that captures
    the tag name, attributes, text, and children – without any XML.
    Usable for round‑trip metadata storage.

    The resulting dict has:
        - "_tag": the local tag name
        - attrib items directly
        - "_text": text content (if present)
        - "_children": list of child dicts (preserving order)
    """
    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
    d: Dict[str, Any] = {"_tag": tag}
    # Attributes
    for key, val in elem.attrib.items():
        # keep full attribute name including namespace if any
        d[key] = val
    # Text
    if elem.text and elem.text.strip():
        d["_text"] = elem.text.strip()
    # Children
    children = []
    for child in elem:
        children.append(element_to_dict(child))
    if children:
        d["_children"] = children
    return d


def dict_to_element(d: Dict[str, Any], namespaces: Dict[str, str]) -> Element:
    """
    Reconstruct an XML Element from a dictionary produced by element_to_dict.
    This is used in the writer for round‑trip.
    """
    tag = d["_tag"]
    # resolve namespace prefix if tag contains one
    ns_prefix = ""
    local_tag = tag
    if ":" in tag:
        ns_prefix, local_tag = tag.split(":", 1)
        ns_uri = namespaces.get(ns_prefix, "")
        full_tag = f"{{{ns_uri}}}{local_tag}" if ns_uri else tag
    else:
        full_tag = tag  # assume no namespace needed (unusual)
    attrib = {k: v for k, v in d.items() if not k.startswith("_")}
    elem = Element(full_tag, attrib)
    if "_text" in d:
        elem.text = d["_text"]
    for child in d.get("_children", []):
        elem.append(dict_to_element(child, namespaces))
    return elem