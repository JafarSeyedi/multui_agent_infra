"""XML parser helpers used by model loader integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class XmlParseError(ValueError):
    """Raised when XML parsing fails."""


def parse_xml(payload: str | bytes) -> ET.Element:
    """Parse XML and return the root element."""
    try:
        return ET.fromstring(payload)
    except (ET.ParseError, TypeError) as exc:
        raise XmlParseError(f"Invalid XML: {exc}") from exc


def xml_to_dict(element: ET.Element) -> dict[str, Any]:
    """Convert an XML element to a nested dict."""
    result: dict[str, Any] = {
        "tag": element.tag,
        "text": (element.text or "").strip() if element.text else "",
        "attrib": dict(element.attrib),
        "children": [xml_to_dict(child) for child in list(element)],
    }
    return result
