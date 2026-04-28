# engines/document/parsers/spreadsheet_parser/xlsx/utils.py
from __future__ import annotations
import re
from typing import Tuple, Optional, List
from xml.etree import ElementTree as ET

# ── Column / coordinate conversion (unchanged) ──
def col_letter_to_index(letter: str) -> int:
    index = 0
    for char in letter.upper():
        index = index * 26 + (ord(char) - ord('A') + 1)
    return index

def col_index_to_letter(index: int) -> str:
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(65 + remainder) + result
    return result

def parse_cell_coordinate(coord: str) -> Tuple[int, int]:
    match = re.match(r"^([A-Z]+)(\d+)$", coord.upper())
    if not match:
        raise ValueError(f"Invalid cell coordinate: {coord}")
    col = col_letter_to_index(match.group(1))
    row = int(match.group(2))
    return row, col

def format_cell_coordinate(row: int, col: int) -> str:
    return f"{col_index_to_letter(col)}{row}"

def parse_range(range_str: str) -> Tuple[int, int, int, int]:
    if ':' not in range_str:
        r, c = parse_cell_coordinate(range_str)
        return r, c, r, c
    start, end = range_str.split(':')
    r1, c1 = parse_cell_coordinate(start)
    r2, c2 = parse_cell_coordinate(end)
    return (min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2))

def format_range(min_row, min_col, max_row, max_col):
    start = format_cell_coordinate(min_row, min_col)
    if min_row == max_row and min_col == max_col:
        return start
    end = format_cell_coordinate(max_row, max_col)
    return f"{start}:{end}"

# ── XML Helpers ──
def xml_find(el: ET.Element, tag: str, ns: dict, default=None):
    """Find first child element with tag, returning default if not found."""
    found = el.find(tag, ns)
    return found if found is not None else default

def xml_findall(el: ET.Element, tag: str, ns: dict) -> List[ET.Element]:
    return el.findall(tag, ns)

def xml_attr(el: ET.Element, attr: str, default=None):
    """Get attribute, return default if missing."""
    return el.get(attr, default)

def xml_text(el: ET.Element, default: str = "") -> str:
    """Return element text, default to empty string."""
    return el.text if el.text is not None else default

def xml_bool(el: ET.Element, attr: str, default: bool = False) -> bool:
    """Read boolean attribute (1, true, True)."""
    val = xml_attr(el, attr, None)
    if val is None:
        return default
    return val.lower() in ("1", "true")

def xml_int(el: ET.Element, attr: str, default: int = 0) -> int:
    val = xml_attr(el, attr, None)
    if val is None:
        return default
    try:
        return int(val)
    except ValueError:
        return default

def xml_float(el: ET.Element, attr: str, default: float = 0.0) -> float:
    val = xml_attr(el, attr, None)
    if val is None:
        return default
    try:
        return float(val)
    except ValueError:
        return default

def color_hex_from_xml(color_el: ET.Element, ns: dict) -> Optional[str]:
    """Convert a <color ...> element to hex/css colour string."""
    if color_el is None:
        return None
    rgb = xml_attr(color_el, "rgb")
    if rgb:
        return f"#{rgb}" if len(rgb) <= 6 else f"#{rgb[2:]}"
    theme = xml_attr(color_el, "theme")
    if theme is not None:
        return f"theme:{theme}"
    indexed = xml_attr(color_el, "indexed")
    if indexed is not None:
        return f"indexed:{indexed}"
    auto = xml_attr(color_el, "auto")
    if auto:
        return "auto"
    return None