# engines/document/writers/pptx_writer/utils.py
"""
Generic helpers for the PPTX writer.
"""
from __future__ import annotations

from typing import Any
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement

def dict_to_element(parent: Element, data: dict[str, Any], namespaces: dict[str, str]) -> None:
    """
    Reconstruct XML children from a structured dict (as produced by parser's element_to_dict).
    This is used for extLst and other opaque round‑trip data.
    """
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            child = SubElement(parent, key)
            dict_to_element(child, value, namespaces)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    child = SubElement(parent, key)
                    dict_to_element(child, item, namespaces)
                else:
                    child = SubElement(parent, key)
                    child.text = str(item)
        else:
            parent.set(key, str(value))
