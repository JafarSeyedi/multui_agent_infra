# engines/document/writers/spreadsheet_writer/xlsx/xlsx.py
"""
XLSX/XLSM writer – modular implementation.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
from typing import cast

from ....models.base import BaseDocument
from ....models.esdm_models import ESDMDocument
from ....models.esdm_models import Workbook
from ..base import ESDMBaseWriter
from ..base import ESDMWriteOptions
from .conditional_formatting_writer import ConditionalFormattingWriter
from .data_validation_writer import DataValidationWriter
from .extra_writers import CommentWriter
from .extra_writers import ContentTypesWriter
from .extra_writers import HyperlinkWriter
from .extra_writers import RelationshipsWriter
from .pivot_writer import PivotWriter
from .shared_strings_writer import SharedStringsWriter
from .styles_writer import StylesWriter
from .table_writer import TableWriter
from .vba_writer import VBAWriter
from .workbook_writer import WorkbookWriter
from .worksheet_writer import WorksheetWriter
from .zip_packager import ZipPackager


class XLSXWriter(ESDMBaseWriter):
    """
    Modular XLSX/XLSM writer.
    Delegates each part of the Excel package to a dedicated sub‑writer.
    """

    def __init__(self, options: ESDMWriteOptions | None = None):
        super().__init__(options)

        self._workbook_writer = WorkbookWriter(self)
        self._worksheet_writer = WorksheetWriter(self)
        self._styles_writer = StylesWriter(self)
        self._shared_strings_writer = SharedStringsWriter(self)
        self._table_writer = TableWriter(self)
        self._cf_writer = ConditionalFormattingWriter(self)
        self._dv_writer = DataValidationWriter(self)
        self._hyperlink_writer = HyperlinkWriter(self)
        self._comment_writer = CommentWriter(self)
        self._pivot_writer = PivotWriter(self)
        self._vba_writer = VBAWriter(self)
        self._rels_writer = RelationshipsWriter(self)
        self._content_types_writer = ContentTypesWriter(self)
        self._zip_packager = ZipPackager(self)

    # --------------------------------------------------------------
    # Public API – Liskov‑compliant: accept BaseDocument, cast to Workbook
    # --------------------------------------------------------------
    async def write_stream(self, document: BaseDocument) -> AsyncIterator[bytes]:
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        data = await self._build_xlsx(workbook)
        chunk_size = 64 * 1024
        for i in range(0, len(data), chunk_size):
            yield data[i:i+chunk_size]

    async def write(self, document: BaseDocument) -> bytes:
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        return await self._build_xlsx(workbook)

    async def write_to_file(
        self,
        document: BaseDocument,
        target: Path,
        options: dict[str, Any] | None = None
    ) -> None:
        doc = cast(ESDMDocument, document)
        workbook = doc.workbook
        if workbook is None:
            raise ValueError("Document has no workbook data")
        data = await self._build_xlsx(workbook)
        target.write_bytes(data)

    # --------------------------------------------------------------
    # Internal builder
    # --------------------------------------------------------------
    async def _build_xlsx(self, workbook: Workbook) -> bytes:
        # Reset all caches (defined in base)
        self._shared_strings = []
        self._shared_strings_index = {}
        self._fonts = []
        self._fills = []
        self._borders = []
        self._numfmts = []
        self._cell_formats = []
        self._style_cache = {}
        self._font_cache = {}
        self._fill_cache = {}
        self._border_cache = {}
        self._numfmt_cache = {}

        parts: dict[str, str | bytes] = {}

        # Core parts
        parts['xl/workbook.xml'] = self._workbook_writer.write(workbook)
        parts['xl/styles.xml'] = self._styles_writer.write()
        parts['xl/sharedStrings.xml'] = self._shared_strings_writer.write()

        # Worksheets & relationships
        sheet_rels = {}
        for idx, sheet in enumerate(workbook.sheets, start=1):
            sheet_xml, sheet_rel = self._worksheet_writer.write(sheet, idx, workbook)
            parts[f'xl/worksheets/sheet{idx}.xml'] = sheet_xml
            if sheet_rel:
                sheet_rels[idx] = sheet_rel

        for idx, rel in sheet_rels.items():
            parts[f'xl/worksheets/_rels/sheet{idx}.xml.rels'] = self._rels_writer.write_worksheet_rels(rel)

        # Tables
        table_index = 1
        for sheet_idx, sheet in enumerate(workbook.sheets, start=1):
            for table in sheet.tables:
                table_xml, table_rel = self._table_writer.write(table, table_index)
                parts[f'xl/tables/table{table_index}.xml'] = table_xml
                sheet_rels.setdefault(sheet_idx, []).append(table_rel)
                table_index += 1

        # Pivot tables
        if workbook.pivot_caches or workbook.pivot_tables:
            pc_xml, pt_xmls, rels = self._pivot_writer.write(workbook)
            if pc_xml:
                parts['xl/pivotCache/pivotCacheDefinition1.xml'] = pc_xml
            for pt_path, pt_content in pt_xmls.items():
                parts[pt_path] = pt_content
            # (rels would be merged into sheet_rels – omitted for brevity)

        # VBA project (XLSM)
        if getattr(workbook, 'vba_project', None) and self._esdm_options.write_macros and workbook.vba_project:
            parts['xl/vbaProject.bin'] = workbook.vba_project

        # Core properties
        parts['docProps/core.xml'] = self._write_core_properties_xml(workbook)

        # Build ZIP

        return await self._zip_packager.pack(workbook, parts, self._content_types_writer, self._rels_writer)

    # --------------------------------------------------------------
    # Abstract methods from ESDMBaseWriter (unused in modular writer)
    # --------------------------------------------------------------
    def _write_workbook_xml(self, workbook: Workbook) -> str:
        raise NotImplementedError("Use modular writer instead")

    def _write_worksheet_xml(self, worksheet, sheet_id: int) -> str:
        raise NotImplementedError("Use modular writer instead")

    def _write_styles_xml(self) -> str:
        raise NotImplementedError("Use modular writer instead")

    # --------------------------------------------------------------
    # Core properties helper
    # --------------------------------------------------------------
    def _write_core_properties_xml(self, workbook: Workbook) -> str:
        root = ET.Element('cp:coreProperties', {
            'xmlns:cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties',
            'xmlns:dc': 'http://purl.org/dc/elements/1.1/',
            'xmlns:dcterms': 'http://purl.org/dc/terms/',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        })
        md = workbook.metadata
        if md.title:
            ET.SubElement(root, 'dc:title').text = md.title
        if md.authors:
            ET.SubElement(root, 'dc:creator').text = ', '.join(md.authors)
        if md.creation_date:
            ET.SubElement(root, 'dcterms:created', {'xsi:type': 'dcterms:W3CDTF'}).text = md.creation_date.isoformat()
        if md.modification_date:
            ET.SubElement(root, 'dcterms:modified', {'xsi:type': 'dcterms:W3CDTF'}).text = md.modification_date.isoformat()
        return ET.tostring(root, encoding='unicode', xml_declaration=True)

    # --------------------------------------------------------------
    # Supported media types and extensions
    # --------------------------------------------------------------
    def get_supported_media_types(self) -> list[str]:
        return [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel.sheet.macroEnabled.12"
        ]

    def get_supported_extensions(self) -> list[str]:
        return [".xlsx", ".xlsm"]
