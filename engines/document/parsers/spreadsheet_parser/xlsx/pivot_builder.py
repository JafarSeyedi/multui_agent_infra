# engines/document/parsers/spreadsheet_parser/xlsx/pivot_builder.py
"""
Complete XML → ESDM for pivot tables and caches.
"""

from xml.etree.ElementTree import Element
from typing import List, Optional
from .namespaces import MAIN, REL
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_int, xml_bool,
    parse_range, col_letter_to_index,
)
from ....models.esdm_models import (
    PivotCache, PivotCacheReference,
    PivotTable, PivotField,
)

NS = {"": MAIN, "r": REL}

def build_pivot_cache_from_xml(cache_elem: Element) -> PivotCache:
    """Parse <pivotCacheDefinition> XML."""
    cache_id = xml_int(cache_elem, "id")
    # Source
    src_elem = xml_find(cache_elem, "cacheSource", NS)
    source = PivotCacheReference(sheet="", ref="")
    if src_elem is not None:
        ws_src = xml_find(src_elem, "worksheetSource", NS)
        if ws_src is not None:
            source.sheet = xml_attr(ws_src, "sheet", "")
            source.ref = xml_attr(ws_src, "ref", "")
    # Cache fields (optional – we could parse for field names)
    return PivotCache(id=cache_id, source=source)

def build_pivot_table_from_xml(pivot_elem: Element) -> PivotTable:
    """Parse <pivotTableDefinition> XML."""
    name = xml_attr(pivot_elem, "name", "PivotTable")
    cache_id = xml_int(pivot_elem, "cacheId")
    # location is a reference like "Sheet1!A3"
    location = xml_attr(pivot_elem, "location", "")
    # Pivot fields
    fields: List[PivotField] = []
    # In OOXML, pivotFields can be under <pivotFields>
    pf_container = xml_find(pivot_elem, "pivotFields", NS)
    if pf_container is not None:
        for pf in xml_findall(pf_container, "pivotField", NS):
            name_attr = xml_attr(pf, "name", "")
            orientation = xml_attr(pf, "orientation", "").lower()
            subtotal = xml_attr(pf, "subtotalTop", None)  # can be none
            # If no explicit orientation, it might be implicit (cache field)
            fields.append(PivotField(
                name=name_attr,
                orientation=orientation if orientation else "row",
                subtotal=subtotal,
            ))
    return PivotTable(
        name=name,
        location=location,
        cache_id=cache_id,
        fields=fields,
    )

def parse_cache_fields_for_names(cache_elem: Element) -> Dict[int, str]:
    """Return a dict of cache field index → name."""
    names = {}
    cache_fields_elem = xml_find(cache_elem, "cacheFields", NS)
    if cache_fields_elem is not None:
        for idx, cf in enumerate(xml_findall(cache_fields_elem, "cacheField", NS)):
            name = xml_attr(cf, "name", "")
            names[idx] = name
    return names