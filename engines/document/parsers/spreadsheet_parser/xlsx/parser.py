# engines/document/parsers/spreadsheet_parser/xlsx/parser.py
"""
XLSXParser – complete Excel parser using direct ZIP + XML.

Refined: sheet‑level relationships are now loaded so that comments,
threaded comments, and tables are correctly attached to each worksheet.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from xml.etree import ElementTree as ET

from engines.document.parsers.spreadsheet_parser.base_spreadsheet_parser import BaseSpreadsheetParser
from engines.document.parsers.base import ParseOptions
from ....models.esdm_models import (
    ESDMDocument,
    Workbook,
    RelationshipCollection,
    Relationship,
)
from .workbook_builder import build_workbook
from .relationships_builder import build_relationships_from_rel_xml
from .utils import xml_find, xml_findall, xml_attr
from .namespaces import MAIN, REL
from .charts_builder import parse_chart

# Relationship types (namespace‑qualified)
NS_OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_COMMENTS = f"{NS_OFFICE}/comments"
REL_TABLE   = f"{NS_OFFICE}/table"
REL_THREADED_COMMENT = "http://schemas.microsoft.com/office/2017/10/relationships/threadedComment"
REL_PIVOT_CACHE = f"{NS_OFFICE}/pivotCacheDefinition"
REL_PIVOT_TABLE = f"{NS_OFFICE}/pivotTable"
REL_EXTERNAL_LINK = f"{NS_OFFICE}/externalLink"
REL_DRAWING = f"{NS_OFFICE}/drawing"
REL_CHART = f"{NS_OFFICE}/chart"
REL_IMAGE = f"{NS_OFFICE}/image"

class XLSXParser(BaseSpreadsheetParser):
    """Complete Excel parser – uses the ZIP package directly."""

    name = "xlsx"
    supported_extensions = (".xlsx", ".xlsm", ".xltx", ".xltm")

    async def _parse_to_workbook(
        self, data: bytes, source_name: str, options: ParseOptions
    ) -> Workbook:
        zip_data = io.BytesIO(data)
        with zipfile.ZipFile(zip_data, "r") as zf:
            # 1. Workbook relationships
            wb_rels = self._load_relationships(zf, "xl/_rels/workbook.xml.rels")

            # 2. Workbook XML
            wb_xml = self._load_xml(zf, "xl/workbook.xml")

            # 3. Shared strings
            ss_xml = self._load_xml(zf, "xl/sharedStrings.xml", optional=True)

            # 4. Styles
            styles_xml = self._load_xml(zf, "xl/styles.xml", optional=True)
            if styles_xml is None:
                # Provide minimal fallback
                styles_xml = ET.fromstring(
                    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"/>'
                )

            # 5. Resolve sheets and load their XML + associated parts
            sheet_info = self._resolve_sheets(wb_xml, wb_rels)
            sheet_xmls: Dict[str, ET.Element] = {}
            comments_xmls: Dict[str, ET.Element] = {}
            threaded_comments_xmls: Dict[str, ET.Element] = {}
            table_xmls: Dict[str, List[ET.Element]] = {}
            drawing_xmls: Dict[str, ET.Element] = {}
            image_map: Dict[str, str] = {}
            chart_map: Dict[str, ET.Element] = {}

            for sheet_name, (sheet_path, sheet_id) in sheet_info.items():
                # Load the sheet itself
                sheet_xml = self._load_xml(zf, sheet_path)
                if sheet_xml is not None:
                    sheet_xmls[sheet_name] = sheet_xml

                # Load sheet‑level relationships
                sheet_rels = self._load_sheet_relationships(zf, sheet_path)

                # Comments (legacy)
                comments_target = self._find_sheet_relationship(sheet_rels, REL_COMMENTS)
                if comments_target:
                    comments_path = self._resolve_relative_path(sheet_path, comments_target)
                    comments_xml = self._load_xml(zf, comments_path, optional=True)
                    if comments_xml is not None:
                        comments_xmls[sheet_name] = comments_xml

                # Threaded comments
                tc_target = self._find_sheet_relationship(sheet_rels, REL_THREADED_COMMENT)
                if tc_target:
                    tc_path = self._resolve_relative_path(sheet_path, tc_target)
                    tc_xml = self._load_xml(zf, tc_path, optional=True)
                    if tc_xml is not None:
                        threaded_comments_xmls[sheet_name] = tc_xml

                # Tables (potentially multiple)
                table_targets = self._find_sheet_relationship_multiple(sheet_rels, REL_TABLE)
                if table_targets:
                    tbl_list = []
                    for tgt in table_targets:
                        tbl_path = self._resolve_relative_path(sheet_path, tgt)
                        tbl_xml = self._load_xml(zf, tbl_path, optional=True)
                        if tbl_xml is not None:
                            tbl_list.append(tbl_xml)
                    if tbl_list:
                        table_xmls[sheet_name] = tbl_list

                # Look for drawing relationship for this sheet
                drawing_rel_target = self._find_sheet_relationship(sheet_rels, REL_DRAWING)
                if drawing_rel_target:
                    drawing_path = self._resolve_relative_path(sheet_path, drawing_rel_target)
                    drawing_xml = self._load_xml(zf, drawing_path, optional=True)
                    if drawing_xml is not None:
                        # Load drawing's own relationships (for images and charts)
                        drawing_rels = self._load_sheet_relationships(zf, drawing_path)
                        for rel in drawing_rels.relationships:
                            if rel.type == REL_IMAGE:
                                full_img_path = self._resolve_relative_path(drawing_path, rel.target)
                                image_map[rel.id] = full_img_path
                            elif rel.type == REL_CHART:
                                chart_path = self._resolve_relative_path(drawing_path, rel.target)
                                chart_xml = self._load_xml(zf, chart_path, optional=True)
                                if chart_xml is not None:
                                    full_chart = parse_chart(chart_xml)   # from charts_builder
                                    chart_map[rel.id] = full_chart                
                    drawing_xmls[sheet_name] = drawing_xml

            # 6. External links (workbook-level relationships)
            external_link_xmls = {}
            for rel in wb_rels.relationships:
                if rel.type == REL_EXTERNAL_LINK:
                    link_id = self._relationship_id_to_int(rel.id)
                    ext_path = f"xl/{rel.target}"
                    ext_xml = self._load_xml(zf, ext_path, optional=True)
                    if ext_xml is not None:
                        external_link_xmls[link_id] = ext_xml

            # 7. Pivot caches / tables
            pivot_cache_xmls = []
            for rel in wb_rels.relationships:
                if rel.type == REL_PIVOT_CACHE:
                    pc_path = f"xl/{rel.target}"
                    pc_xml = self._load_xml(zf, pc_path, optional=True)
                    if pc_xml is not None:
                        pivot_cache_xmls.append(pc_xml)

            pivot_table_xmls = []
            for rel in wb_rels.relationships:
                if rel.type == REL_PIVOT_TABLE:
                    pt_path = f"xl/{rel.target}"
                    pt_xml = self._load_xml(zf, pt_path, optional=True)
                    if pt_xml is not None:
                        pivot_table_xmls.append(pt_xml)

            # 8. Calculation chain
            calc_chain_xml = self._load_xml(zf, "xl/calcChain.xml", optional=True)

            # 9. VBA project
            vba_bin = None
            if "xl/vbaProject.bin" in set(zf.namelist()):
                vba_bin = zf.read("xl/vbaProject.bin")

            # 10. Build the workbook
            workbook = build_workbook(
                workbook_xml=wb_xml,
                shared_strings_xml=ss_xml,
                styles_xml=styles_xml,
                workbook_rels=wb_rels,
                sheet_xmls=sheet_xmls,
                comments_xmls=comments_xmls,
                threaded_comments_xmls=threaded_comments_xmls,
                table_xmls=table_xmls,
                calc_chain_xml=calc_chain_xml,
                pivot_cache_xmls=pivot_cache_xmls,
                pivot_table_xmls=pivot_table_xmls,
                external_links_xmls=external_link_xmls,
                vba_bin=vba_bin,
                drawing_xmls=drawing_xmls,
                image_map = image_map,
                chart_map=chart_map,
            )

            # Apply sheet filter option
            if options.sheet_names:
                workbook.sheets = [s for s in workbook.sheets if s.name in options.sheet_names]

            return workbook

    # ── XML loading helpers ────────────────────────────────────

    @staticmethod
    def _load_xml(zf: zipfile.ZipFile, path: str, optional: bool = False) -> Optional[ET.Element]:
        try:
            with zf.open(path) as f:
                return ET.parse(f).getroot()
        except KeyError:
            if optional:
                return None
            raise FileNotFoundError(f"Required part missing: {path}")

    @staticmethod
    def _load_relationships(zf: zipfile.ZipFile, rels_path: str) -> RelationshipCollection:
        try:
            root = XLSXParser._load_xml(zf, rels_path)
            return build_relationships_from_rel_xml(root)
        except FileNotFoundError:
            return RelationshipCollection()

    @staticmethod
    def _load_sheet_relationships(zf: zipfile.ZipFile, sheet_path: str) -> RelationshipCollection:
        """
        Derive the sheet's .rels path from sheet_path and load it.
        e.g., xl/worksheets/sheet1.xml → xl/worksheets/_rels/sheet1.xml.rels
        """
        path_obj = Path(sheet_path)
        rels_name = path_obj.name + ".rels"
        rels_path = str(path_obj.parent / "_rels" / rels_name)
        return XLSXParser._load_relationships(zf, rels_path)

    # ── Sheet resolution ───────────────────────────────────────

    def _resolve_sheets(self, wb_xml: ET.Element, wb_rels: RelationshipCollection) -> Dict[str, Tuple[str, int]]:
        """
        Returns a dict: sheet_name → (full_zip_path, sheet_id)
        """
        sheets = {}
        ns = {"": MAIN, "r": REL}
        sheets_elem = xml_find(wb_xml, "sheets", ns)
        if sheets_elem is None:
            return sheets
        for sheet_el in xml_findall(sheets_elem, "sheet", ns):
            name = xml_attr(sheet_el, "name", "")
            r_id = xml_attr(sheet_el, "r:id", "")
            s_id = int(xml_attr(sheet_el, "sheetId", "0"))
            # resolve target from workbook rels
            target = None
            for rel in wb_rels.relationships:
                if rel.id == r_id:
                    target = rel.target
                    break
            if target:
                path = f"xl/{target}"
                sheets[name] = (path, s_id)
        return sheets

    # ── Relationship lookups ────────────────────────────────────

    def _find_sheet_relationship(
        self, rels: RelationshipCollection, rel_type: str
    ) -> Optional[str]:
        """Return the first target for the given relationship type in `rels`."""
        for rel in rels.relationships:
            if rel.type == rel_type:
                return rel.target
        return None

    def _find_sheet_relationship_multiple(
        self, rels: RelationshipCollection, rel_type: str
    ) -> List[str]:
        """Return all targets for the given relationship type in `rels`."""
        return [rel.target for rel in rels.relationships if rel.type == rel_type]

    # ── Path helpers ────────────────────────────────────────────

    @staticmethod
    def _resolve_relative_path(base_path: str, target: str) -> str:
        base_dir = Path(base_path).parent
        return (base_dir / target).as_posix()

    @staticmethod
    def _relationship_id_to_int(r_id: str) -> int:
        """Extract numeric id from rId string, e.g., rId8 → 8."""
        try:
            return int(r_id.lower().replace("rid", ""))
        except ValueError:
            return hash(r_id) % 10000

    # ── Public parse method (overriding base) ────────────────────
    async def parse_bytes(
        self,
        data: bytes,
        document_id: str,
        source_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        options: Optional[ParseOptions] = None,
    ) -> ESDMDocument:
        options = options or ParseOptions()
        workbook = await self._parse_to_workbook(data, source_name, options)
        from engines.document.models.media_detection import detect_media_type
        media_type = detect_media_type(path=source_name, data=data)
        return ESDMDocument(
            title=source_name or document_id,
            document_id=document_id,
            media_type=media_type,
            file_extension=Path(source_name).suffix if source_name else "",
            metadata=metadata or {},
            workbook=workbook,
        )