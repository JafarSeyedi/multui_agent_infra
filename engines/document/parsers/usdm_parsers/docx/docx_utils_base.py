"""Shared constants and dataclasses for DOCX utilities."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

OOXML_NAMESPACES = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
    'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml',
    'w15': 'http://schemas.microsoft.com/office/word/2012/wordml',
    'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
    'dgm': 'http://schemas.openxmlformats.org/drawingml/2006/diagram',
}

NS = OOXML_NAMESPACES

for prefix, uri in OOXML_NAMESPACES.items():
    ET.register_namespace(prefix, uri)


@dataclass
class DocxStyleInfo:
    """DOCX style information"""
    style_id: str
    style_type: str
    style_name: str | None = None
    based_on: str | None = None
    next_style: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocxNumberingInfo:
    """DOCX numbering information"""
    num_id: str
    abstract_num_id: str
    level: int
    format: str
    text: str | None = None
    start: int = 1
    properties: dict[str, Any] = field(default_factory=dict)


def parse_dxa_to_points(value: str | int | float | None) -> float | None:
    """
    Convert DXA (twentieths of a point) to points.
    
    Args:
        value: DXA value as string, int, or float
        
    Returns:
        Value in points or None
    """
    if value is None:
        return None

    try:
        dxa = float(value) if isinstance(value, str) else float(value)
        return dxa / 20.0
    except (ValueError, TypeError):
        return None


def parse_emu_to_pixels(value: str | int | float | None, dpi: int = 96) -> float | None:
    """
    Convert EMU (English Metric Units) to pixels.
    
    Args:
        value: EMU value as string, int, or float
        dpi: Dots per inch (default 96)
        
    Returns:
        Value in pixels or None
    """
    if value is None:
        return None

    try:
        emu = float(value) if isinstance(value, str) else float(value)
        inches = emu / 914400.0
        return inches * dpi
    except (ValueError, TypeError):
        return None
