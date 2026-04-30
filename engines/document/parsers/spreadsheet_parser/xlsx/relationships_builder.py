# engines/document/parsers/spreadsheet_parser/xlsx/relationships_builder.py
"""
Parses OPC .rels files and Excel special relationships:
- RelationshipCollection
- External links
- Hyperlinks
- Defined names (from workbook.xml)
"""

from xml.etree.ElementTree import Element
from typing import List, Dict, Optional
from .namespaces import MAIN, REL
from .utils import (
    xml_find, xml_findall, xml_attr, xml_text, xml_bool, xml_int,
)
from ....models.esdm_models import (
    Relationship, RelationshipCollection,
    ExternalLink, ExternalReference,
    DefinedName, Hyperlink,
)

REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_REL = {"": REL_NS}

def build_relationships_from_rel_xml(rels_root: Element) -> RelationshipCollection:
    """Parse a .rels XML file (e.g., _rels/.rels, xl/_rels/workbook.xml.rels)."""
    coll = RelationshipCollection()
    for rel in xml_findall(rels_root, "Relationship", NS_REL):
        coll.add(Relationship(
            id=xml_attr(rel, "Id", ""),
            type=xml_attr(rel, "Type", ""),
            target=xml_attr(rel, "Target", ""),
            mode="External" if xml_attr(rel, "TargetMode") == "External" else "Internal",
        ))
    return coll

def build_external_links_from_rels(rels: RelationshipCollection) -> List[ExternalLink]:
    """Extract external links from relationships where type contains 'externalLink'."""
    links: Dict[int, ExternalLink] = {}
    for rel in rels.relationships:
        if "externalLink" in rel.type.lower():
            # Extract numeric ID from rId string like "rId10"
            try:
                link_id = int(rel.id.replace("rId", ""))
            except ValueError:
                link_id = hash(rel.id) % 10000
            links[link_id] = ExternalLink(
                id=link_id,
                file_path=rel.target,
                references=[],
            )
    return list(links.values())

def build_external_link_references(ext_link_xml: Element) -> List[ExternalReference]:
    """Parse an external link XML part (xl/externalLinks/externalLink*.xml) to get references."""
    refs = []
    ns = {"": MAIN}
    for ole_item in xml_findall(ext_link_xml, "oleItems/oleItem", ns):
        # only relevant if DDE/OLE linked
        pass
    # Standard external book references
    for ext_book in xml_findall(ext_link_xml, "externalBook", ns):
        sheet_names = xml_find(ext_book, "sheetNames", ns)
        if sheet_names is not None:
            for sn in xml_findall(sheet_names, "sheetName", ns):
                val = xml_attr(sn, "val")
                refs.append(ExternalReference(workbook_name="", sheet_name=val, ref=""))
        # external defined names
        for dname in xml_findall(ext_book, "definedNames/definedName", ns):
            name = xml_attr(dname, "name", "")
            ref = xml_text(dname)
            sheet = xml_attr(dname, "sheet", "")
            refs.append(ExternalReference(workbook_name="", sheet_name=sheet, ref=ref))
    return refs

def build_defined_names(workbook_xml: Element) -> List[DefinedName]:
    """Parse <definedNames> from workbook.xml."""
    names = []
    # The container is <definedNames>
    dn_elem = xml_find(workbook_xml, "definedNames", {"": MAIN})
    if dn_elem is None:
        return names
    for dn in xml_findall(dn_elem, "definedName", {"": MAIN}):
        names.append(DefinedName(
            name=xml_attr(dn, "name", ""),
            formula=xml_text(dn),
            local_sheet_id=xml_int(dn, "localSheetId", None) or None,
            comment=xml_attr(dn, "comment"),
            hidden=xml_bool(dn, "hidden"),
            function=xml_bool(dn, "function"),
            vb_procedure=xml_bool(dn, "vbProcedure"),
        ))
    return names

def build_hyperlinks(worksheet_xml: Element) -> List[Hyperlink]:
    """Extract <hyperlinks> from a worksheet XML."""
    links = []
    ns = {"": MAIN, "r": REL}
    hl_elem = xml_find(worksheet_xml, "hyperlinks", ns)
    if hl_elem is None:
        return links
    for hl in xml_findall(hl_elem, "hyperlink", ns):
        links.append(Hyperlink(
            ref=xml_attr(hl, "ref", ""),
            target=xml_attr(hl, "r:id", ""),  # actually relationship id, will be resolved later
            tooltip=xml_attr(hl, "tooltip"),
            display=xml_attr(hl, "display"),
        ))
    return links