# engines/document/parsers/pptx_parser/ole_parser.py
"""
Extracts OLE objects from a slide XML.
"""
from __future__ import annotations

from xml.etree.ElementTree import Element

from ....models.base import ElementType
from ....models.usdm_models import OLEObjectContent
from .constants import NAMESPACES

NS = NAMESPACES

def parse_ole_objects(slide_xml: Element) -> list[OLEObjectContent]:
    ole_list = []
    for ole_elem in slide_xml.findall(".//p:oleObj", NS):
        prog_id = ole_elem.get("progId")
        r_id = ole_elem.get(f"{{{NS['r']}}}id")
        display_icon = ole_elem.get("showAsIcon") == "1"
        # The binary data is not stored directly; we just capture the reference.
        ole = OLEObjectContent(
            prog_id=prog_id,
            relationship_id=r_id,
            display_as_icon=display_icon,
        )
        ole_list.append(ole)
    return ole_list

def load_ole_binaries(slide_elements, slide_rels, zip_file, base_dir):
    """
    Resolve OLE relationships and load binary data into OLEObjectContent._meta["data"].
    """
    from .relationship_utils import get_target_for_id, resolve_path
    for elem in slide_elements:
        if elem.element_type == ElementType.OLE_OBJECT:
            ole = elem.content
            r_id = ole.relationship_id
            if r_id and r_id in slide_rels:
                target = get_target_for_id(slide_rels, r_id)
                if target:
                    path = resolve_path(base_dir, target)
                    try:
                        ole._meta["data"] = zip_file.read(path)
                    except KeyError:
                        pass
